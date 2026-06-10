"""Validator for the canonical CLAUDE.md schema.

================================ OVERVIEW ====================
This file is the QUALITY INSPECTOR of the pipeline ("Stage 2"). Given one
record (already in canonical shape), it answers: "is this record actually
correct, complete, and internally consistent?" It does NOT change the record —
it only reports problems.

It checks four layers, from cheapest to most semantic:
  1. SCHEMA   — does the record have all required sections/fields, of the right
                JSON types? (handled by the `jsonschema` library)
  2. ENUMS    — do `type`, `category`, `relation`, `phase` values come from the
                approved vocabularies, not made-up words?
  3. REFERENCES — does every id a relationship/step/etc. points at actually
                exist as a component? (catches "dangling references")
  4. SEMANTIC — softer engineering sanity (electrical parts should have wiring,
                3D-printed parts should have print settings, costs ≥ 0, …)

Every problem is reported as an "issue" dict, the same format normalize.py uses:
  {"severity": "error"|"warn", "code": str, "message": str, "refs": [ids]}
"error" issues mean the record is invalid; "warn" issues are advisory.

Two public entry points:
  - `validate_normalized(record)` → the full list of issue dicts
  - `is_valid(record)` → just True/False (True when there are zero errors)

Where it's used: Stage 3 runs this on every generated variant. A positive
variant that fails is thrown away; an "evaluation negative" is SUPPOSED to fail
in one specific way, and the matching issue is stored inside its own record.
============================================================================
"""
from __future__ import annotations
import re
from typing import Any
# `jsonschema` is a third-party library that validates a Python object against
# a "JSON Schema" (a formal description of the required structure). We use it so
# we don't have to hand-write every structural check.
from jsonschema import Draft202012Validator

# --- controlled vocabularies (from CLAUDE.md) ------------------------------
# These `set`s are the ONLY values allowed for each enumerated field. A `set`
# (curly braces, no key:value pairs) gives instant "is x in here?" membership
# tests. Anything outside these sets is flagged as a controlled-vocab violation.

COMPONENT_TYPES = {
    "3d_printed", "machined", "laser_cut", "electronic",
    "fastener", "mechanical", "consumable", "misc",
}

COMPONENT_CATEGORIES = {
    "mechanical", "electrical", "structural", "control",
    "interface", "power", "mounting", "safety",
}

RELATION_TYPES = {
    "attached_to", "secured_by", "fastens_into", "rotates_on",
    "supported_by", "routed_around", "connects_to", "mounted_on",
    "contains", "positions",
}

INSTRUCTION_PHASES = {
    "fabrication", "assembly", "wiring", "bring_up", "testing",
}

SKILL_LEVELS = {"beginner", "intermediate", "advanced", "unknown"}

VARIANT_TYPES = {
    "seed", "prompt_rewrite", "positive_variant", "evaluation_negative",
}

# Pattern an id must fully match to be valid snake_case: start (^) to end ($),
# only lowercase letters, digits, and underscores in between.
_SNAKE_RE = re.compile(r"^[a-z0-9_]+$")


# --- top-level structural schema (jsonschema) -----------------------------
# This big nested dict IS the formal contract for a canonical record, written
# in the JSON Schema language. "required" lists fields that must be present;
# "type" constrains the JSON type; "pattern" applies a regex; "minItems"/
# "minLength"/"minimum" set lower bounds. `additionalProperties: True` means
# extra, unlisted keys are tolerated. The jsonschema library reads this and
# reports any place the record violates it.

CANONICAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "project", "requirements", "components", "relationships",
        "fabrication", "instructions", "sourcing", "validation",
    ],
    "properties": {
        "project": {
            "type": "object",
            "required": [
                "project_id", "name", "category", "summary",
                "original_prompt", "variant_type", "seed_project_id",
            ],
            "properties": {
                "project_id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                "name": {"type": "string", "minLength": 2},
                "category": {"type": "string"},
                "summary": {"type": "string"},
                "original_prompt": {"type": "string"},
                "variant_type": {"type": "string"},
                "seed_project_id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
            },
        },
        "requirements": {
            "type": "object",
            "required": ["tools", "assumptions", "skill_level",
                         "safety_notes", "constraints"],
            "properties": {
                "tools": {"type": "array", "items": {"type": "string"}},
                "assumptions": {"type": "array", "items": {"type": "string"}},
                "skill_level": {"type": "string"},
                "safety_notes": {"type": "array", "items": {"type": "string"}},
                "constraints": {"type": "array", "items": {"type": "string"}},
            },
        },
        "components": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "component_id", "display_name", "category", "type",
                    "material", "quantity", "description", "dimensions",
                    "functional_role", "fabrication_ref", "sourcing_ref",
                ],
                "properties": {
                    "component_id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                    "display_name": {"type": "string", "minLength": 1},
                    "category": {"type": "string"},
                    "type": {"type": "string"},
                    "material": {"type": "string"},
                    "quantity": {"type": "number", "minimum": 0},
                    "description": {"type": "string"},
                    "dimensions": {"type": "object"},
                    "functional_role": {"type": "string"},
                    "fabrication_ref": {"type": ["string", "null"]},
                    "sourcing_ref": {"type": ["string", "null"]},
                },
                "additionalProperties": True,
            },
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "relation", "target", "required", "notes"],
                "properties": {
                    "source": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                    "relation": {"type": "string"},
                    "target": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                    "required": {"type": "boolean"},
                    "notes": {"type": "string"},
                },
                "additionalProperties": True,
            },
        },
        "fabrication": {
            "type": "object",
            "required": ["processes", "component_settings",
                         "post_processing", "tolerances"],
            "properties": {
                "processes": {"type": "array", "items": {"type": "string"}},
                "component_settings": {"type": "object"},
                "post_processing": {"type": "array"},
                "tolerances": {"type": "object"},
            },
        },
        "instructions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["step_id", "phase", "title",
                             "component_ids", "dependencies", "expected_result"],
                "properties": {
                    "step_id": {"type": "string"},
                    "phase": {"type": "string"},
                    "title": {"type": "string", "minLength": 1},
                    "component_ids": {"type": "array", "items": {"type": "string"}},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "expected_result": {"type": "string"},
                },
                "additionalProperties": True,
            },
        },
        "sourcing": {
            "type": "object",
            "required": ["items", "cost_summary", "vendors"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["component_id", "quantity", "unit_cost_usd",
                                     "total_cost_usd"],
                        "properties": {
                            "component_id": {"type": "string"},
                            "quantity": {"type": "number", "minimum": 0},
                            "unit_cost_usd": {"type": "number", "minimum": 0},
                            "total_cost_usd": {"type": "number", "minimum": 0},
                        },
                        "additionalProperties": True,
                    },
                },
                "cost_summary": {"type": "object"},
                "vendors": {"type": "array"},
            },
        },
        "validation": {
            "type": "object",
            "required": [
                "schema_valid", "reference_integrity_valid",
                "manufacturability_valid", "naming_consistency_valid",
                "issues", "confidence_score",
            ],
            "properties": {
                "schema_valid": {"type": "boolean"},
                "reference_integrity_valid": {"type": "boolean"},
                "manufacturability_valid": {"type": "boolean"},
                "naming_consistency_valid": {"type": "boolean"},
                "issues": {"type": "array"},
                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
            },
        },
    },
    "additionalProperties": True,
}

# Build the validator object once from the schema (reused for every record).
_validator = Draft202012Validator(CANONICAL_SCHEMA)


def _issue(severity: str, code: str, message: str, refs: list | None = None) -> dict:
    """Tiny factory that builds one issue dict in the standard shape.

    `refs or []` means: use the given refs list, or an empty list if refs is
    None — guaranteeing the field is always a list.
    """
    return {"severity": severity, "code": code, "message": message, "refs": refs or []}


def _validate_schema(record: dict) -> list[dict]:
    """Layer 1: structural validation via the jsonschema library.

    `iter_errors` yields one error per schema violation. We turn each into our
    own issue format, building a readable path like "components/0/quantity" that
    points at exactly where the problem is.
    """
    issues: list[dict] = []
    for err in _validator.iter_errors(record):
        # `err.absolute_path` is the location of the error as a sequence of keys
        # /indexes; join them with "/" for a human-readable breadcrumb.
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        issues.append(_issue("error", "schema_violation",
                             f"{path}: {err.message}", [path]))
    return issues


