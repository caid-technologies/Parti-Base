"""Deterministic seed → variant transforms (no LLM).

================================ OVERVIEW ====================
"Variants" are extra training examples we MANUFACTURE from a clean seed project
so the dataset is bigger and more varied. This file makes two kinds, WITHOUT any
AI (everything is plain Python arithmetic and dictionary edits):

  1. POSITIVE variants — a believable redesign of the same project: smaller
     ("compact"), larger ("standard_size"), cheaper ("low_cost"), fancier
     ("premium_material"), or with extras stripped ("accessory_light"). These
     stay valid by construction — they only tweak numbers, swap materials, or
     drop optional parts, never break the structure.

  2. EVALUATION NEGATIVES — a copy with ONE deliberate defect injected (a
     pointer to a missing part, an illegal type, etc.), used to teach a model
     to RECOGNIZE bad records. The defect is recorded in the record's own
     `validation` block so the "wrongness" is labelled, not hidden.

Why no AI? An earlier attempt asked an LLM to write whole variants, but the
schema is too intricate and the model produced lots of broken output. These
mechanical transforms are instant and provably correct.

The two public functions are `make_positive_variants` and
`make_evaluation_negative` at the bottom; everything above them is helpers.
============================================================================
"""
from __future__ import annotations
# `copy` provides deepcopy — a FULL independent clone of a nested object. We
# clone the seed before editing so the original is never accidentally changed.
import copy
from typing import Callable

from .costs import recompute_cost_summary


# --- positive variant transforms ------------------------------------------
# Every dimension key that holds a plain number we might want to scale.
_SCALAR_DIM_KEYS = ("length_mm", "width_mm", "height_mm",
                    "diameter_mm", "id_mm", "od_mm")


def _scale_dims(dims: dict, factor: float) -> dict:
    """Return a copy of a dimensions dict with every numeric size × factor.

    e.g. factor=0.7 shrinks everything to 70%. Non-numeric keys (like "raw" or
    "thread") are left untouched. `round(..., 2)` keeps two decimal places.
    """
    out = dict(dims)
    for k in _SCALAR_DIM_KEYS:
        if k in out and isinstance(out[k], (int, float)):
            out[k] = round(out[k] * factor, 2)
    return out


def _recompute_costs(rec: dict) -> None:
    """Rebuild the cost totals after a transform changed prices or parts.

    `-> None` means this edits the record in place and returns nothing.
    Transforms change unit costs / quantities / item membership, so per-item
    totals must be refreshed before the summary is rebuilt.
    """
    recompute_cost_summary(rec, refresh_item_totals=True)


def _make_compact(rec: dict) -> dict | None:
    # COMPACT axis: shrink every part to ~70% and drop prices ~15% (smaller =
    # cheaper). `copy.deepcopy` clones first so we never mutate the seed.
    v = copy.deepcopy(rec)
    factor = 0.7
    for c in v["components"]:
        c["dimensions"] = _scale_dims(c["dimensions"], factor)
    for item in v["sourcing"]["items"]:
        item["unit_cost_usd"] = round(item["unit_cost_usd"] * 0.85, 2)
    _recompute_costs(v)
    v["project"]["name"] = f"{v['project']['name']} (Compact)"
    v["project"]["summary"] = (
        "Compact variant: dimensions reduced ~30% for portability. "
        + v["project"].get("summary", "")
    )
    return v


def _make_standard_size(rec: dict) -> dict | None:
    # STANDARD_SIZE axis: the opposite of compact — grow parts ~30% and nudge
    # prices up ~15%.
    v = copy.deepcopy(rec)
    factor = 1.3
    for c in v["components"]:
        c["dimensions"] = _scale_dims(c["dimensions"], factor)
    for item in v["sourcing"]["items"]:
        item["unit_cost_usd"] = round(item["unit_cost_usd"] * 1.15, 2)
    _recompute_costs(v)
    v["project"]["name"] = f"{v['project']['name']} (Standard Size)"
    v["project"]["summary"] = (
        "Standard-size variant: dimensions scaled ~30% larger for capacity. "
        + v["project"].get("summary", "")
    )
    return v


