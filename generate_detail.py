"""Generate detailed assembly instructions for the dataset projects (LLM step).

================================ OVERVIEW ====================
Most projects have bare instruction titles with no body, so the assembly gate
(synth/assembly_check.py) skips them. This script uses the local LLM (Ollama) to
write a real {summary, steps, tip} detail body for every step that lacks one,
across the whole normalized corpus, then writes the enriched records back to
out/normalized/. After this, those projects pass the gate; variants derived
from them inherit the detail.

Sources (default: both):
  - data        : the 42 hand-authored Data/ seeds (normalized fresh if absent)
  - normalized  : every record already in out/normalized/ (e.g. the new_* LLM
                  projects that make up the existing corpus)

It NEVER fabricates parts — each step's detail is grounded in that step's real
components. Steps whose LLM call fails are left bodyless and get skipped
downstream rather than filled with junk.

RESUMABLE: each record is written the moment it's enriched, and steps that are
already complete are skipped (no LLM call). Re-running continues where it left
off; pass --force to regenerate every step.

Usage:
    python generate_detail.py                      # enrich data + normalized
    python generate_detail.py --source normalized  # only out/normalized/*
    python generate_detail.py --limit 3            # smoke test: first 3 records
    python generate_detail.py --force              # regenerate every step
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

# Force UTF-8 + line-buffered stdout so part names / arrows can't crash a long
# Windows run and progress streams live (not block-buffered) when piped.
for _stream in ("stdout", "stderr"):
    _s = getattr(sys, _stream)
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except (ValueError, OSError):
            pass

from synth.assembly_check import (
    coverage_summary_lines, filter_compliant, is_assembly_complete,
)
from synth.config import MODEL_ID, NORMALIZED_DIR, OLLAMA_BASE_URL
from synth.corpus import iter_configs
from synth.fixup import fixup_record
from synth.instruction_detail import enrich_record
from synth.normalize import normalize_seed
from synth.ollama_client import chat_text
from synth.validate import is_valid


def _preflight() -> bool:
    """Confirm the LLM is reachable before starting a long run."""
    print(f"Ollama endpoint: {OLLAMA_BASE_URL}")
    print(f"Model:           {MODEL_ID}")
    try:
        chat_text(
            [{"role": "user", "content": "reply with the single word: ok"}],
            max_tokens=5,
        )
        print("LLM reachable. Starting.\n")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"\nERROR: LLM not reachable ({type(e).__name__}: {e}).")
        print("Start Ollama and pull the model, then re-run:")
        print("  ollama serve            # if not already running")
        print(f"  ollama pull {MODEL_ID}")
        return False


def _ensure_data_seeds_present() -> int:
    """Normalize any of the 42 Data/ seeds not already in out/normalized.

    Existing files are left untouched so prior enrichment is preserved
    (resumable). Returns how many seed files were newly created.
    """
    created = 0
    for slug, raw_cfg in iter_configs():
        target = NORMALIZED_DIR / f"{slug}.json"
        if target.exists():
            continue
        rec = normalize_seed(slug, raw_cfg)
        if not is_valid(rec):
            rec, _ = fixup_record(rec)   # self-heal dangling refs etc. (as run.py)
        target.write_text(json.dumps(rec, indent=2, ensure_ascii=False),
                          encoding="utf-8")
        created += 1
    return created


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", choices=["data", "normalized", "both"],
                    default="both",
                    help="Which records to enrich (default: both).")
    ap.add_argument("--limit", type=int, default=None,
                    help="Only process the first N records (smoke test).")
    ap.add_argument("--force", action="store_true",
                    help="Regenerate detail for every step, not just missing ones.")
    args = ap.parse_args()

    if not _preflight():
        return 1

    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

    # Make sure the Data/ seeds exist on disk when they're in scope.
    if args.source in ("data", "both"):
        seed_slugs = {slug for slug, _ in iter_configs()}
        created = _ensure_data_seeds_present()
        if created:
            print(f"Normalized {created} missing Data/ seeds into {NORMALIZED_DIR}\n")
    else:
        seed_slugs = set()

    # Decide which files to enrich.
    all_files = sorted(NORMALIZED_DIR.glob("*.json"))
    if args.source == "data":
        files = [p for p in all_files if p.stem in seed_slugs]
    elif args.source == "normalized":
        files = all_files
    else:  # both
        files = all_files
    if args.limit is not None:
        files = files[: args.limit]

    print(f"Enriching {len(files)} records (source={args.source}, force={args.force})\n")

    started = time.time()
    enriched: list[dict] = []
    totals = {"generated": 0, "already_ok": 0, "failed": 0}

    for idx, path in enumerate(files, start=1):
        rec = json.loads(path.read_text(encoding="utf-8"))
        pid = rec.get("project", {}).get("project_id", path.stem)
        elapsed = time.time() - started
        print(f"[{idx}/{len(files)}] {pid}  (elapsed {elapsed/60:.1f}m)")
        stats = enrich_record(rec, force=args.force)
        for k in totals:
            totals[k] += stats[k]
        complete, reason = is_assembly_complete(rec)
        flag = "OK" if complete else f"INCOMPLETE ({reason})"
        print(f"    steps={stats['steps_total']} generated={stats['generated']} "
              f"already_ok={stats['already_ok']} failed={stats['failed']} -> {flag}")
        # Write the moment it's enriched so an interrupted run loses nothing.
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False),
                        encoding="utf-8")
        enriched.append(rec)

    print()
    print(f"Detail generation: generated {totals['generated']}, "
          f"already_ok {totals['already_ok']}, failed {totals['failed']} "
          f"in {(time.time() - started)/60:.1f}m")
    print()

    _, coverage = filter_compliant(enriched)
    for line in coverage_summary_lines(coverage):
        print(line)
    print()
    print("Next: build the dataset from the enriched projects:")
    print("  python run.py --enable-variants --force-variants   # + variants, gated")
    print("  python prepare_training.py                          # out/train/*.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