def _validate_enums(record: dict) -> list[dict]:
    """Layer 2: every enumerated field must use an approved vocabulary value."""
    issues: list[dict] = []

    # variant_type tells the pipeline what KIND of record this is; it must be
    # one of the four known kinds. `{vt!r}` prints the value with quotes (repr).
    vt = record["project"].get("variant_type")
    if vt not in VARIANT_TYPES:
        issues.append(_issue("error", "invalid_variant_type",
                             f"project.variant_type {vt!r} not in {sorted(VARIANT_TYPES)}",
                             [vt]))

    # skill_level is only advisory, so an unknown value is a warning, not error.
    sl = record["requirements"].get("skill_level")
    if sl not in SKILL_LEVELS:
        issues.append(_issue("warn", "invalid_skill_level",
                             f"requirements.skill_level {sl!r} not in {sorted(SKILL_LEVELS)}",
                             [sl]))

    # Check every component's type and category against the allowed vocab.
    for c in record["components"]:
        if c["type"] not in COMPONENT_TYPES:
            issues.append(_issue("error", "invalid_component_type",
                                 f"component {c['component_id']!r}: type {c['type']!r} "
                                 f"not in controlled vocab",
                                 [c["component_id"]]))
        if c["category"] not in COMPONENT_CATEGORIES:
            issues.append(_issue("error", "invalid_component_category",
                                 f"component {c['component_id']!r}: category {c['category']!r} "
                                 f"not in controlled vocab",
                                 [c["component_id"]]))

    # `enumerate` gives both the index `i` and the item `r`, so error messages
    # can say exactly which relationship (e.g. "relationships[3]") is bad.
    for i, r in enumerate(record["relationships"]):
        if r["relation"] not in RELATION_TYPES:
            issues.append(_issue("error", "invalid_relation",
                                 f"relationships[{i}].relation {r['relation']!r} "
                                 f"not in controlled vocab",
                                 [r.get("source"), r.get("target")]))

    for i, step in enumerate(record["instructions"]):
        if step["phase"] not in INSTRUCTION_PHASES:
            issues.append(_issue("error", "invalid_phase",
                                 f"instructions[{i}].phase {step['phase']!r} "
                                 f"not in controlled vocab",
                                 [step.get("step_id")]))

    return issues


def _validate_references(record: dict) -> list[dict]:
    """Layer 3: every id that one section points at must exist somewhere valid.

    This is the most important integrity check. The whole record is a graph of
    cross-references — relationships point at components, steps point at
    components and at earlier steps, sourcing/fabrication point at components.
    A pointer to a non-existent id is a "dangling reference" and makes the
    record unusable for training, so all of these are ERRORS.
    """
    issues: list[dict] = []
    # Collect every real component id ONCE into a set for fast membership tests.
    # (`{expr for x in ...}` is a "set comprehension".)
    component_ids = {c["component_id"] for c in record["components"]}
    step_ids: list[str] = []
    seen_step_ids: set[str] = set()

    # 3a. Component ids must be valid snake_case.
    for i, c in enumerate(record["components"]):
        cid = c["component_id"]
        if not _SNAKE_RE.match(cid):
            issues.append(_issue("error", "invalid_id_format",
                                 f"components[{i}].component_id {cid!r} not snake_case",
                                 [cid]))

    # 3b. No two components may share an id.
    seen_cids: set[str] = set()
    for c in record["components"]:
        if c["component_id"] in seen_cids:
            issues.append(_issue("error", "duplicate_component_id",
                                 f"duplicate component_id {c['component_id']!r}",
                                 [c["component_id"]]))
        seen_cids.add(c["component_id"])

    # 3c. Both ends of every relationship must be real components.
    for i, r in enumerate(record["relationships"]):
        if r["source"] not in component_ids:
            issues.append(_issue("error", "dangling_ref",
                                 f"relationships[{i}].source {r['source']!r} not in components",
                                 [r["source"]]))
        if r["target"] not in component_ids:
            issues.append(_issue("error", "dangling_ref",
                                 f"relationships[{i}].target {r['target']!r} not in components",
                                 [r["target"]]))

    # 3d. Step ids must be unique, and every part a step references must exist.
    for i, step in enumerate(record["instructions"]):
        sid = step["step_id"]
        if sid in seen_step_ids:
            issues.append(_issue("error", "duplicate_step_id",
                                 f"duplicate step_id {sid!r}", [sid]))
        seen_step_ids.add(sid)
        step_ids.append(sid)

        for cid in step.get("component_ids", []):
            if cid not in component_ids:
                issues.append(_issue("error", "dangling_step_ref",
                                     f"instruction {sid!r} references missing component {cid!r}",
                                     [cid]))

    # 3e. A step's dependencies must point to steps that come BEFORE it. We walk
    # steps in order tracking `seen_so_far`; depending on a not-yet-seen step is
    # either "missing" (no such step at all) or "forward" (exists but later) —
    # both break the build order (a directed acyclic graph, "DAG").
    seen_so_far: set[str] = set()
    for step in record["instructions"]:
        for dep in step.get("dependencies", []):
            if dep not in seen_so_far and dep not in step_ids:
                issues.append(_issue("error", "missing_dependency",
                                     f"step {step['step_id']!r} depends on missing step {dep!r}",
                                     [dep]))
            elif dep not in seen_so_far:
                issues.append(_issue("error", "forward_dependency",
                                     f"step {step['step_id']!r} depends on later step {dep!r}",
                                     [dep]))
        seen_so_far.add(step["step_id"])

    # 3f. Every sourcing line item must reference a real component.
    for i, item in enumerate(record["sourcing"]["items"]):
        if item["component_id"] not in component_ids:
            issues.append(_issue("error", "dangling_sourcing_ref",
                                 f"sourcing.items[{i}].component_id {item['component_id']!r} "
                                 f"not in components",
                                 [item["component_id"]]))

    # 3g. Every fabrication settings entry must reference a real component.
    for cid in record["fabrication"]["component_settings"]:
        if cid not in component_ids:
            issues.append(_issue("error", "dangling_fabrication_ref",
                                 f"fabrication.component_settings[{cid!r}] not in components",
                                 [cid]))

    return issues


