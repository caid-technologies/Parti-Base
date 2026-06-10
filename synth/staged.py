"""Stage 4: derive Mode A–F ChatML rows from canonical-schema records.

================================ OVERVIEW ====================
This file turns clean project records into actual TRAINING EXAMPLES. The end
goal of the whole project is to fine-tune a language model, and a model learns
from (input, desired-output) pairs. This file produces those pairs.

The trick: from ONE project record we can derive SIX different tasks ("modes"),
each teaching the model a different skill. Every mode is just a different
"view" or "slice" of the same record:

  A  Normalize          — plain-English prompt → the full canonical record
  B  Prompt→Project     — like A, framed as "design this project for me"
  C  Prompt→Components  — prompt → just the components list
  D  Components→Relationships — a components table → just the relationship graph
  E  Project→Instructions — project+components+relationships → the build steps
  F  Project→Validation — a record with validation blanked → the validation block

No AI is used here — it's pure rearranging of data ("projection"). Each mode
becomes a (system prompt, user message, assistant reply) triple. The model
learns which task it's doing from the system prompt plus the shape of the input.
============================================================================
"""
from __future__ import annotations
import json
from collections.abc import Iterator

# --- per-mode task system prompts -----------------------------------------
# The "system prompt" is the instruction the model always sees first; it tells
# the model which of the six jobs it's performing and exactly what output shape
# to return. There's one fixed system prompt per mode, stored in this dict.

MODE_SYSTEM_PROMPTS: dict[str, str] = {
    "A": (
        "Mode A — Normalize. You receive a free-text description of a hobbyist "
        "hardware project. Produce a single JSON object conforming to the "
        "canonical project schema: top-level fields `project`, `requirements`, "
        "`components`, `relationships`, `fabrication`, `instructions`, "
        "`sourcing`, `validation`. Use snake_case component ids. Output only "
        "the JSON object."
    ),
    "B": (
        "Mode B — Prompt→Project. You design hobbyist electronics and "
        "manufacturing projects. Given a user request, respond with a single "
        "JSON object describing the complete project: project metadata, "
        "components, relationships, fabrication, instructions, sourcing, and "
        "a validation block. All `source`/`target`/`component_ids` references "
        "must point to component ids you actually define. Output only the JSON "
        "object."
    ),
    "C": (
        "Mode C — Prompt→Components. Given a user request for a hobbyist "
        "hardware project, respond with only the components list, as JSON of "
        "the form `{\"components\": [...]}`. Each component must include "
        "component_id (snake_case), display_name, category, type, material, "
        "quantity, description, dimensions, functional_role, fabrication_ref, "
        "and sourcing_ref."
    ),
    "D": (
        "Mode D — Components→Relationships. Given a project's components "
        "list, produce the relationship graph as JSON of the form "
        "`{\"relationships\": [...]}`. Every `source` and `target` must equal "
        "a `component_id` from the input. Use only these relation values: "
        "attached_to, secured_by, fastens_into, rotates_on, supported_by, "
        "routed_around, connects_to, mounted_on, contains, positions."
    ),
    "E": (
        "Mode E — Project→Instructions. Given a project's metadata, "
        "components, and relationships, produce the ordered build instructions "
        "as JSON of the form `{\"instructions\": [...]}`. Each step has "
        "step_id, phase (fabrication/assembly/wiring/bring_up/testing), title, "
        "component_ids (referencing the input components), dependencies "
        "(referencing earlier step_ids), and expected_result. Order steps so "
        "dependencies precede dependents."
    ),
    "F": (
        "Mode F — Project→Validation. You audit hobbyist hardware project "
        "records. Given a complete record with its `validation` block blanked, "
        "produce the validation block as JSON: schema_valid, "
        "reference_integrity_valid, manufacturability_valid, "
        "naming_consistency_valid, issues (array of "
        "{severity, code, message, refs}), and confidence_score (0.0–1.0). "
        "Flag dangling references, controlled-vocab violations, missing "
        "instructions, and naming conflicts."
    ),
}


def _dumps(obj) -> str:
    """Convert a Python object to a pretty-printed JSON string.

    `ensure_ascii=False` keeps non-English characters readable instead of
    escaping them; `indent=2` makes the JSON nicely formatted. We pass JSON
    text (not Python objects) as the training input/output because that's what
    the model reads and writes.
    """
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _components_table(components: list[dict]) -> str:
    """Compact component summary for Mode D's user-turn input."""
    rows = [
        {
            "component_id": c["component_id"],
            "display_name": c["display_name"],
            "category": c["category"],
            "type": c["type"],
            "quantity": c["quantity"],
        }
        for c in components
    ]
    return _dumps({"components": rows})