def _make_low_cost(rec: dict) -> dict | None:
    # LOW_COST axis: cut prices to ~65% AND downgrade premium materials to
    # cheaper equivalents (ASA/PETG/PC → PLA, stainless → carbon steel, …).
    v = copy.deepcopy(rec)
    cost_factor = 0.65
    for item in v["sourcing"]["items"]:
        item["unit_cost_usd"] = round(item["unit_cost_usd"] * cost_factor, 2)
    # A lookup table: cheaper substitute for each expensive material.
    swaps = {
        "asa": "pla", "petg": "pla", "pc": "pla",
        "stainless": "carbon_steel", "stainless_steel": "carbon_steel",
        "anodized_aluminum": "aluminum",
    }
    for c in v["components"]:
        mat = (c.get("material") or "").lower()
        if mat in swaps:
            c["material"] = swaps[mat]
    _recompute_costs(v)
    v["project"]["name"] = f"{v['project']['name']} (Budget)"
    v["project"]["summary"] = (
        "Budget variant: cheaper sourcing and basic materials throughout. "
        + v["project"].get("summary", "")
    )
    return v


def _make_premium_material(rec: dict) -> dict | None:
    # PREMIUM_MATERIAL axis: the mirror image of low_cost — upgrade materials,
    # raise prices ~40%, and add finishing steps (sanding, primer).
    v = copy.deepcopy(rec)
    cost_factor = 1.4
    premium_map = {
        "pla": "asa", "abs": "asa", "petg": "pc_blend",
        "carbon_steel": "stainless", "steel": "stainless", "mild_steel": "stainless",
        "nylon": "ptfe", "aluminum": "anodized_aluminum",
    }
    for c in v["components"]:
        mat = (c.get("material") or "").lower()
        if mat in premium_map:
            c["material"] = premium_map[mat]
    for item in v["sourcing"]["items"]:
        item["unit_cost_usd"] = round(item["unit_cost_usd"] * cost_factor, 2)
    _recompute_costs(v)
    v["fabrication"]["post_processing"] = ["sand_180_grit", "primer_coat"]
    v["project"]["name"] = f"{v['project']['name']} (Premium)"
    v["project"]["summary"] = (
        "Premium variant: upgraded materials (ASA, stainless) and post-process finishing. "
        + v["project"].get("summary", "")
    )
    return v


def _drop_components(rec: dict, drop_ids: set[str]) -> None:
    """Remove a set of components and clean up EVERY reference to them.

    This is the careful part: you can't just delete components, or you'd leave
    dangling references (which the validator rejects). So for each section we
    rebuild the list keeping only items that don't touch a dropped id. The
    `[x for x in list if condition]` pattern is a "list comprehension" — it
    builds a new, filtered list. Steps that lose ALL their parts are dropped
    entirely, and we also remove those now-dead step ids from dependencies.
    """
    # Keep only components whose id is NOT in the drop set.
    rec["components"] = [c for c in rec["components"] if c["component_id"] not in drop_ids]
    # Keep only relationships where neither end was dropped.
    rec["relationships"] = [
        r for r in rec["relationships"]
        if r["source"] not in drop_ids and r["target"] not in drop_ids
    ]

    new_steps: list[dict] = []
    dropped_step_ids: set[str] = set()
    for step in rec["instructions"]:
        # Strip dropped parts out of each step's part list and dependency list.
        step["component_ids"] = [
            cid for cid in step["component_ids"] if cid not in drop_ids
        ]
        step["dependencies"] = [
            d for d in step["dependencies"] if d not in dropped_step_ids
        ]
        # A step that now references no parts is meaningless → drop it too.
        if not step["component_ids"]:
            dropped_step_ids.add(step["step_id"])
            continue
        new_steps.append(step)
    rec["instructions"] = new_steps

    # Same filtering for sourcing line items and fabrication settings.
    rec["sourcing"]["items"] = [
        it for it in rec["sourcing"]["items"] if it["component_id"] not in drop_ids
    ]
    rec["fabrication"]["component_settings"] = {
        k: v for k, v in rec["fabrication"]["component_settings"].items()
        if k not in drop_ids
    }
    _recompute_costs(rec)


