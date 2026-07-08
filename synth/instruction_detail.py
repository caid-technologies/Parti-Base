"""LLM generation of detailed assembly-instruction bodies for normalized records.

============================ WHAT THIS DOES ================================
Most source projects ship instruction steps that are bare titles with no body,
so the assembly-completeness gate (synth/assembly_check.py) rightly skips them.
This module fills that gap: for each step that is NOT already complete, it asks
the local LLM (Ollama) to write a real `{summary, steps[], tip}` detail body,
grounded in the project's actual components and the step's title/phase.

Design choices, consistent with phase_variants.py:
  - One tightly-schema-constrained `chat_json` call PER STEP — small, reliable
    output, the same trick that makes prompt-rewrites robust.
  - We never invent parts: the prompt is grounded in the step's real
    component_ids and the project context, and told not to introduce new parts.
  - A failed/garbage call leaves the step untouched (still bodyless) so the gate
    skips it rather than letting fabricated junk through. Nothing is forced.
============================================================================
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .assembly_check import step_is_complete
from .denormalize import _dims_to_string
from .ollama_client import chat_json

# Strict output shape for one step's detail. Mirrors the source `detail` shape
# ({summary, steps, tip}) the normalizer/denormalizer already understand.
DETAIL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["summary", "steps"],
    "properties": {
        "summary": {"type": "string", "minLength": 20, "maxLength": 600},
        "steps": {
            "type": "array",
            "minItems": 3,
            "maxItems": 12,
            "items": {"type": "string", "minLength": 15, "maxLength": 500},
        },
        "tip": {"type": "string", "maxLength": 500},
    },
    "additionalProperties": False,
}

_SYSTEM = (
    "You write clear, accurate, detailed assembly instructions for hobbyist "
    "hardware projects. You are precise and practical. You never invent parts "
    "that were not provided. Return only the JSON object requested."
)


def _parts_context(step: dict, comp_index: dict[str, dict]) -> str:
    """Human-readable description of the parts this step touches."""
    lines: list[str] = []
    for cid in step.get("component_ids", []):
        c = comp_index.get(cid)
        if not c:
            continue
        dims = _dims_to_string(c.get("dimensions")) or "unknown size"
        mat = c.get("material") or "unknown"
        lines.append(
            f"- {c['display_name']} (type={c['type']}, material={mat}, "
            f"size={dims}, role={c.get('functional_role', 'unknown')})"
        )
    return "\n".join(lines) if lines else "- (no specific parts listed for this step)"


def generate_step_detail(
    rec: dict, step: dict, comp_index: dict[str, dict]
) -> dict | None:
    """Ask the LLM for one step's detail body. Returns the dict, or None on failure."""
    proj = rec.get("project", {})
    req = rec.get("requirements", {})
    user = (
        f"Project: {proj.get('name', '')}\n"
        f"Summary: {proj.get('summary', '')}\n"
        f"Skill level: {req.get('skill_level', 'intermediate')}\n\n"
        f"Build phase: {step.get('phase', '')}\n"
        f"Step: {step.get('title', '')}\n"
        f"Parts involved in this step:\n{_parts_context(step, comp_index)}\n\n"
        "Write detailed, do-this-then-that instructions for THIS step only. "
        "Return JSON of the form "
        '{"summary": "...", "steps": ["...", "...", "..."], "tip": "..."} where:\n'
        "  - summary: 1-2 sentences on what this step accomplishes\n"
        "  - steps: 3-12 concrete ordered actions a builder physically performs\n"
        "  - tip: one practical caution or best-practice note\n"
        "Only reference the parts listed above; do not introduce new components."
    )
    try:
        result = chat_json(
            [{"role": "system", "content": _SYSTEM},
             {"role": "user", "content": user}],
            schema=DETAIL_SCHEMA,
            temperature=0.4,
            max_tokens=1500,
        )
    except Exception as e:  # noqa: BLE001 — one flaky call must not abort the run
        print(f"    [detail] step {step.get('step_id')!r} failed: {e}")
        return None

    # Defensive: keep only the fields we expect, ensure steps are non-empty.
    if not isinstance(result, dict):
        return None
    steps = [str(s).strip() for s in (result.get("steps") or []) if str(s).strip()]
    if not steps:
        return None
    detail: dict[str, Any] = {"summary": str(result.get("summary", "")).strip(),
                              "steps": steps}
    tip = result.get("tip")
    if tip and str(tip).strip():
        detail["tip"] = str(tip).strip()
    return detail


def enrich_record(
    rec: dict,
    force: bool = False,
    log: Callable[[str], None] = print,
) -> dict:
    """Fill in missing step detail on one record, in place.

    For every step that is not already complete (or all steps, if `force`), call
    the LLM and attach the generated `detail`. Returns per-record stats. Steps
    that fail generation are left untouched.
    """
    comp_index = {c["component_id"]: c for c in rec.get("components", [])}
    stats = {"steps_total": 0, "generated": 0, "already_ok": 0, "failed": 0}
    for step in rec.get("instructions", []):
        stats["steps_total"] += 1
        ok, _ = step_is_complete(step)
        if ok and not force:
            stats["already_ok"] += 1
            continue
        detail = generate_step_detail(rec, step, comp_index)
        if detail is None:
            stats["failed"] += 1
            continue
        step["detail"] = detail
        stats["generated"] += 1
    return stats
