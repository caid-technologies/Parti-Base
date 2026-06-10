"""Convert (system, user, assistant) row tuples to ChatML JSONL.

================================ OVERVIEW ====================
This is the FINAL packaging step of Stage 4. The mode generators in staged.py
hand us raw (system, user, assistant) triples; this file wraps each one in the
"ChatML" format the training tooling expects, removes duplicates, shuffles the
order, and writes everything to a `.jsonl` file (one JSON object per line).

  - ChatML = a list of {role, content} message dicts (system/user/assistant).
  - JSONL  = "JSON Lines": a text file where each line is one complete JSON
             record. It's the standard input format for fine-tuning.

This file is deliberately generic: it doesn't care that staged.py produced the
rows — anything yielding the same triples could feed it.
============================================================================
"""
from __future__ import annotations
import hashlib   # for fingerprinting rows so we can detect duplicates
import json
import random    # for deterministic shuffling
from collections import Counter        # tallies counts per tag
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def to_chatml(system_prompt: str, user_prompt: str, assistant_content: str) -> dict:
    """Wrap one conversation turn into the ChatML message-list shape.

    The result is one training example: the model is shown the system + user
    messages and learns to produce the assistant message.
    """
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def _row_hash(system: str, user: str) -> str:
    """Make a fingerprint of a row's INPUT (system + user) for dedup.

    We hash only the input, not the answer: two examples with identical inputs
    are duplicates even if their outputs differ. `" ".join(text.split())`
    normalizes all whitespace so trivial spacing differences don't slip past the
    check. `hashlib.sha256(...).hexdigest()` turns the text into a fixed-length
    fingerprint string; identical inputs always produce the same fingerprint.
    """
    norm = " ".join((system + "||" + user).lower().split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def write_jsonl(
    rows: Iterable[tuple],
    out_path: Path,
    seed: int = 0,
) -> dict[str, Any]:
    """De-duplicate, shuffle, and write the rows as a ChatML JSONL file.

    Returns a small stats dict (how many written, how many dupes dropped, and a
    per-tag breakdown). Each input row is either a 3-tuple (system, user,
    assistant) or a 4-tuple with a trailing `tag` (the mode letter) used only
    for accounting.
    """
    seen: set[str] = set()              # fingerprints we've already kept
    records: list[tuple[dict, str | None]] = []
    duplicates = 0

    for row in rows:
        # Rows may have an optional 4th element (the tag). Unpack accordingly.
        if len(row) == 4:
            system, user, asst, tag = row
        else:
            system, user, asst = row
            tag = None
        h = _row_hash(system, user)
        if h in seen:
            duplicates += 1
            continue        # skip — we've already kept an identical input
        seen.add(h)
        records.append((to_chatml(system, user, asst), tag))

    # Shuffle so the modes are interleaved, not grouped — better for training.
    # `random.Random(seed)` makes the shuffle REPRODUCIBLE: the same seed always
    # yields the same order, so runs are repeatable.
    random.Random(seed).shuffle(records)

    out_path.parent.mkdir(parents=True, exist_ok=True)  # ensure folder exists
    tag_counts: Counter = Counter()
    # Open the output file and write one JSON object per line.
    with out_path.open("w", encoding="utf-8") as f:
        for rec, tag in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if tag is not None:
                tag_counts[tag] += 1    # Counter auto-starts missing keys at 0

    return {
        "written": len(records),
        "duplicates_dropped": duplicates,
        "by_tag": dict(tag_counts),
    }
