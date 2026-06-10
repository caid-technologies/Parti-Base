"""Build a training-ready dataset from the normalized + variant records.

Produces, under out/train/:
  train.jsonl        ChatML rows for fine-tuning
  val.jsonl          held-out validation rows
  test.jsonl         held-out test rows
  dataset_card.md    stats: counts, split sizes, length distribution, mode mix
  length_report.txt  token-length percentiles (to choose max_seq_len)

Split is GROUPED by base (seed) project: every variant and every task-mode
row of a given project lands in exactly one split, so val/test measure
generalization to UNSEEN projects rather than memorized rephrasings.

Builds rows directly from out/normalized/ + out/variants/ (not pilot.jsonl)
so every row carries a reliable group key.

Usage:
  python prepare_training.py
  python prepare_training.py --val 0.1 --test 0.1 --seed 0
  python prepare_training.py --format both     # also emit Alpaca-style
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from synth.config import OUT_DIR
from synth.assemble import to_chatml
from synth.staged import iter_rows

CHARS_PER_TOKEN = 4.0  # rough estimate; confirm with the real tokenizer.


def _load_records() -> list[dict]:
    recs: list[dict] = []
    for p in sorted((OUT_DIR / "normalized").glob("*.json")):
        recs.append(json.loads(p.read_text(encoding="utf-8")))
    vdir = OUT_DIR / "variants"
    if vdir.exists():
        for p in sorted(vdir.glob("*.json")):
            recs.append(json.loads(p.read_text(encoding="utf-8")))
    return recs


def _base_project(rec: dict) -> str:
    proj = rec.get("project", {})
    return proj.get("seed_project_id") or proj.get("project_id") or "unknown"


def _row_chars(rec: dict) -> int:
    return sum(len(m["content"]) for m in rec["messages"])


def _to_alpaca(rec: dict) -> dict:
    msgs = {m["role"]: m["content"] for m in rec["messages"]}
    return {
        "instruction": msgs.get("system", ""),
        "input": msgs.get("user", ""),
        "output": msgs.get("assistant", ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR / "train")
    ap.add_argument("--val", type=float, default=0.1)
    ap.add_argument("--test", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--format", choices=["chatml", "alpaca", "both"],
                    default="chatml")
    args = ap.parse_args()

    records = _load_records()
    if not records:
        print("No records found — run 'python run.py' first.")
        return 1
    print(f"Loaded {len(records)} source records "
          f"({sum(1 for r in records if r['project'].get('variant_type') == 'seed')} seeds)")

    # Build ChatML rows grouped by base project, deduped by (system+user).
    grouped: dict[str, list[dict]] = defaultdict(list)
    seen: set[str] = set()
    dup = 0
    mode_mix: Counter = Counter()
    for rec in records:
        base = _base_project(rec)
        for system, user, asst, mode in iter_rows([rec]):
            key = hashlib.sha256(
                " ".join((system + "||" + user).lower().split()).encode()
            ).hexdigest()
            if key in seen:
                dup += 1
                continue
            seen.add(key)
            grouped[base].append(to_chatml(system, user, asst))
            mode_mix[mode] += 1

    total_rows = sum(len(v) for v in grouped.values())
    base_keys = sorted(grouped.keys())
    print(f"Built {total_rows} unique rows ({dup} duplicates dropped) "
          f"across {len(base_keys)} base projects")

    # Split GROUPS so no project leaks across splits.
    rng = random.Random(args.seed)
    rng.shuffle(base_keys)
    n = len(base_keys)
    n_test = max(1, int(n * args.test))
    n_val = max(1, int(n * args.val))
    test_g = set(base_keys[:n_test])
    val_g = set(base_keys[n_test:n_test + n_val])

    splits: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for base, rows in grouped.items():
        bucket = "test" if base in test_g else "val" if base in val_g else "train"
        splits[bucket].extend(rows)
    for rows in splits.values():
        rng.shuffle(rows)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    def _write(name: str, data: list[dict], alpaca: bool) -> None:
        with (args.out_dir / name).open("w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(_to_alpaca(r) if alpaca else r,
                                   ensure_ascii=False) + "\n")

    emit_chatml = args.format in ("chatml", "both")
    emit_alpaca = args.format in ("alpaca", "both")
    for bucket, data in splits.items():
        if emit_chatml:
            _write(f"{bucket}.jsonl", data, alpaca=False)
        if emit_alpaca:
            _write(f"{bucket}.alpaca.jsonl", data, alpaca=True)

    # --- length report ---
    all_rows = [r for rows in splits.values() for r in rows]
    tok_lens = sorted(int(_row_chars(r) / CHARS_PER_TOKEN) for r in all_rows)

    def _pct(p: float) -> int:
        return tok_lens[min(len(tok_lens) - 1, int(len(tok_lens) * p))]

    p99 = _pct(0.99)
    suggested_seq = 1 << max(9, p99.bit_length())

    length_lines = [
        "=== Token-length distribution (est. ~4 chars/token) ===",
        f"  rows: {len(tok_lens)}",
        f"  min:  {tok_lens[0]}",
        f"  p50:  {_pct(0.50)}",
        f"  p90:  {_pct(0.90)}",
        f"  p95:  {_pct(0.95)}",
        f"  p99:  {p99}",
        f"  max:  {tok_lens[-1]}",
        "",
        f"Suggested max_seq_len: {suggested_seq} (covers p99)",
        "NOTE: estimate only — confirm with your model's tokenizer.",
    ]
    (args.out_dir / "length_report.txt").write_text(
        "\n".join(length_lines) + "\n", encoding="utf-8")

    # --- dataset card ---
    card = [
        "# Dataset Card — hobbyist hardware project design",
        "",
        "Synthetic SFT dataset: plain-language prompt -> structured buildable",
        "project (components, wiring, mechanical, instructions, sourcing).",
        "",
        "## Splits (grouped by base project — no leakage across splits)",
        f"- train: {len(splits['train'])} rows",
        f"- val:   {len(splits['val'])} rows",
        f"- test:  {len(splits['test'])} rows",
        f"- base projects: {n} (train {n - n_test - n_val}, "
        f"val {n_val}, test {n_test})",
        "",
        "## Task modes",
    ]
    for m in "ABCDEF":
        card.append(f"- Mode {m}: {mode_mix.get(m, 0)}")
    card += [
        "",
        "## Format",
        "ChatML messages JSONL — each line:",
        '`{"messages": [{"role":"system",...}, {"role":"user",...}, '
        '{"role":"assistant",...}]}`',
        "Works with TRL SFTTrainer, axolotl, LLaMA-Factory, Unsloth.",
        "Pass `--format both` to also emit Alpaca-style *.alpaca.jsonl.",
        "",
        "See length_report.txt for max_seq_len guidance.",
    ]
    (args.out_dir / "dataset_card.md").write_text(
        "\n".join(card) + "\n", encoding="utf-8")

    print(f"\nWrote to {args.out_dir}:")
    print(f"  train {len(splits['train'])}  val {len(splits['val'])}  "
          f"test {len(splits['test'])}")
    print(f"  base projects: train {n - n_test - n_val}, val {n_val}, test {n_test}")
    print("\n".join(length_lines))
    print(f"\nDataset card: {args.out_dir / 'dataset_card.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
