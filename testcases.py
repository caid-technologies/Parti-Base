"""Zero-shot test cases: base model (no fine-tuning) on the document→record task.

Measures how well an UNTRAINED base model (e.g. qwen3.5 via Ollama) handles
our core use case — turn a project document into the full canonical record —
across four input media derived from the 42 seed projects under Data/:

  txt    the project's original free-text prompt, written to files/<slug>.txt
  md     the project's GUIDE.md, used verbatim from Data/
  pdf    GUIDE.md rendered to files/<slug>.pdf at build time; at run time the
         text is re-extracted with pypdf (exercises the PDF ingestion path)
  image  the project's VISUAL.png, sent as an OpenAI-style vision content
         part (requires a vision-capable model tag, e.g. a -vl variant)

Gold = out/normalized/<slug>.json (Stage 1 output). Scoring reuses
eval_local.py: JSON-parse rate, strict-schema valid rate (score_ab), and
structural F1 vs the gold record (components / relationship triples / steps).
This is the no-training baseline the fine-tuned adapter must beat.

Two subcommands:
    python testcases.py build                    # deterministic, no LLM
    python testcases.py build --limit 3          # smoke: first 3 projects

    python testcases.py run --model qwen3.5      # zero-shot eval via Ollama
    python testcases.py run --types txt,md --per-type 5
    python testcases.py run --dump out/testcases/fails.jsonl --min-valid 20

`build` writes out/testcases/cases.jsonl (+ generated txt/pdf inputs under
out/testcases/files/). `run` reads that manifest, calls Ollama zero-shot
(temperature 0), prints a per-input-type table, and writes
out/testcases/report_<model>.json as the traceable result.
"""
from __future__ import annotations
import argparse
import base64
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

# Same UTF-8 guard as run.py / eval_local.py — ✓/✗ marks on a cp1252 console.
for _stream in ("stdout", "stderr"):
    _s = getattr(sys, _stream)
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from eval_local import (  # noqa: E402
    extract_json, keyset, prf, f1_from_counts, score_ab,
)
from synth.staged import MODE_SYSTEM_PROMPTS  # noqa: E402

DATA_DIR = ROOT / "Data"
GOLD_DIR = ROOT / "out" / "normalized"
CASES_DIR = ROOT / "out" / "testcases"
INPUT_TYPES = ("txt", "md", "pdf", "image")

# The task contract is identical to Mode B (request → full canonical record);
# only the input medium changes, and the user turn states which one it is.
SYSTEM_PROMPT = MODE_SYSTEM_PROMPTS["B"]

_DOC_LABEL = {
    "txt": "plain-text project request",
    "md": "markdown build guide",
    "pdf": "build guide (text extracted from a PDF)",
}


# --- document helpers -------------------------------------------------------

def latin1_safe(text: str) -> str:
    """fpdf2 core fonts are latin-1 only; replace anything outside it.

    Good enough for a test input — the guides are ASCII-heavy English and the
    scorer never compares the PDF text back to the source verbatim.
    """
    return text.encode("latin-1", "replace").decode("latin-1")


def _fit_lines(pdf, text: str):
    """Wrap text to the page width using the font's real metrics.

    We wrap OURSELVES instead of using fpdf2's multi_cell wrapping: WORD mode
    aborts on tokens wider than the line, and CHAR mode can spin forever
    (observed hang in fpdf2 2.8.7 line_break.get_width on our guides). Breaks
    at the last space that fits, mid-token when nothing else can.
    """
    maxw = pdf.epw
    for raw in latin1_safe(text).splitlines() or [""]:
        line = raw.replace("\t", "    ").rstrip()
        if not line:
            yield ""
            continue
        while pdf.get_string_width(line) > maxw:
            lo, hi = 1, len(line)  # longest prefix that fits, by bisection
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if pdf.get_string_width(line[:mid]) <= maxw:
                    lo = mid
                else:
                    hi = mid - 1
            cut = line.rfind(" ", 0, lo)
            if cut <= 0:
                cut = max(lo, 1)
            yield line[:cut]
            line = line[cut:].lstrip()
        yield line