def _make_accessory_light(rec: dict) -> dict | None:
    # ACCESSORY_LIGHT axis: strip the project down — drop all "misc" extras and
    # keep at most 4 fasteners. Returns None if there's nothing to drop (so we
    # don't emit a "variant" identical to the seed).
    v = copy.deepcopy(rec)
    fasteners_kept = 0
    drop_ids: set[str] = set()
    for c in v["components"]:
        if c["type"] == "fastener":
            if fasteners_kept < 4:
                fasteners_kept += 1   # keep the first 4 fasteners
            else:
                drop_ids.add(c["component_id"])  # drop the rest
        elif c["type"] == "misc":
            drop_ids.add(c["component_id"])

    if not drop_ids:
        return None  # nothing to drop — variant would be identical to seed

    _drop_components(v, drop_ids)
    v["project"]["name"] = f"{v['project']['name']} (Accessory-Light)"
    v["project"]["summary"] = (
        f"Accessory-light variant: {len(drop_ids)} non-essential components removed. "
        + v["project"].get("summary", "")
    )
    return v


# Registry of all positive axes: label → the function that builds that variant.
# `Callable[[dict], dict | None]` is a type hint meaning "a function taking a
# dict and returning a dict or None". The orchestrator looks names up here.
PROGRAMMATIC_POSITIVE_AXES: dict[str, Callable[[dict], dict | None]] = {
    "compact": _make_compact,
    "standard_size": _make_standard_size,
    "low_cost": _make_low_cost,
    "premium_material": _make_premium_material,
    "accessory_light": _make_accessory_light,
}


def _finalize_positive(v: dict, seed_id: str, axis_label: str) -> dict:
    """Stamp the shared bookkeeping fields onto a finished positive variant.

    Every positive transform ends by calling this: it sets the variant_type,
    links the variant back to its seed, gives it a unique id like
    "<seed>__pos_compact", and writes a clean (all-passing) validation block —
    because positive variants are valid by construction.
    """
    v["project"]["variant_type"] = "positive_variant"
    v["project"]["seed_project_id"] = seed_id
    v["project"]["project_id"] = f"{seed_id}__pos_{axis_label}"
    # Design changed → the seed's PNG is no longer accurate.
    v["project"]["visual_ref"] = None
    v["validation"] = {
        "schema_valid": True,
        "reference_integrity_valid": True,
        "manufacturability_valid": True,
        "naming_consistency_valid": True,
        "issues": [],
        "confidence_score": 1.0,
    }
    return v


def make_positive_variants(seed: dict, axis_labels: list[str]) -> list[dict]:
    """PUBLIC: build the requested positive variants for one seed.

    Looks up each axis label, runs its transform, and finalizes the result.
    Transforms that return None (nothing meaningful to change) are skipped, so
    the output list may be shorter than `axis_labels`.
    """
    seed_id = seed["project"]["project_id"]
    out: list[dict] = []
    for label in axis_labels:
        fn = PROGRAMMATIC_POSITIVE_AXES.get(label)
        if fn is None:
            continue   # unknown axis name — ignore it
        v = fn(seed)
        if v is None:
            continue   # transform didn't apply (e.g. nothing to drop)
        out.append(_finalize_positive(v, seed_id, label))
    return out


# --- evaluation negative injectors ----------------------------------------
# Each `_inject_*` takes a CLEAN seed and returns a copy with exactly ONE defect
# plus a validation block that HONESTLY DESCRIBES that defect. The pattern is
# identical every time: deepcopy, break one thing, write the matching issue.

def _inject_dangling_ref(rec: dict) -> dict | None:
    # DEFECT: point a relationship at a part that doesn't exist.
    v = copy.deepcopy(rec)
    if not v["relationships"]:
        return None   # can't inject this defect with no relationships
    phantom = "phantom_part_xyz"   # an id guaranteed not to be a real component
    v["relationships"][0]["target"] = phantom
    v["validation"] = {
        "schema_valid": True,
        "reference_integrity_valid": False,
        "manufacturability_valid": True,
        "naming_consistency_valid": True,
        "issues": [{
            "severity": "error",
            "code": "dangling_ref",
            "message": f"relationships[0].target {phantom!r} not in components",
            "refs": [phantom],
        }],
        "confidence_score": 0.2,
    }
    return v


