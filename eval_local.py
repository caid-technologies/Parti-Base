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
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from synth.validate import (  # noqa: E402  (after sys.path tweak)
    validate_normalized,
    COMPONENT_TYPES, COMPONENT_CATEGORIES, RELATION_TYPES, INSTRUCTION_PHASES,
    _SNAKE_RE,
)

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
                    help="eval context window (>train window is fine)")
    ap.add_argument("--max-new-tokens", type=int, default=4096)
    ap.add_argument("--limit", type=int, default=0, help="0 = all rows")
    ap.add_argument("--dump", type=Path, default=None,
                    help="write failing cases to this JSONL for inspection")
    args = ap.parse_args()

    rows_path = TRAIN_DIR / f"{args.split}.jsonl"
    if not rows_path.exists():
        print(f"No {rows_path} — run 'python prepare_training.py' first.")
        return 1
    rows = [json.loads(l) for l in rows_path.open(encoding="utf-8")]
    if args.limit:
        rows = rows[:args.limit]
    print(f"Evaluating {len(rows)} rows from {rows_path.name}\n")

    # Import torch/unsloth lazily so --help works without a GPU env.
    import torch
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(args.adapter), max_seq_length=args.max_seq, load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)

    # stats[mode] = dict of running counters
    def _new() -> dict:
        return {"n": 0, "parse": 0, "valid": 0, "em": 0,
                "tp": 0, "fp": 0, "fn": 0}
    stats: dict[str, dict] = defaultdict(_new)
    fails = []

    for idx, row in enumerate(rows):
        msgs = row["messages"]
        system = next(m["content"] for m in msgs if m["role"] == "system")
        user = next(m["content"] for m in msgs if m["role"] == "user")
        gold_text = msgs[-1]["content"]
        try:
            gold = extract_json(gold_text)
        except json.JSONDecodeError:
            gold = None
        mode = detect_mode(system)
        gold_keys = keyset(mode, gold) if gold is not None else set()

        inputs = tokenizer.apply_chat_template(
            [{"role": "system", "content": system},
             {"role": "user", "content": user}],
            add_generation_prompt=True, return_tensors="pt", return_dict=True,
        ).to("cuda")
        with torch.no_grad():
            out = model.generate(
                **inputs, max_new_tokens=args.max_new_tokens,
                do_sample=False, pad_token_id=tokenizer.eos_token_id,
            )
        text = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:],
                                skip_special_tokens=True)

        st = stats[mode]
        st["n"] += 1
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
    hdr = f"{'mode':<6}{'n':>5}{'parse%':>8}{'valid%':>8}{'EM%':>7}{'F1':>7}"
    print(hdr)
    agg = _new()
    for mode in sorted(stats):
        s = stats[mode]
        for k in agg:
            agg[k] += s[k]
        n = s["n"]
        f1 = f1_from_counts(s["tp"], s["fp"], s["fn"])
        print(f"{mode:<6}{n:>5}{100*s['parse']/n:>7.0f}%{100*s['valid']/n:>7.0f}%"
              f"{100*s['em']/n:>6.0f}%{f1:>7.2f}")
    n = agg["n"]
    f1 = f1_from_counts(agg["tp"], agg["fp"], agg["fn"])
    print(f"{'ALL':<6}{n:>5}{100*agg['parse']/n:>7.0f}%{100*agg['valid']/n:>7.0f}%"
          f"{100*agg['em']/n:>6.0f}%{f1:>7.2f}")
    print("\nparse%  = produced valid JSON")
    print("valid%  = passed mode-specific schema/reference checks")
    print("EM%     = output exactly equals the gold answer (strict)")
    print("F1      = micro-F1 of structural atoms vs gold "
          "(components / relationship triples / steps / validation flags)")

    if args.dump and fails:
        args.dump.parent.mkdir(parents=True, exist_ok=True)
        with args.dump.open("w", encoding="utf-8") as f:
            for fa in fails:
                f.write(json.dumps(fa, ensure_ascii=False) + "\n")
        print(f"\nWrote {len(fails)} failing cases -> {args.dump}")

    return 0 if agg["valid"] == agg["n"] else 1


if __name__ == "__main__":
    sys.exit(main())