def render_pdf(text: str, path: Path) -> None:
    """Render plain/markdown text into a simple single-column PDF."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in _fit_lines(pdf, text):
        pdf.cell(pdf.epw, 5, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))


def pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    return "\n".join((page.extract_text() or "")
                     for page in PdfReader(str(path)).pages)


def image_data_uri(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


# --- build ------------------------------------------------------------------

def project_slugs(data_dir: Path = DATA_DIR) -> list[str]:
    return sorted(p.name[: -len("_files")]
                  for p in data_dir.glob("*_files") if p.is_dir())


def build_cases(out_dir: Path = CASES_DIR, data_dir: Path = DATA_DIR,
                gold_dir: Path = GOLD_DIR, limit: int = 0) -> list[dict]:
    """Write the case manifest + generated txt/pdf inputs. Deterministic.

    Each case: {case_id, slug, input_type, input_path, gold_path}. Paths are
    stored relative to the repo ROOT (posix separators) so the manifest is
    portable; missing source files skip that one case, never the project.
    """
    files_dir = out_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    def rel(p: Path) -> str:
        p = p.resolve()
        try:
            return p.relative_to(ROOT).as_posix()
        except ValueError:  # out dir outside the repo (tests) — keep absolute
            return p.as_posix()

    cases: list[dict] = []
    slugs = project_slugs(data_dir)
    if limit:
        slugs = slugs[:limit]
    for slug in slugs:
        gold_path = gold_dir / f"{slug}.json"
        if not gold_path.exists():
            print(f"  ! {slug}: no gold at {gold_path} — skipped "
                  f"(run 'python run.py' to produce out/normalized/)")
            continue
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        folder = data_dir / f"{slug}_files"
        guide = folder / f"{slug}_GUIDE.md"
        png = folder / f"{slug}_VISUAL.png"

        def add(input_type: str, input_path: Path) -> None:
            cases.append({
                "case_id": f"{slug}__{input_type}",
                "slug": slug,
                "input_type": input_type,
                "input_path": rel(input_path),
                "gold_path": rel(gold_path),
            })

        prompt = (gold.get("project") or {}).get("original_prompt", "")
        if prompt:
            txt_path = files_dir / f"{slug}.txt"
            txt_path.write_text(prompt, encoding="utf-8")
            add("txt", txt_path)
        if guide.exists():
            add("md", guide)
            pdf_path = files_dir / f"{slug}.pdf"
            render_pdf(guide.read_text(encoding="utf-8"), pdf_path)
            add("pdf", pdf_path)
        if png.exists():
            add("image", png)

    manifest = out_dir / "cases.jsonl"
    with manifest.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return cases


def load_cases(out_dir: Path = CASES_DIR) -> list[dict]:
    manifest = out_dir / "cases.jsonl"
    if not manifest.exists():
        raise FileNotFoundError(
            f"No {manifest} — run 'python testcases.py build' first.")
    with manifest.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# --- run --------------------------------------------------------------------

def _resolve(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    return p if p.is_absolute() else ROOT / p


def user_content(case: dict):
    """Build the user-turn content for a case.

    Text media return a plain string; images return OpenAI-style content
    parts (text + image_url data URI), which Ollama's /v1 layer accepts for
    vision-capable models.
    """
    path = _resolve(case["input_path"])
    kind = case["input_type"]
    if kind == "image":
        text = ("Design the hobbyist hardware project shown in this image. "
                "Infer the components, relationships, fabrication, "
                "instructions, sourcing, and validation from what you see.")
        return [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": image_data_uri(path)}},
        ]
    doc = pdf_text(path) if kind == "pdf" else path.read_text(encoding="utf-8")
    return (f"Design the hobbyist hardware project described in this "
            f"{_DOC_LABEL[kind]}:\n\n{doc}")


def score_case(output_text: str, gold: dict) -> dict:
    """Parse + strict-validate + structural F1 vs gold. Pure, no LLM."""
    res = {"parsed": False, "valid": False, "errors": [],
           "tp": 0, "fp": 0, "fn": 0}
    gold_keys = keyset("B", gold)
    try:
        obj = extract_json(output_text)
    except json.JSONDecodeError as e:
        res["errors"] = [f"json: {e}"]
        res["fn"] = len(gold_keys)
        return res
    res["parsed"] = True
    errs = score_ab(obj, "")
    res["errors"] = errs
    res["valid"] = not errs
    res["tp"], res["fp"], res["fn"] = prf(keyset("B", obj), gold_keys)
    return res


def run_eval(args) -> int:
    cases = load_cases(args.cases_dir)
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    unknown = set(types) - set(INPUT_TYPES)
    if unknown:
        print(f"Unknown --types {sorted(unknown)}; pick from {INPUT_TYPES}")
        return 1
    cases = [c for c in cases if c["input_type"] in types]
    if args.per_type:
        seen: dict[str, int] = defaultdict(int)
        picked = []
        for c in cases:  # manifest is slug-sorted, so this is deterministic
            if seen[c["input_type"]] < args.per_type:
                seen[c["input_type"]] += 1
                picked.append(c)
        cases = picked
    if args.limit:
        cases = cases[:args.limit]
    if not cases:
        print("No cases match — check --types / --per-type / --limit.")
        return 1

    from synth.ollama_client import chat_text

    model = args.model
    print(f"Zero-shot eval: {len(cases)} cases, model={model}, "
          f"types={','.join(types)}\n")

    def _new() -> dict:
        return {"n": 0, "err": 0, "parse": 0, "valid": 0,
                "tp": 0, "fp": 0, "fn": 0, "secs": 0.0}
    stats: dict[str, dict] = defaultdict(_new)
    fails: list[dict] = []

    for idx, case in enumerate(cases):
        st = stats[case["input_type"]]
        st["n"] += 1
        gold = json.loads(_resolve(case["gold_path"]).read_text(encoding="utf-8"))
        t0 = time.time()
        try:
            text = chat_text(
                [{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": user_content(case)}],
                temperature=0.0, max_tokens=args.max_tokens, model=model,
            )
        except Exception as e:  # transport/model errors (e.g. no vision support)
            st["err"] += 1
            st["fn"] += len(keyset("B", gold))
            fails.append({"case_id": case["case_id"], "reason": f"call: {e}"})
            print(f"[{idx:>3}] {case['case_id']:<44} ✗ call failed: {e}")
            continue
        secs = time.time() - t0
        st["secs"] += secs

        r = score_case(text, gold)
        st["parse"] += r["parsed"]
        st["valid"] += r["valid"]
        for k in ("tp", "fp", "fn"):
            st[k] += r[k]
        f1 = f1_from_counts(r["tp"], r["fp"], r["fn"])
        if r["valid"]:
            print(f"[{idx:>3}] {case['case_id']:<44} ✓ F1 {f1:.2f} ({secs:.0f}s)")
        else:
            reason = r["errors"][0] if r["errors"] else "?"
            fails.append({"case_id": case["case_id"], "reason": r["errors"][:5],
                          "output_tail": text[-300:]})
            print(f"[{idx:>3}] {case['case_id']:<44} ✗ {len(r['errors'])} "
                  f"issue(s): {reason} — F1 {f1:.2f} ({secs:.0f}s)")

    # --- report ---
    print("\n=== Zero-shot results by input type ===")
    print(f"{'type':<8}{'n':>5}{'err':>5}{'parse%':>8}{'valid%':>8}{'F1':>7}"
          f"{'avg_s':>7}")
    agg = _new()
    report_types: dict[str, dict] = {}

    def _row(label: str, s: dict) -> str:
        n = s["n"]
        if n == 0:
            return f"{label:<8}{0:>5}{'--':>5}{'--':>8}{'--':>8}{'--':>7}{'--':>7}"
        ok = n - s["err"]
        f1 = f1_from_counts(s["tp"], s["fp"], s["fn"])
        avg = s["secs"] / ok if ok else 0.0
        return (f"{label:<8}{n:>5}{s['err']:>5}"
                f"{100*s['parse']/n:>7.0f}%{100*s['valid']/n:>7.0f}%"
                f"{f1:>7.2f}{avg:>7.0f}")

    for t in INPUT_TYPES:
        if t not in stats:
            continue
        s = stats[t]
        for k in agg:
            agg[k] += s[k]
        report_types[t] = dict(s, f1=f1_from_counts(s["tp"], s["fp"], s["fn"]))
        print(_row(t, s))
    print(_row("ALL", agg))
    overall_valid = 100 * agg["valid"] / agg["n"] if agg["n"] else 0.0
    print("\nerr    = call failed (transport / model can't take the medium)")
    print("parse% = produced parseable JSON")
    print("valid% = passed the strict canonical-schema validator")
    print("F1     = micro-F1 of structural atoms vs gold (as in eval_local.py)")

    safe_model = model.replace(":", "_").replace("/", "_")
    report_path = args.cases_dir / f"report_{safe_model}.json"
    report_path.write_text(json.dumps({
        "model": model,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "types": report_types,
        "overall": dict(agg, f1=f1_from_counts(agg["tp"], agg["fp"], agg["fn"]),
                        valid_pct=overall_valid),
    }, indent=2), encoding="utf-8")
    print(f"\nReport -> {report_path}")

    if args.dump and fails:
        args.dump.parent.mkdir(parents=True, exist_ok=True)
        with args.dump.open("w", encoding="utf-8") as f:
            for fa in fails:
                f.write(json.dumps(fa, ensure_ascii=False) + "\n")
        print(f"Wrote {len(fails)} failing cases -> {args.dump}")

    if overall_valid < args.min_valid:
        print(f"\nFAIL: overall valid {overall_valid:.0f}% < "
              f"--min-valid {args.min_valid:.0f}%")
        return 1
    return 0


# --- CLI --------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="write out/testcases/ manifest + inputs")
    b.add_argument("--out", type=Path, default=CASES_DIR)
    b.add_argument("--limit", type=int, default=0,
                   help="only the first N projects (0 = all)")

    r = sub.add_parser("run", help="zero-shot eval of a base model via Ollama")
    r.add_argument("--model", default="qwen3.5",
                   help="Ollama model tag; image cases need a vision-capable "
                        "tag (default: qwen3.5)")
    r.add_argument("--cases-dir", type=Path, default=CASES_DIR)
    r.add_argument("--types", default=",".join(INPUT_TYPES),
                   help="comma list of input types to run")
    r.add_argument("--per-type", type=int, default=0,
                   help="at most N cases per input type (0 = all)")
    r.add_argument("--limit", type=int, default=0, help="total case cap")
    r.add_argument("--max-tokens", type=int, default=12288,
                   help="generation budget; full records run ~9k tokens")
    r.add_argument("--dump", type=Path, default=None,
                   help="write failing cases to this JSONL")
    r.add_argument("--min-valid", type=float, default=0.0,
                   help="exit 1 if overall valid%% falls below this (a "
                        "zero-shot base model may legitimately score 0)")
    args = ap.parse_args()

    if args.cmd == "build":
        cases = build_cases(args.out, limit=args.limit)
        by_type = defaultdict(int)
        for c in cases:
            by_type[c["input_type"]] += 1
        print(f"Built {len(cases)} cases -> {args.out / 'cases.jsonl'}")
        print("  " + "  ".join(f"{t}: {by_type[t]}" for t in INPUT_TYPES))
        return 0
    return run_eval(args)


if __name__ == "__main__":
    sys.exit(main())
