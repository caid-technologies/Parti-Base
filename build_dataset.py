"""Write the synthesized dataset as folder-per-project bundles.

================================ OVERVIEW ====================
The other output of this project is out/pilot.jsonl (the training file). THIS
script produces the SECOND output format: it takes the clean canonical records
and writes each one back out as a folder of files that looks exactly like the
original hand-authored projects in Data/ (a CONFIG.json, a GUIDE.md, two
connection files, and a PARTS.csv).

In short: normalize.py converts Data/ folders → canonical records; this file
does the REVERSE, canonical records → Data/-style folders. The actual
record→files conversion lives in synth/denormalize.py; this script just loops
over every record, calls that, and writes the files to disk. It also copies the
seed's preview PNG across when one exists.

Run it AFTER run.py has populated out/normalized/ (and optionally out/variants/).

Usage:
    python build_dataset.py                 # seeds + variants → out/dataset/
    python build_dataset.py --seeds-only    # just the 42 normalized seeds
    python build_dataset.py --out path      # alternate output directory
============================================================================
"""
from __future__ import annotations
import argparse
import json
import shutil        # used to copy PNG files
import sys
from pathlib import Path

from synth.assembly_check import coverage_summary_lines, filter_compliant
from synth.config import DATA_DIR, OUT_DIR
from synth.denormalize import denormalize   # canonical record → 5 file contents
from synth.normalize import to_snake_id


def _build_data_folder_map() -> dict[str, Path]:
    """Map normalized project_id → original Data/ folder.

    Source folders may use characters (dashes, parens, non-ASCII) that get
    stripped during `to_snake_id`, so the project_id doesn't match the folder
    name directly. Build a lookup once.
    """
    out: dict[str, Path] = {}
    for folder in DATA_DIR.iterdir():
        if not folder.is_dir():
            continue
        slug = folder.name.removesuffix("_files")
        out[to_snake_id(slug)] = folder
    return out


def _load_records(seeds_only: bool) -> list[dict]:
    """Read all canonical records from out/normalized/ (and out/variants/).

    When `seeds_only` is True we skip the variants folder and emit just the
    original normalized seeds.
    """
    records: list[dict] = []
    for p in sorted((OUT_DIR / "normalized").glob("*.json")):
        records.append(json.loads(p.read_text(encoding="utf-8")))
    if not seeds_only:
        variants_dir = OUT_DIR / "variants"
        if variants_dir.exists():
            for p in sorted(variants_dir.glob("*.json")):
                records.append(json.loads(p.read_text(encoding="utf-8")))
    return records


def main() -> int:
    """Entry point: load records, denormalize each into files, report counts."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds-only", action="store_true",
                    help="Skip variants — only emit the 42 normalized seeds.")
    ap.add_argument("--out", type=Path, default=OUT_DIR / "dataset",
                    help="Output directory (default: out/dataset).")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    records = _load_records(seeds_only=args.seeds_only)
    data_folder_map = _build_data_folder_map()
    print(f"Loaded {len(records)} records "
          f"({'seeds only' if args.seeds_only else 'seeds + variants'}).")

    # Assembly-instruction gate: only write folders for objects whose assembly
    # instructions are COMPLETE and detailed (shared rule in
    # synth/assembly_check.py). Skipped object_ids are logged + summarized.
    records, coverage = filter_compliant(records, log=print)
    for line in coverage_summary_lines(coverage):
        print(line)
    print(f"Writing to {args.out}")
    print()

    # Running tallies for the final report.
    written = 0
    pngs_copied = 0
    skipped: list[str] = []
    # Count how many of each variant_type we emit, for the summary.
    by_kind = {"seed": 0, "prompt_rewrite": 0, "positive_variant": 0,
               "evaluation_negative": 0, "unknown": 0}

    for rec in records:
        # `rec.get("project", {}).get(...)` safely reaches into nested dicts: if
        # "project" is missing it uses an empty dict so the second .get can't crash.
        pid = rec.get("project", {}).get("project_id")
        if not pid:
            skipped.append("<missing project_id>")   # can't name the folder — skip
            continue
        vt = rec.get("project", {}).get("variant_type", "unknown")
        by_kind[vt] = by_kind.get(vt, 0) + 1

        # Make the project's folder, then write each of the 5 files into it.
        folder = args.out / f"{pid}_files"
        folder.mkdir(exist_ok=True)
        bundle = denormalize(rec)   # dict of {filename_suffix: file_contents}
        for suffix, content in bundle.items():
            (folder / f"{pid}{suffix}").write_text(content, encoding="utf-8")
        written += 1

        # If this record traces back to a real seed PNG, copy that image across
        # so the rebuilt folder visually matches the original. Variants whose
        # design changed have visual_ref=None and are skipped here.
        visual_ref = rec.get("project", {}).get("visual_ref")
        seed_pid = rec.get("project", {}).get("seed_project_id")
        if visual_ref and seed_pid:
            src_folder = data_folder_map.get(seed_pid)
            if src_folder is not None:
                # PNG file in the source folder may use a different stem than seed_pid.
                pngs = list(src_folder.glob("*VISUAL.png"))
                if pngs:
                    dst_png = folder / f"{pid}_VISUAL.png"
                    shutil.copyfile(pngs[0], dst_png)
                    pngs_copied += 1

    print(f"Wrote {written} project folders, skipped {len(skipped)}.")
    print(f"Copied {pngs_copied} visual PNGs into seed/rewrite folders.")
    print()
    print("By variant_type:")
    for k, n in by_kind.items():
        if n:
            print(f"  {k}: {n}")
    if skipped:
        print(f"\nSkipped: {skipped[:5]}{'...' if len(skipped) > 5 else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