def _validate_semantic(record: dict, strict: bool) -> list[dict]:
    """Layer 4: softer engineering-sense checks.

    Unlike the earlier layers, these are judgement calls about whether the
    project makes practical sense. The `strict` flag controls how harsh to be:
    when True, the most important of these are ERRORS; when False they downgrade
    to WARNINGS. `"error" if strict else "warn"` picks the severity inline.
    """
    issues: list[dict] = []

    variant_type = record["project"].get("variant_type")

    # Instructions present (allowed empty only for explicit dataset-mode variants).
    if not record["instructions"] and variant_type != "evaluation_negative":
        issues.append(_issue("error" if strict else "warn",
                             "empty_instructions",
                             "no instruction steps; project not buildable as-is",
                             []))

    # A project with multiple electrical parts but no electrical wiring is
    # almost always a generation/parse failure (e.g. connection keys dropped).
    # Evaluation negatives are exempt — they may intentionally omit wiring.
    if variant_type != "evaluation_negative":
        n_electrical = sum(1 for c in record["components"]
                           if c.get("category") == "electrical")
        has_electrical_link = any(
            r.get("relation") == "connects_to"
            for r in record["relationships"]
        )
        if n_electrical >= 2 and not has_electrical_link:
            issues.append(_issue("error" if strict else "warn",
                                 "missing_electrical_connections",
                                 f"{n_electrical} electrical components but no "
                                 f"connects_to relationships",
                                 []))

    # 3D-printed parts ought to carry print settings (advisory only → warn).
    settings = record["fabrication"]["component_settings"]
    for c in record["components"]:
        if c["type"] == "3d_printed" and c["component_id"] not in settings:
            issues.append(_issue("warn", "missing_print_settings",
                                 f"3d_printed component {c['component_id']!r} has no fabrication settings",
                                 [c["component_id"]]))

    # A negative total cost is impossible — always an error.
    if record["sourcing"]["cost_summary"].get("total_usd", 0) < 0:
        issues.append(_issue("error", "negative_cost",
                             "sourcing.cost_summary.total_usd is negative", []))

    # Count how often each display_name appears; flag any reused name (it makes
    # the build instructions ambiguous about which part is meant).
    name_counts: dict[str, int] = {}
    for c in record["components"]:
        name_counts[c["display_name"]] = name_counts.get(c["display_name"], 0) + 1
    for name, count in name_counts.items():
        if count > 1:
            issues.append(_issue("warn", "duplicate_display_name",
                                 f"display_name {name!r} used by {count} components", [name]))

    return issues


def validate_normalized(record: dict, strict: bool = True) -> list[dict]:
    """PUBLIC ENTRY POINT: run all four layers and return every issue found.

    Layers run cheapest-first. If the schema layer already fails, we stop early
    and return just those issues — the deeper checks assume a well-formed record
    and would crash (e.g. by indexing a missing field) on broken structure.
    `.extend(...)` appends all of another list's items onto `issues`.
    """
    issues = _validate_schema(record)
    if issues:
        # No point running deeper checks on a structurally invalid record.
        return issues

    issues.extend(_validate_enums(record))
    issues.extend(_validate_references(record))
    issues.extend(_validate_semantic(record, strict))
    return issues


def is_valid(record: dict, strict: bool = True) -> bool:
    """Convenience wrapper: True only if the record has ZERO error-level issues.

    Warnings are ignored here — a record can have warnings and still be "valid".
    """
    return not any(i["severity"] == "error" for i in validate_normalized(record, strict))
