"""Evaluate the fine-tuned adapter on the held-out split.

The split in out/train/ is GROUPED by base project, so test.jsonl / val.jsonl
contain projects the model never trained on. Scoring well here means the model
LEARNED the task; scoring well only on train means it MEMORIZED. This script
measures the former.

For every ChatML row we feed system+user to the model, parse the JSON it
returns, and score it mode-aware (the system prompt says which mode it is):

  A,B  full canonical record  -> synth.validate.validate_normalized (zero errors)
  C    {"components":[...]}    -> per-component required fields + controlled vocab
  D    {"relationships":[...]} -> source/target must be component ids FROM THE INPUT
  E    {"instructions":[...]}  -> phase vocab, component_ids in input, dep ordering
  F    validation block        -> required keys/types, confidence in [0,1]

Headline metrics: JSON-parse rate and task-valid rate, per mode and overall.

Run (in the unsloth env):
    python eval_local.py                       # test split, all rows
    python eval_local.py --split val
    python eval_local.py --limit 20            # quick smoke
    python eval_local.py --dump out/eval_fails.jsonl
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import warnings
from collections import defaultdict
from pathlib import Path

# Force UTF-8 stdout/stderr so the ✓/✗ progress marks can't crash a Windows
# cp1252 console or a piped/teed run (same guard as run.py / generate_detail.py).
for _stream in ("stdout", "stderr"):
    _s = getattr(sys, _stream)
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

# Silence two benign-but-noisy per-row warnings that flood the log:
#  - "Both max_new_tokens and max_length seem to have been set" (we always pass
#    max_new_tokens; the model's generation_config carries a max_length default)
#  - transformers' deprecated AttentionMaskConverter FutureWarning (fires twice
#    per eval pass inside the library; nothing we can act on here)
warnings.filterwarnings("ignore", message=".*max_new_tokens.*max_length.*")
warnings.filterwarnings("ignore", category=FutureWarning,
                        module="transformers.modeling_attn_mask_utils")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from synth.validate import (  # noqa: E402  (after sys.path tweak)
    validate_normalized,
    COMPONENT_TYPES, COMPONENT_CATEGORIES, RELATION_TYPES, INSTRUCTION_PHASES,
    _SNAKE_RE,
)
from synth.repair import repair_record  # noqa: E402

# Eval context can exceed the 4096 training window — the base model supports
# 32k and LoRA doesn't cap it. Mode F inputs (a full record) run 5–6k tokens,
# so a 4096 window truncates the prompt and the model can't answer.
MAX_SEQ = 8192
ADAPTER = ROOT / "out" / "lora" / "adapter"
TRAIN_DIR = ROOT / "out" / "train"

# --- JSON extraction -------------------------------------------------------
_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str):
    """Best-effort: pull the first JSON object out of a model response.

    Handles ```json fences and leading/trailing prose. Returns the parsed
    object, or raises json.JSONDecodeError if nothing parses.
    """
    t = text.strip()
    m = _FENCE.search(t)
    if m:
        t = m.group(1).strip()
    # Fast path: the whole thing is JSON.
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    # Fallback: take from the first '{' to the last '}' and try that.
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        return json.loads(t[start:end + 1])
    raise json.JSONDecodeError("no JSON object found", t, 0)


# --- mode detection --------------------------------------------------------
_MODE_RE = re.compile(r"Mode\s+([A-F])\b")


def detect_mode(system_prompt: str) -> str:
    m = _MODE_RE.search(system_prompt)
    return m.group(1) if m else "?"


# --- per-mode scorers ------------------------------------------------------
# Each returns a list of error strings; empty list == task-valid.

def _score_components(items: list) -> list[str]:
    errs = []
    req = {"component_id", "display_name", "category", "type", "material",
           "quantity", "description", "dimensions", "functional_role"}
    for i, c in enumerate(items):
        if not isinstance(c, dict):
            errs.append(f"component[{i}] not an object")
            continue
        missing = req - set(c)
        if missing:
            errs.append(f"component[{i}] missing {sorted(missing)}")
        cid = c.get("component_id", "")
        if not isinstance(cid, str) or not _SNAKE_RE.match(cid):
            errs.append(f"component[{i}] id {cid!r} not snake_case")
        if c.get("type") not in COMPONENT_TYPES:
            errs.append(f"component {cid!r}: bad type {c.get('type')!r}")
        if c.get("category") not in COMPONENT_CATEGORIES:
            errs.append(f"component {cid!r}: bad category {c.get('category')!r}")
    return errs


def score_c(obj, user) -> list[str]:
    if not isinstance(obj, dict) or not isinstance(obj.get("components"), list):
        return ["missing top-level 'components' list"]
    if not obj["components"]:
        return ["components list is empty"]
    return _score_components(obj["components"])


def _input_component_ids(user: str) -> set[str]:
    """Pull component ids out of a mode D/E user turn (JSON embedded in prose)."""
    try:
        obj = extract_json(user)
    except json.JSONDecodeError:
        return set()
    comps = obj.get("components", []) if isinstance(obj, dict) else []
    return {c.get("component_id") for c in comps if isinstance(c, dict)}


def score_d(obj, user) -> list[str]:
    if not isinstance(obj, dict) or not isinstance(obj.get("relationships"), list):
        return ["missing top-level 'relationships' list"]
    ids = _input_component_ids(user)
    errs = []
    for i, r in enumerate(obj["relationships"]):
        if not isinstance(r, dict):
            errs.append(f"relationship[{i}] not an object")
            continue
        for end in ("source", "target"):
            v = r.get(end)
            if ids and v not in ids:
                errs.append(f"relationship[{i}].{end} {v!r} not an input component")
        if r.get("relation") not in RELATION_TYPES:
            errs.append(f"relationship[{i}] bad relation {r.get('relation')!r}")
    return errs


def score_e(obj, user) -> list[str]:
    if not isinstance(obj, dict) or not isinstance(obj.get("instructions"), list):
        return ["missing top-level 'instructions' list"]
    ids = _input_component_ids(user)
    errs = []
    seen_steps: set[str] = set()
    for i, s in enumerate(obj["instructions"]):
        if not isinstance(s, dict):
            errs.append(f"step[{i}] not an object")
            continue
        if s.get("phase") not in INSTRUCTION_PHASES:
            errs.append(f"step[{i}] bad phase {s.get('phase')!r}")
        for cid in s.get("component_ids", []):
            if ids and cid not in ids:
                errs.append(f"step[{i}] references unknown component {cid!r}")
        for dep in s.get("dependencies", []):
            if dep not in seen_steps:
                errs.append(f"step[{i}] depends on later/missing step {dep!r}")
        seen_steps.add(s.get("step_id"))
    return errs


def score_f(obj, user) -> list[str]:
    if not isinstance(obj, dict):
        return ["validation block not an object"]
    req = {"schema_valid", "reference_integrity_valid", "manufacturability_valid",
           "naming_consistency_valid", "issues", "confidence_score"}
    errs = [f"missing {k}" for k in req - set(obj)]
    for k in ("schema_valid", "reference_integrity_valid",
              "manufacturability_valid", "naming_consistency_valid"):
        if k in obj and not isinstance(obj[k], bool):
            errs.append(f"{k} not boolean")
    if "issues" in obj and not isinstance(obj["issues"], list):
        errs.append("issues not a list")
    cs = obj.get("confidence_score")
    if not isinstance(cs, (int, float)) or not (0.0 <= cs <= 1.0):
        errs.append(f"confidence_score {cs!r} not in [0,1]")
    return errs


def score_ab(obj, user) -> list[str]:
    if not isinstance(obj, dict):
        return ["output is not a JSON object"]
    return [i["message"] for i in validate_normalized(obj, strict=True)
            if i["severity"] == "error"]


SCORERS = {"A": score_ab, "B": score_ab, "C": score_c,
           "D": score_d, "E": score_e, "F": score_f}


# --- reference-based scoring (vs the gold answer) --------------------------
# We score each output against its gold target two ways:
#   exact_match  — canonicalized output == canonicalized gold (strict lower bound)
#   F1           — overlap of a mode-specific "key set" of structural items
# The key set turns a record into a bag of comparable atoms (components,
# relationship triples, step ids, validation flags). F1 = harmonic mean of the
# precision/recall of those atoms. This is standard slot/edge-F1 for structured
# output; it tolerates reordering and extra prose that exact-match would punish.

def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def _components_keys(items) -> set:
    out = set()
    for c in items or []:
        if isinstance(c, dict):
            out.add(("c", c.get("component_id")))
    return out


def _relationship_keys(items) -> set:
    out = set()
    for r in items or []:
        if isinstance(r, dict):
            out.add(("r", r.get("source"), r.get("relation"), r.get("target")))
    return out


def _instruction_keys(items) -> set:
    out = set()
    for s in items or []:
        if isinstance(s, dict):
            out.add(("s", s.get("step_id")))
            for cid in s.get("component_ids", []):
                out.add(("sc", s.get("step_id"), cid))
    return out


def _validation_keys(obj) -> set:
    out = set()
    if not isinstance(obj, dict):
        return out
    for k in ("schema_valid", "reference_integrity_valid",
              "manufacturability_valid", "naming_consistency_valid"):
        out.add(("v", k, obj.get(k)))
    for i in obj.get("issues", []) or []:
        if isinstance(i, dict):
            out.add(("vi", i.get("code")))
    return out


def keyset(mode: str, obj) -> set:
    """The bag of structural atoms used for F1, per mode."""
    if not isinstance(obj, dict):
        return set()
    if mode in ("A", "B"):
        return (_components_keys(obj.get("components"))
                | _relationship_keys(obj.get("relationships"))
                | _instruction_keys(obj.get("instructions")))
    if mode == "C":
        return _components_keys(obj.get("components"))
    if mode == "D":
        return _relationship_keys(obj.get("relationships"))
    if mode == "E":
        return _instruction_keys(obj.get("instructions"))
    if mode == "F":
        return _validation_keys(obj)
    return set()


def prf(pred: set, gold: set) -> tuple[int, int, int]:
    """Return (true_positives, false_positives, false_negatives)."""
    tp = len(pred & gold)
    return tp, len(pred) - tp, len(gold) - tp


def f1_from_counts(tp: int, fp: int, fn: int) -> float:
    if tp == 0:
        return 0.0
    p = tp / (tp + fp)
    r = tp / (tp + fn)
    return 2 * p * r / (p + r)


# --- main ------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", choices=["test", "val"], default="test")
    ap.add_argument("--adapter", type=Path, default=ADAPTER)
    ap.add_argument("--max-seq", type=int, default=MAX_SEQ,
                    help="eval context window; rows whose prompt exceeds it are "
                         "SKIPPED (not truncated) and reported separately")
    ap.add_argument("--max-new-tokens", type=int, default=4096,
                    help="CEILING on generated tokens; the real per-row budget is "
                         "sized to the gold answer (+50%%) so short modes finish fast")
    ap.add_argument("--per-mode", type=int, default=0,
                    help="evaluate at most N rows per mode (seeded stratified "
                         "sample); 0 = all rows")
    ap.add_argument("--tf-modes", type=str, default="AB",
                    help="modes scored TEACHER-FORCED (one forward pass, no slow "
                         "autoregression) instead of by generation. These modes "
                         "have huge outputs (A/B ~9k tok); default 'AB'. Empty to "
                         "generate everything.")
    ap.add_argument("--tf-chunk", type=int, default=512,
                    help="teacher-forcing cross-entropy chunk size (bounds the "
                         "fp32 logit upcast)")
    ap.add_argument("--tf-max-seq", type=int, default=12288,
                    help="max prompt+gold length for teacher-forcing; longer rows "
                         "are skipped (one full forward materializes [seq x vocab] "
                         "logits, so keep this ~12k on a 12 GB card)")
    ap.add_argument("--gen-sample", type=int, default=0,
                    help="for teacher-forced modes, ALSO free-generate this many "
                         "rows/mode as a JSON-validity spot check (slow; needs a "
                         "high --max-new-tokens to complete A/B)")
    ap.add_argument("--limit", type=int, default=0, help="0 = all rows")
    ap.add_argument("--dump", type=Path, default=None,
                    help="write failing cases to this JSONL for inspection")
    args = ap.parse_args()

    rows_path = TRAIN_DIR / f"{args.split}.jsonl"
    if not rows_path.exists():
        print(f"No {rows_path} — run 'python prepare_training.py' first.")
        return 1
    # Fail early with a clear message if the default adapter isn't trained yet.
    # (A non-default --adapter may be a HF hub id, so only check the default.)
    if str(args.adapter) == str(ADAPTER) and not ADAPTER.exists():
        print(f"No adapter at {ADAPTER} — run 'python train_local.py' first, "
              f"or pass --adapter <path-or-hub-id>.")
        return 1
    with rows_path.open(encoding="utf-8") as f:
        rows = [json.loads(l) for l in f]
    if args.per_mode:
        # Stratified, seeded sample: at most N rows per mode. A held-out estimate
        # doesn't need all rows, and this keeps every mode represented.
        import random
        buckets: dict[str, list] = defaultdict(list)
        for r in rows:
            sysmsg = next((m["content"] for m in r.get("messages", [])
                           if m.get("role") == "system"), "")
            buckets[detect_mode(sysmsg)].append(r)
        rng = random.Random(0)
        picked: list = []
        for mode in sorted(buckets):
            rs = buckets[mode][:]
            rng.shuffle(rs)
            picked.extend(rs[: args.per_mode])
        rows = picked
    if args.limit:
        rows = rows[:args.limit]
    if not rows:
        print("No rows to evaluate — check the split file / --per-mode / --limit.")
        return 1

    tf_modes = set(args.tf_modes.upper().strip())
    gen_modes = sorted(set("ABCDEF") - tf_modes)
    print(f"Evaluating {len(rows)} rows from {rows_path.name}")
    print(f"  teacher-forced: {' '.join(sorted(tf_modes)) or '(none)'}"
          f"   generated: {' '.join(gen_modes) or '(none)'}\n")

    # The model must be loaded with a window that covers BOTH paths: generation
    # rows are bounded by --max-seq, but teacher-forcing runs one forward over
    # prompt+gold up to --tf-max-seq. Loading with the smaller value makes
    # Unsloth truncate longer TF inputs (silently corrupting the scores).
    model_ctx = max(args.max_seq, args.tf_max_seq if tf_modes else 0)

    # Import torch/unsloth lazily so --help works without a GPU env.
    import torch
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(args.adapter), max_seq_length=model_ctx, load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    # Qwen's generation_config ships max_length=32768. We always pass
    # max_new_tokens (which takes precedence), but transformers logs a noisy
    # "Both max_new_tokens and max_length seem to be set" line on EVERY generate
    # call while both are non-default. Reset to the library default (20) so the
    # warning never fires; it has no effect since max_new_tokens always wins.
    model.generation_config.max_length = 20

    import math
    import torch.nn.functional as F

    # stats[mode] = dict of running counters
    def _new() -> dict:
        return {"n": 0, "parse": 0, "valid": 0, "rparse": 0, "rvalid": 0,
                "em": 0, "tp": 0, "fp": 0, "fn": 0, "skipped_long": 0}
    stats: dict[str, dict] = defaultdict(_new)

    def _tf_new() -> dict:
        return {"n": 0, "tok_correct": 0, "tok_total": 0, "loss_sum": 0.0,
                "gen_n": 0, "gen_parse": 0, "gen_valid": 0, "skipped_long": 0}
    tf_stats: dict[str, dict] = defaultdict(_tf_new)
    fails = []

    def _tf_score(system: str, user: str, gold_text: str):
        """Teacher-forced next-token accuracy + loss on the gold answer.

        ONE full forward over prompt+gold with NO KV cache — Unsloth's cached
        decode path only accepts a single token at a time (`assert q_len == 1`),
        so we can't feed multi-token chunks with past_key_values. The full
        forward handles q_len>1 fine; we then compute the cross-entropy/argmax
        over the assistant slice in CHUNKS so the fp32 upcast never covers the
        whole [gold x vocab] block. Returns (correct, total, loss_sum), or None
        if prompt+gold exceeds --tf-max-seq.
        """
        prompt_ids = tokenizer.apply_chat_template(
            [{"role": "system", "content": system},
             {"role": "user", "content": user}],
            add_generation_prompt=True, return_tensors="pt").to("cuda")
        full_ids = tokenizer.apply_chat_template(
            [{"role": "system", "content": system},
             {"role": "user", "content": user},
             {"role": "assistant", "content": gold_text}],
            add_generation_prompt=False, return_tensors="pt").to("cuda")
        P, T = prompt_ids.shape[1], full_ids.shape[1]
        if T > args.tf_max_seq:
            return None
        # BPE can merge tokens across the prompt/gold boundary, so full_ids is
        # not guaranteed to start with prompt_ids verbatim. Verify, and on a
        # mismatch score from the first diverging position — otherwise every
        # "gold" label would be off by one and tok_acc/ppl silently wrong.
        L = min(P, T)
        eq = full_ids[0, :L] == prompt_ids[0, :L]
        if not bool(eq.all()):
            P = int((~eq).nonzero()[0].item())
        if P < 1:
            return 0, 0, 0.0
        G = T - P
        if G <= 0:
            return 0, 0, 0.0
        correct = total = 0
        loss_sum = 0.0
        with torch.no_grad():
            out = model(input_ids=full_ids, use_cache=False)
            logits = out.logits[0]                 # [T, V]
            tgt = full_ids[0, P:]                  # [G]  the gold tokens
            pred = logits[P - 1:T - 1]             # [G, V]  predictions for them
            for s in range(0, G, args.tf_chunk):
                pl = pred[s:s + args.tf_chunk].float()
                lb = tgt[s:s + args.tf_chunk]
                loss_sum += F.cross_entropy(pl, lb, reduction="sum").item()
                correct += int((pl.argmax(-1) == lb).sum().item())
                total += int(lb.numel())
                del pl
            del logits, out
        return correct, total, loss_sum

    def _generate(system: str, user: str, budget: int) -> str:
        inp = tokenizer.apply_chat_template(
            [{"role": "system", "content": system},
             {"role": "user", "content": user}],
            add_generation_prompt=True, return_tensors="pt", return_dict=True,
        ).to("cuda")
        with torch.no_grad():
            o = model.generate(**inp, max_new_tokens=budget, do_sample=False,
                               pad_token_id=tokenizer.eos_token_id)
        return tokenizer.decode(o[0][inp["input_ids"].shape[1]:],
                                skip_special_tokens=True)

    for idx, row in enumerate(rows):
        msgs = row.get("messages", [])
        system = next((m["content"] for m in msgs if m.get("role") == "system"), "")
        user = next((m["content"] for m in msgs if m.get("role") == "user"), "")
        if not msgs or not user:
            print(f"[{idx:>3}] ?  ~ skipped (malformed row: missing messages/user)")
            continue
        gold_text = msgs[-1]["content"]
        try:
            gold = extract_json(gold_text)
        except json.JSONDecodeError:
            gold = None
        mode = detect_mode(system)
        gold_keys = keyset(mode, gold) if gold is not None else set()

        # Teacher-forced path for long-output modes: score the gold in one pass
        # instead of generating thousands of tokens per row.
        if mode in tf_modes:
            ts = tf_stats[mode]
            r = _tf_score(system, user, gold_text)
            if r is None:
                ts["skipped_long"] += 1
                print(f"[{idx:>3}] {mode}  ~ skipped (seq > {args.tf_max_seq})")
                continue
            correct, total, loss_sum = r
            ts["n"] += 1
            ts["tok_correct"] += correct
            ts["tok_total"] += total
            ts["loss_sum"] += loss_sum
            acc = 100 * correct / total if total else 0.0
            print(f"[{idx:>3}] {mode}  · tok-acc {acc:.0f}% ({total} tok)")
            # Optional slow spot-check: free-generate a few rows to test validity.
            if ts["gen_n"] < args.gen_sample:
                ts["gen_n"] += 1
                gtext = _generate(system, user, args.max_new_tokens)
                try:
                    gobj = extract_json(gtext)
                    ts["gen_parse"] += 1
                    if not SCORERS[mode](gobj, user):
                        ts["gen_valid"] += 1
                except json.JSONDecodeError:
                    pass
            continue

        inputs = tokenizer.apply_chat_template(
            [{"role": "system", "content": system},
             {"role": "user", "content": user}],
            add_generation_prompt=True, return_tensors="pt", return_dict=True,
        ).to("cuda")

        st = stats[mode]
        # Skip prompts that don't fit the window instead of silently truncating
        # them: a chopped prompt guarantees broken output AND wastes prefill time.
        input_len = inputs["input_ids"].shape[1]
        remaining = args.max_seq - input_len
        if remaining <= 0:
            st["skipped_long"] += 1
            print(f"[{idx:>3}] {mode}  ~ skipped (input {input_len} >= {args.max_seq})")
            continue
        # Likewise skip rows whose gold answer cannot fit in what's left of the
        # window — generating there guarantees a truncated/garbage output that
        # would be scored as a model failure when it's a window artifact.
        if gold is not None:
            gold_tok = len(tokenizer(gold_text).input_ids)
            if gold_tok + 8 > remaining:
                st["skipped_long"] += 1
                print(f"[{idx:>3}] {mode}  ~ skipped (answer ~{gold_tok} tok > "
                      f"{remaining} left in window)")
                continue

        # Size the generation budget to the gold answer (+50% margin), capped by
        # --max-new-tokens AND by the remaining window. Short-output modes
        # (F ~44 tok) stop early instead of grinding to 4096 — the main speedup.
        if gold is not None:
            gen_budget = min(args.max_new_tokens, int(gold_tok * 1.5) + 64, remaining)
        else:
            gen_budget = min(args.max_new_tokens, remaining)

        with torch.no_grad():
            out = model.generate(
                **inputs, max_new_tokens=gen_budget,
                do_sample=False, pad_token_id=tokenizer.eos_token_id,
            )
        text = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:],
                                skip_special_tokens=True)

        st["n"] += 1
        # What a consumer gets BEHIND the deterministic repair gate
        # (synth/repair.py): syntax salvage + snake_case id rewrite. Scored
        # alongside the raw output so both realities stay visible.
        robj, _rnotes = repair_record(text)
        if robj is not None:
            st["rparse"] += 1
            if not SCORERS.get(mode, lambda o, u: ["unknown mode"])(robj, user):
                st["rvalid"] += 1
        try:
            obj = extract_json(text)
        except json.JSONDecodeError as e:
            st["fn"] += len(gold_keys)  # produced nothing matchable
            fails.append({"mode": mode, "reason": f"json: {e}",
                          "user": user[:200], "output_tail": text[-300:]})
            print(f"[{idx:>3}] {mode}  ✗ invalid JSON")
            continue
        st["parse"] += 1

        # reference-based: exact match + F1 atom counts (vs the gold answer)
        if gold is not None:
            if _canon(obj) == _canon(gold):
                st["em"] += 1
            tp, fp, fn = prf(keyset(mode, obj), gold_keys)
            st["tp"] += tp
            st["fp"] += fp
            st["fn"] += fn

        errs = SCORERS.get(mode, lambda o, u: ["unknown mode"])(obj, user)
        if errs:
            fails.append({"mode": mode, "reason": errs[:5], "user": user[:200]})
            print(f"[{idx:>3}] {mode}  ✗ {len(errs)} issue(s): {errs[0]}")
        else:
            st["valid"] += 1
            print(f"[{idx:>3}] {mode}  ✓")

    # --- report ---
    print("\n=== Results by mode ===")
    hdr = (f"{'mode':<6}{'n':>5}{'skip':>6}{'parse%':>8}{'valid%':>8}"
           f"{'rprs%':>8}{'rvld%':>8}{'EM%':>7}{'F1':>7}")
    print(hdr)
    agg = _new()

    def _row(label: str, s: dict) -> str:
        n = s["n"]
        if n == 0:  # every row for this mode was skipped (prompt too long)
            return (f"{label:<6}{n:>5}{s['skipped_long']:>6}"
                    f"{'--':>8}{'--':>8}{'--':>8}{'--':>8}{'--':>7}{'--':>7}")
        f1 = f1_from_counts(s["tp"], s["fp"], s["fn"])
        return (f"{label:<6}{n:>5}{s['skipped_long']:>6}"
                f"{100*s['parse']/n:>7.0f}%{100*s['valid']/n:>7.0f}%"
                f"{100*s['rparse']/n:>7.0f}%{100*s['rvalid']/n:>7.0f}%"
                f"{100*s['em']/n:>6.0f}%{f1:>7.2f}")

    for mode in sorted(stats):
        s = stats[mode]
        for k in agg:
            agg[k] += s[k]
        print(_row(mode, s))
    print(_row("ALL", agg))
    print("\nskip    = row doesn't fit the --max-seq window (prompt too long, or "
          "gold answer too big for what's left) — raise --max-seq to include")
    print("parse%  = produced valid JSON")
    print("valid%  = passed mode-specific schema/reference checks")
    print("rprs%   = parses AFTER the deterministic repair gate (synth/repair.py)")
    print("rvld%   = valid AFTER repair — what a consumer behind the gate gets")
    print("EM%     = output exactly equals the gold answer (strict)")
    print("F1      = micro-F1 of structural atoms vs gold "
          "(components / relationship triples / steps / validation flags)")

    if tf_stats:
        print("\n=== Teacher-forced modes (scored on the gold, no generation) ===")
        print(f"{'mode':<6}{'n':>5}{'skip':>6}{'tok_acc%':>10}{'ppl':>9}"
              f"{'gen':>5}{'gen_valid%':>12}")
        for mode in sorted(tf_stats):
            t = tf_stats[mode]
            tot = t["tok_total"]
            acc = 100 * t["tok_correct"] / tot if tot else 0.0
            ppl = math.exp(t["loss_sum"] / tot) if tot else float("nan")
            gv = f"{100*t['gen_valid']/t['gen_n']:.0f}%" if t["gen_n"] else "-"
            print(f"{mode:<6}{t['n']:>5}{t['skipped_long']:>6}{acc:>9.0f}%"
                  f"{ppl:>9.1f}{t['gen_n']:>5}{gv:>12}")
        print("\ntok_acc% = next-token accuracy on the gold answer (teacher-forced)")
        print("ppl      = perplexity of the gold answer (lower is better)")
        print("gen      = rows also free-generated for a JSON-validity spot check")

    if args.dump and fails:
        args.dump.parent.mkdir(parents=True, exist_ok=True)
        with args.dump.open("w", encoding="utf-8") as f:
            for fa in fails:
                f.write(json.dumps(fa, ensure_ascii=False) + "\n")
        print(f"\nWrote {len(fails)} failing cases -> {args.dump}")

    return 0 if agg["valid"] == agg["n"] else 1


if __name__ == "__main__":
    sys.exit(main())