def _inject_invalid_component_type(rec: dict) -> dict | None:
    # DEFECT: set a component's type to a word not in the controlled vocab.
    v = copy.deepcopy(rec)
    if not v["components"]:
        return None
    cid = v["components"][0]["component_id"]
    v["components"][0]["type"] = "gadget"   # "gadget" is not an allowed type
    v["validation"] = {
        "schema_valid": True,
        "reference_integrity_valid": True,
        "manufacturability_valid": True,
        "naming_consistency_valid": True,
        "issues": [{
            "severity": "error",
            "code": "invalid_component_type",
            "message": f"component {cid!r}: type 'gadget' not in controlled vocab",
            "refs": [cid],
        }],
        "confidence_score": 0.2,
    }
    return v


def _inject_invalid_relation(rec: dict) -> dict | None:
    # DEFECT: use a relation word not in the controlled vocab.
    v = copy.deepcopy(rec)
    if not v["relationships"]:
        return None
    v["relationships"][0]["relation"] = "stuck_to"   # not an allowed relation
    v["validation"] = {
        "schema_valid": True,
        "reference_integrity_valid": True,
        "manufacturability_valid": True,
        "naming_consistency_valid": True,
        "issues": [{
            "severity": "error",
            "code": "invalid_relation",
            "message": "relationships[0].relation 'stuck_to' not in controlled vocab",
            "refs": [v["relationships"][0]["source"], v["relationships"][0]["target"]],
        }],
        "confidence_score": 0.2,
    }
    return v


def _inject_dangling_step_ref(rec: dict) -> dict | None:
    # DEFECT: make a build step reference a part that doesn't exist.
    v = copy.deepcopy(rec)
    if not v["instructions"]:
        return None
    sid = v["instructions"][0]["step_id"]
    v["instructions"][0]["component_ids"].append("phantom_part_xyz")
    v["validation"] = {
        "schema_valid": True,
        "reference_integrity_valid": False,
        "manufacturability_valid": True,
        "naming_consistency_valid": True,
        "issues": [{
            "severity": "error",
            "code": "dangling_step_ref",
            "message": f"instruction {sid!r} references missing component 'phantom_part_xyz'",
            "refs": ["phantom_part_xyz"],
        }],
        "confidence_score": 0.2,
    }
    return v


# NOTE: a `negative_cost` injector was removed — the canonical schema enforces
# `minimum: 0` on cost fields, so a negative value surfaces as a generic
# `schema_violation` rather than a clean `negative_cost` issue, which made it
# useless as a labelled training negative.


# Registry of all defect injectors: defect code → the function that injects it.
PROGRAMMATIC_NEGATIVE_DEFECTS: dict[str, Callable[[dict], dict | None]] = {
    "dangling_ref": _inject_dangling_ref,
    "invalid_component_type": _inject_invalid_component_type,
    "invalid_relation": _inject_invalid_relation,
    "dangling_step_ref": _inject_dangling_step_ref,
}


def make_evaluation_negative(seed: dict, defect_code: str) -> dict | None:
    """PUBLIC: build one evaluation-negative variant with the named defect.

    Returns None if the defect can't be injected into this seed (e.g. asking for
    a dangling relationship when the seed has no relationships). Otherwise stamps
    the bookkeeping fields and a unique "<seed>__neg_<defect>" id.
    """
    fn = PROGRAMMATIC_NEGATIVE_DEFECTS.get(defect_code)
    if fn is None:
        return None   # unknown defect code
    v = fn(seed)
    if v is None:
        return None   # this seed can't host this defect
    seed_id = seed["project"]["project_id"]
    v["project"]["variant_type"] = "evaluation_negative"
    v["project"]["seed_project_id"] = seed_id
    v["project"]["project_id"] = f"{seed_id}__neg_{defect_code}"
    # Design intentionally flawed → no honest visual reference.
    v["project"]["visual_ref"] = None
    return v
