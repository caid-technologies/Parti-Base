"""Single source of truth: is an object's assembly instruction set complete?

============================ WHY THIS EXISTS ===============================
Every object the generator emits into the dataset MUST carry COMPLETE, DETAILED
assembly instructions. A record is NON-COMPLIANT when it has no build steps, or
when any step's body is missing/empty, is just a one-line title with no real
detail, or still contains the "*(not yet generated)*" placeholder.

The generator must never emit a non-compliant object and must never fabricate
the missing detail. The accept/write points (run.py, prepare_training.py,
build_dataset.py) call `filter_compliant()` here to drop non-compliant objects,
log why, and print a coverage summary so you know what to regenerate.

Keep the rule in THIS file only. Every sink imports it; nothing duplicates it.
============================================================================
"""
from __future__ import annotations

from collections.abc import Callable, Iterable

# The literal marker denormalize.py renders into GUIDE.md when a step has no
# real body. Its presence anywhere is an automatic non-compliance.
PLACEHOLDER = "*(not yet generated)*"

# A step body shorter than this (after stripping) is treated as "just a title
# with no real detail". Real source `detail` bodies run to hundreds of chars;
# this only catches empty / one-liner placeholders.
MIN_DETAIL_CHARS = 15


def _step_body_text(step: dict) -> str:
    """Collect the human-readable instruction body for one step.

    The body can live in a structured `detail` dict ({summary, steps, tip} —
    the shape carried over from the source CONFIG subSteps), in a plain `detail`
    string, and/or in `expected_result`. We concatenate whatever is present so
    the completeness test sees the full body regardless of which field holds it.
    """
    parts: list[str] = []
    detail = step.get("detail")
    if isinstance(detail, dict):
        if detail.get("summary"):
            parts.append(str(detail["summary"]))
        for s in detail.get("steps") or []:
            if str(s).strip():
                parts.append(str(s))
        if detail.get("tip"):
            parts.append(str(detail["tip"]))
    elif isinstance(detail, str):
        parts.append(detail)
    er = step.get("expected_result")
    if er and str(er).strip().lower() != "unknown":
        parts.append(str(er))
    return "\n".join(parts).strip()


def step_is_complete(step: dict) -> tuple[bool, str]:
    """Return (is_complete, reason) for ONE instruction step.

    The single per-step rule, shared by the gate (`is_assembly_complete`) and the
    detail generator (which uses it to decide which steps still need a body).
    """
    if not isinstance(step, dict):
        return False, "step is not an object"
    sid = step.get("step_id") or "<step>"
    title = str(step.get("title", "")).strip()

    # The placeholder marker is an automatic fail wherever it appears.
    if PLACEHOLDER in title:
        return False, f"step {sid!r} title contains placeholder marker"
    body = _step_body_text(step)
    if PLACEHOLDER in body:
        return False, f"step {sid!r} body contains placeholder marker"

    if not body:
        return False, f"step {sid!r} has empty/missing body"
    if body.strip().lower() == title.lower():
        return False, f"step {sid!r} is title-only (no real detail)"
    if len(body) < MIN_DETAIL_CHARS:
        return False, f"step {sid!r} body too short (no real detail)"
    return True, "ok"


def is_assembly_complete(record: dict) -> tuple[bool, str]:
    """Return (is_complete, reason).

    Complete iff the record has at least one instruction step AND every step
    passes `step_is_complete`. `reason` is "ok" when complete, otherwise names
    the first offending step so the skip log is actionable.
    """
    instructions = record.get("instructions")
    if not isinstance(instructions, list) or not instructions:
        return False, "no instruction steps"

    for step in instructions:
        ok, reason = step_is_complete(step)
        if not ok:
            return False, reason
    return True, "ok"


def guide_has_placeholder(guide_text: str) -> bool:
    """True if a rendered GUIDE.md still carries the placeholder marker.

    Defense-in-depth for the folder-format sink: even if a record slipped
    through, a GUIDE.md with this marker is non-compliant on its face.
    """
    return PLACEHOLDER in (guide_text or "")


def _object_id(record: dict) -> str:
    return (record.get("project") or {}).get("project_id") or "<unknown>"


def filter_compliant(
    records: Iterable[dict],
    log: Callable[[str], None] | None = None,
) -> tuple[list[dict], dict]:
    """Split records into (compliant, summary), logging every skip.

    `summary` = {seen, emitted, skipped, skipped_ids: [(object_id, reason)]}.
    Non-compliant objects are dropped (never repaired/fabricated here) and, when
    `log` is provided, reported as "SKIP <object_id>: <reason>".
    """
    kept: list[dict] = []
    skipped_ids: list[tuple[str, str]] = []
    seen = 0
    for rec in records:
        seen += 1
        ok, reason = is_assembly_complete(rec)
        if ok:
            kept.append(rec)
        else:
            oid = _object_id(rec)
            skipped_ids.append((oid, reason))
            if log is not None:
                log(f"SKIP {oid}: {reason}")
    summary = {
        "seen": seen,
        "emitted": len(kept),
        "skipped": len(skipped_ids),
        "skipped_ids": skipped_ids,
    }
    return kept, summary


def coverage_summary_lines(summary: dict) -> list[str]:
    """Format a coverage summary for printing at end of generation."""
    lines = [
        "=== Assembly-instruction coverage ===",
        f"  objects seen:    {summary['seen']}",
        f"  emitted:         {summary['emitted']}",
        f"  skipped:         {summary['skipped']}",
    ]
    if summary["skipped_ids"]:
        lines.append("  skipped object_ids (regenerate these):")
        for oid, reason in summary["skipped_ids"]:
            lines.append(f"    - {oid}: {reason}")
    return lines
