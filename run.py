"""Orchestrator: normalize → generate variants (LLM) → derive Mode A–F rows.

================================ OVERVIEW ====================
This is the MAIN ENTRY POINT — the script you actually run ("python run.py").
It ties the whole pipeline together by calling the synth/ modules in order. It
doesn't do the transformation work itself; it COORDINATES the stages and prints
progress.

The stages it runs:
  Stage 0 (optional)  generate brand-new projects with the LLM (--new-projects)
  Stage 1             make sure out/normalized/ holds clean canonical records
                      (runs normalize.py on the Data/ seeds if needed)
  Stage 3 (optional)  generate variants via phase_variants.py (--enable-variants)
  Stage 4             turn every record into Mode A–F training rows and write
                      the final out/pilot.jsonl

Run it with `--dry-run` first to see projected counts without writing anything.
Everything is controlled by command-line flags parsed in `main()` near the
bottom; reading `main()` top-to-bottom is the best way to follow the flow.
============================================================================
"""
from __future__ import annotations
import argparse   # parses command-line flags like --enable-variants
import json
import sys
import time        # for timing how long each stage takes
from pathlib import Path

# Force UTF-8 stdout/stderr so non-ASCII in any printed string (em-dashes,
# arrows, part names) can never crash a long unattended run on a Windows
# cp1252 console. `errors="replace"` makes encoding failures impossible.
for _stream in ("stdout", "stderr"):
    _s = getattr(sys, _stream)
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

from synth.assemble import write_jsonl
from synth.assembly_check import coverage_summary_lines, filter_compliant
from synth.config import MODEL_ID, NORMALIZED_DIR, OLLAMA_BASE_URL, OUT_DIR
from synth.corpus import iter_configs
from synth.fixup import fixup_record
from synth.normalize import normalize_seed
from synth.staged import MODE_GENERATORS, iter_rows
from synth.validate import is_valid

VARIANTS_DIR = OUT_DIR / "variants"   # where Stage 3 writes its variant files


