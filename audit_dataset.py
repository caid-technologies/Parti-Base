"""Run the semantic audit (prompt ↔ design coverage) on the full dataset.

Writes:
  out/audit_report.json   full per-record findings
  out/audit_summary.txt   human-readable rollup
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from synth.config import OUT_DIR
from synth.semantic_audit import audit_dataset


def _load_records() -> list[dict]:
    records: list[dict] = []
    for p in sorted((OUT_DIR / "normalized").glob("*.json")):
        records.append(json.loads(p.read_text(encoding="utf-8")))
    variants_dir = OUT_DIR / "variants"
    if variants_dir.exists():
        for p in sorted(variants_dir.glob("*.json")):
            records.append(json.loads(p.read_text(encoding="utf-8")))
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, default=OUT_DIR / "audit_report.json")
    ap.add_argument("--summary", type=Path, default=OUT_DIR / "audit_summary.txt")
    args = ap.parse_args()

    records = _load_records()
    print(f"Auditing {len(records)} records...")
    report = audit_dataset(records)
    summary = report["summary"]

    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines: list[str] = [
        "=== Semantic Audit Summary ===",
        f"Total records: {summary['total_records']}",
        f"Records with prompt keywords detected: {summary['records_with_prompt_keywords']}",
        f"Records with mismatches: {summary['records_with_mismatches']} "
        f"({100*summary['records_with_mismatches']/summary['total_records']:.1f}%)",
        f"Total mismatches across dataset: {summary['total_mismatches']}",
        "",
        "Mismatch frequency by keyword:",
    ]
    for kw, n in summary["mismatch_keyword_frequency"].items():
        lines.append(f"  {n:4d}  {kw}")
    lines.append("")
    lines.append("By variant_type:")
    for vt, d in summary["by_variant_type"].items():
        rate = 100 * d["with_mismatches"] / d["records"] if d["records"] else 0
        lines.append(f"  {vt}: {d['records']} records, {d['with_mismatches']} with mismatches "
                     f"({rate:.1f}%), {d['mismatches']} mismatches total")
    lines.append("")
    lines.append(f"Full per-record report: {args.report}")

    summary_text = "\n".join(lines) + "\n"
    args.summary.write_text(summary_text, encoding="utf-8")
    print(summary_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