def _blank_validation() -> dict:
    return {
        "schema_valid": None,
        "reference_integrity_valid": None,
        "manufacturability_valid": None,
        "naming_consistency_valid": None,
        "issues": [],
        "confidence_score": None,
    }


# --- mode generators -------------------------------------------------------
# One function per mode. Each takes a normalized record and returns a
# (user_turn, assistant_turn) pair — the input and the desired output for that
# training example. Returning `None` means "this record can't make this kind of
# example" (its "source filter" failed — e.g. no prompt text, no instructions),
# so that record is simply skipped for that mode.


def _get_prompt(rec: dict) -> str:
    """Safely pull the project's original prompt text out of a record.

    The chained `(rec.get("project") or {})` avoids a crash if "project" is
    missing: `.get` returns None, `None or {}` becomes an empty dict, and
    `.get("original_prompt", "")` then returns "" rather than erroring.
    """
    return (rec.get("project") or {}).get("original_prompt", "").strip()


def _mode_a(rec: dict) -> tuple[str, str] | None:
    # Mode A: input is the prompt wrapped in a "normalize this" instruction;
    # output is the ENTIRE record. Skip records that have no prompt.
    prompt = _get_prompt(rec)
    if not prompt:
        return None
    user = (
        "Normalize the following hobbyist hardware project into the canonical "
        "schema.\n\nProject description:\n" + prompt
    )
    return user, _dumps(rec)


def _mode_b(rec: dict) -> tuple[str, str] | None:
    # Mode B: input is the bare prompt; output is the entire record. Same output
    # as A but a more natural "build me this" framing.
    prompt = _get_prompt(rec)
    if not prompt:
        return None
    return prompt, _dumps(rec)


def _mode_c(rec: dict) -> tuple[str, str] | None:
    # Mode C: prompt → only the components list. Needs both a prompt AND
    # components to be a usable example.
    prompt = _get_prompt(rec)
    if not prompt or not rec.get("components"):
        return None
    return prompt, _dumps({"components": rec["components"]})


def _mode_d(rec: dict) -> tuple[str, str] | None:
    # Mode D: a components table → the relationship graph. Teaches the model to
    # figure out how parts connect given only the parts list.
    if not rec.get("relationships") or not rec.get("components"):
        return None
    user = (
        "Given the following components, produce the relationship graph.\n\n"
        + _components_table(rec["components"])
    )
    return user, _dumps({"relationships": rec["relationships"]})


def _mode_e(rec: dict) -> tuple[str, str] | None:
    # Mode E: project + components + relationships → the ordered build steps.
    # The input deliberately omits the instructions so the model must produce them.
    if not rec.get("instructions"):
        return None
    user = _dumps({
        "project": rec.get("project") or {},
        "components": rec.get("components") or [],
        "relationships": rec.get("relationships") or [],
    })
    return user, _dumps({"instructions": rec["instructions"]})


def _mode_f(rec: dict) -> tuple[str, str] | None:
    # Mode F: a full record with its validation block wiped → the real
    # validation block. Teaches the model to audit a project for problems.
    if not isinstance(rec.get("validation"), dict):
        return None
    # `dict(rec)` makes a shallow copy so blanking validation doesn't mutate the
    # original record that other modes still need intact.
    blanked = dict(rec)
    blanked["validation"] = _blank_validation()
    return _dumps(blanked), _dumps(rec["validation"])


# This dict maps each mode letter to its generator function. Storing functions
# in a dict lets the loop below call the right one by name (mode letter).
MODE_GENERATORS = {
    "A": _mode_a,
    "B": _mode_b,
    "C": _mode_c,
    "D": _mode_d,
    "E": _mode_e,
    "F": _mode_f,
}


def iter_rows(
    records: list[dict],
    modes: list[str] | None = None,
) -> Iterator[tuple[str, str, str, str]]:
    """Yield (system_prompt, user_turn, assistant_turn, mode) per record × mode.

    Records that fail a mode's source filter (e.g. no instructions for Mode E)
    are skipped for that mode only.
    """
    # If no modes given, use all of them. This is the "main loop" of Stage 4:
    # for every record, try every requested mode and emit each example that works.
    modes = modes or list(MODE_GENERATORS.keys())
    for rec in records:
        for mode in modes:
            result = MODE_GENERATORS[mode](rec)  # call this mode's generator
            if result is None:
                continue  # record didn't qualify for this mode — skip it
            user, asst = result
            # `yield` produces one item at a time (this is a "generator"),
            # so we never hold the whole dataset in memory at once.
            yield MODE_SYSTEM_PROMPTS[mode], user, asst, mode