def _ensure_normalized(force: bool = False, skip_data: bool = False) -> list[dict]:
    """Make sure out/normalized/*.json is current. Return loaded records.

    With skip_data=True the Data/ example corpus is NOT normalized into
    out/normalized — the run operates only on records already present there
    (e.g. generated projects, plus any just written by Stage 0). This keeps a
    generated-only normalized set from being polluted by the example seeds.
    """
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

    if skip_data:
        existing = sorted(NORMALIZED_DIR.glob("*.json"))
        print(f"Skipping Data/ normalization (--no-data-seed); using "
              f"{len(existing)} records already in {NORMALIZED_DIR}")
        return [json.loads(p.read_text(encoding="utf-8")) for p in existing]

    # Load the raw corpus and compare what's expected vs what's already on disk.
    # `{p.stem for ...}` is a set of filenames-without-extension already present.
    raw_corpus = list(iter_configs())
    existing = {p.stem for p in NORMALIZED_DIR.glob("*.json")}
    expected = {slug for slug, _ in raw_corpus}

    # Re-normalize only if forced, or if some expected record is missing.
    # `expected.issubset(existing)` is True when every expected file already exists.
    if force or not expected.issubset(existing):
        print(f"Normalizing {len(raw_corpus)} seeds -> {NORMALIZED_DIR}")
        repaired = 0
        for slug, raw_cfg in raw_corpus:
            rec = normalize_seed(slug, raw_cfg)   # Stage 1 transform (normalize.py)
            # Auto-repair seeds that fail strict validation (dangling refs,
            # empty instructions, etc.) so a clean-slate run is self-healing.
            if not is_valid(rec):
                rec, _ = fixup_record(rec)        # try to fix it (fixup.py)
                if is_valid(rec):
                    repaired += 1
            (NORMALIZED_DIR / f"{slug}.json").write_text(
                json.dumps(rec, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if repaired:
            print(f"  auto-repaired {repaired} seeds via fixup")
    else:
        print(f"Reusing {len(expected)} normalized records from {NORMALIZED_DIR}")

    # Load every normalized record back from disk and return the list.
    records: list[dict] = []
    for p in sorted(NORMALIZED_DIR.glob("*.json")):
        records.append(json.loads(p.read_text(encoding="utf-8")))
    return records


def _load_variants() -> list[dict]:
    """Load all Stage 3 variant records from out/variants/ (empty if none yet)."""
    if not VARIANTS_DIR.exists():
        return []
    out: list[dict] = []
    for p in sorted(VARIANTS_DIR.glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def _projected_counts(records: list[dict]) -> dict[str, int]:
    """Count, per mode, how many of these records would produce a training row.

    A dry-run preview: it runs each mode's generator just to check it returns
    something (not None), without building the actual dataset. `{m: 0 for m in
    MODE_GENERATORS}` is a dict comprehension seeding every mode's count at 0.
    """
    counts = {m: 0 for m in MODE_GENERATORS}
    for rec in records:
        for mode, fn in MODE_GENERATORS.items():
            if fn(rec) is not None:
                counts[mode] += 1
    return counts


def main() -> int:
    """The program's starting point. Returns an exit code (0 = success).

    Reads command-line flags, then runs Stage 0/1/3/4 in sequence, printing a
    progress report. Each `ap.add_argument(...)` below declares one CLI flag.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT_DIR / "pilot.jsonl")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--modes", type=str, default="ABCDEF",
                    help="Which modes to emit, as a string of letters. Default: ABCDEF.")
    ap.add_argument("--force-normalize", action="store_true",
                    help="Re-run Stage 1 even if normalized files already exist.")
    ap.add_argument("--no-data-seed", action="store_true",
                    help="Don't normalize the Data/ example corpus into "
                         "out/normalized; operate only on records already there "
                         "(keeps a generated-only set).")
    ap.add_argument("--new-projects", type=int, default=0,
                    help="Stage 0: generate N brand-new LLM projects into "
                         "out/normalized/ before normalizing the corpus.")
    ap.add_argument("--enable-variants", action="store_true",
                    help="Run Stage 3 (LLM variant generation) before assembly.")
    ap.add_argument("--force-variants", action="store_true",
                    help="Regenerate variants even if cached files exist (implies --enable-variants).")
    ap.add_argument("--variant-seeds-limit", type=int, default=None,
                    help="Cap on how many seeds get variants (for smoke tests).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Project row counts; do not write pilot.jsonl.")
    args = ap.parse_args()

    print(f"Ollama endpoint: {OLLAMA_BASE_URL}")
    print(f"Model:           {MODEL_ID}")
    print(f"Output:          {args.out}")
    print()

    # Turn the "ABCDEF" string into a list of single letters and reject typos.
    modes = list(args.modes.upper())
    bad_modes = [m for m in modes if m not in MODE_GENERATORS]
    if bad_modes:
        print(f"Unknown modes: {bad_modes}. Valid: {list(MODE_GENERATORS.keys())}")
        return 1   # non-zero exit code signals an error to the shell

    started = time.time()   # remember the start time to report total elapsed

    # --- Stage 0: new LLM-generated projects (optional) ---
    if args.new_projects > 0:
        from synth.new_projects import generate_new_projects

        print(f"=== Stage 0: generating {args.new_projects} new projects ===")
        s0 = time.time()
        np_stats = generate_new_projects(
            NORMALIZED_DIR, count=args.new_projects, seed=args.seed,
        )
        print(f"Stage 0 stats: {np_stats}")
        print(f"Stage 0 elapsed: {time.time() - s0:.1f}s")
        print()

    # --- Stage 1: normalize the seeds (and load every normalized record) ---
    seeds = _ensure_normalized(force=args.force_normalize, skip_data=args.no_data_seed)
    # `sum(1 for r in ... if is_valid(r))` counts how many records pass validation.
    clean = sum(1 for r in seeds if is_valid(r))
    print(f"Normalized: {len(seeds)} records, {clean} pass strict validation.")
    print()

    # --- Stage 3 (optional): build variants from the clean seeds ---
    enable_variants = args.enable_variants or args.force_variants
    if enable_variants:
        # Import here (not at top) so a normal run never needs the LLM modules.
        from synth.phase_variants import generate_variants

        # Pair each valid seed with its id, as phase_variants expects.
        clean_seeds = [(r["project"]["project_id"], r) for r in seeds if is_valid(r)]
        if args.variant_seeds_limit is not None:
            clean_seeds = clean_seeds[: args.variant_seeds_limit]   # cap for smoke tests
        print(f"=== Stage 3: variant generation over {len(clean_seeds)} clean seeds ===")
        stage3_start = time.time()
        v_stats = generate_variants(
            clean_seeds,
            out_dir=VARIANTS_DIR,
            seed=args.seed,
            force=args.force_variants,
        )
        print(f"Stage 3 stats: {v_stats}")
        print(f"Stage 3 elapsed: {time.time() - stage3_start:.1f}s")
        print()

    # --- Load all records (seeds + any existing variants) for assembly ---
    variants = _load_variants()
    all_records = seeds + variants   # `+` concatenates the two lists
    print(f"Available for assembly: {len(seeds)} seeds + {len(variants)} variants = {len(all_records)}")
    print()

    # --- Assembly-instruction gate: only emit objects with COMPLETE detailed
    # assembly instructions. Non-compliant objects are skipped + logged (never
    # repaired here). The rule lives in synth/assembly_check.py. ---
    all_records, coverage = filter_compliant(all_records, log=print)
    for line in coverage_summary_lines(coverage):
        print(line)
    print()

    # Preview how many rows each mode will yield before doing the real work.
    projected = _projected_counts(all_records)
    print("Projected per-mode rows (before dedup):")
    for mode in modes:
        print(f"  Mode {mode}: {projected[mode]}")
    print(f"  Total ceiling: {sum(projected[m] for m in modes)}")
    print()

    # In dry-run mode we stop here, having printed the projection but no files.
    if args.dry_run:
        print("DRY RUN - not writing pilot.")
        return 0

    # --- Stage 4: build all the rows and write the final JSONL dataset ---
    # `iter_rows` (staged.py) yields rows lazily; `list(...)` collects them all.
    rows = list(iter_rows(all_records, modes=modes))
    stats = write_jsonl(rows, args.out, seed=args.seed)   # dedup + shuffle + write
    elapsed = time.time() - started

    print(f"Wrote {stats['written']} records to {args.out}")
    print(f"  Duplicates dropped: {stats['duplicates_dropped']}")
    print(f"  By mode:            {stats['by_tag']}")
    print(f"  Total elapsed:      {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
