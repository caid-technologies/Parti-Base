"""Run the offline normalizer on every seed in Data/.

Writes one canonical-schema JSON per project to `out/normalized/<slug>.json`
and prints an aggregate summary.
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from synth.config import OUT_DIR
from synth.corpus import iter_configs
from synth.normalize import normalize_seed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR / "normalized")
    ap.add_argument("--summary-only", action="store_true",
                    help="Skip writing files, just print the stats.")
    args = ap.parse_args()

    if not args.summary_only:
        args.out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    clean = 0
    with_issues = 0
    issue_codes = Counter()
    confidence_buckets = Counter()
    rejected = []

    for slug, raw_cfg in iter_configs():
        total += 1
        normalized = normalize_seed(slug, raw_cfg)
        issues = normalized["validation"]["issues"]
        score = normalized["validation"]["confidence_score"]
        if issues:
            with_issues += 1
            for it in issues:
                issue_codes[it["code"]] += 1
            if score < 0.5:
                rejected.append((slug, len(issues)))
        else:
            clean += 1

        bucket = (
            "1.0" if score == 1.0
            else "0.7" if score == 0.7
            else "0.4"
        )
        confidence_buckets[bucket] += 1

        if not args.summary_only:
            out_path = args.out_dir / f"{slug}.json"
            out_path.write_text(
                json.dumps(normalized, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    print(f"=== Normalization results ===")
    print(f"Total seeds:        {total}")
    print(f"Clean (no issues):  {clean}")
    print(f"With issues:        {with_issues}")
    print()
    print(f"Confidence distribution:")
    for b in ("1.0", "0.7", "0.4"):
        print(f"  {b}: {confidence_buckets[b]}")
    print()
    print(f"Issue code frequency:")
    for code, count in issue_codes.most_common():
        print(f"  {count:4d}  {code}")
    if rejected:
        print()
        print(f"Low-confidence (<0.5) seeds:")
        for slug, n in rejected:
            print(f"  {slug}: {n} issues")

    if not args.summary_only:
        print()
        print(f"Wrote {total} files to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
