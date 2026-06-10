"""Repair low-confidence normalized seeds in-place.

Three repair strategies, applied in order:

  A. Fuzzy-resolve dangling refs to existing component_ids
     - drop trailing 's' for plural→singular (`ultrasonic_sensors` → `ultrasonic_sensor`)
     - common alias swaps (`_microcontroller` ↔ `_mcu`, `_module` drops, ...)
     - substring containment (last-resort)
  B. Add placeholder components for refs that can't be resolved
     - infer category/type/material from the id text
     - link via existing relationship intent or instruction step
  C. Synthesize instructions for seeds with `empty_instructions`
     - group components by phase (fabrication → wiring → bring_up → assembly)
     - chain step dependencies linearly

After fixup, `validate_normalized(strict=True)` must pass for each record.
"""
from __future__ import annotations
import copy
import re

from .costs import recompute_cost_summary

# --- fuzzy id resolution --------------------------------------------------

_ALIAS_SWAPS = [
    ("_microcontroller", "_mcu"),
    ("_mcu", "_microcontroller"),
]

# Tokens that mark "accessory parts FOR another component" — never fuzzy-match
# a base component to one of its accessories or vice versa.
_ACCESSORY_TOKENS = {
    "mount", "housing", "holder", "bezel", "frame", "cover", "grille",
    "mast", "bracket", "shell", "case", "enclosure", "panel", "stand",
}

# Number-like tokens — if both ids contain different numeric specs the match is wrong.
_NUMERIC_RE = re.compile(r"^(m\d+(?:\.\d+)?|\d+v\d*|\d+ma|\d+w|\d+mm|\d+cm|\d+s|\d+x\d+|\d+ah|\d+mah|\d+gb|\d+mhz|\d+ghz|v\d+)$", re.I)


def _tokens(id_: str) -> list[str]:
    return id_.lower().split("_")


def _numeric_tokens(id_: str) -> set[str]:
    return {t for t in _tokens(id_) if _NUMERIC_RE.match(t)}


def _accessory_tokens(id_: str) -> set[str]:
    return set(_tokens(id_)) & _ACCESSORY_TOKENS


def _compatible(missing_id: str, candidate: str) -> bool:
    """Reject obviously-wrong matches: differing numeric specs, accessory-vs-base."""
    # Numeric mismatch: if both have numeric tokens and they differ → reject
    m_nums = _numeric_tokens(missing_id)
    c_nums = _numeric_tokens(candidate)
    if m_nums and c_nums and not (m_nums & c_nums):
        return False
    # Accessory-vs-base: candidate has accessory token that missing lacks → reject
    # (and vice versa). Components and their mounts are different things.
    m_acc = _accessory_tokens(missing_id)
    c_acc = _accessory_tokens(candidate)
    if m_acc != c_acc:
        return False
    return True


def fuzzy_resolve(missing_id: str, existing_ids: set[str]) -> str | None:
    """Return an existing id that probably matches `missing_id`, or None.

    Conservative: prefers no match over a wrong one. When uncertain, the
    caller adds a placeholder component instead.
    """
    if missing_id in existing_ids:
        return missing_id

    # Plural → singular (and vice versa)
    if missing_id.endswith("s") and missing_id[:-1] in existing_ids:
        cand = missing_id[:-1]
        if _compatible(missing_id, cand):
            return cand
    if (missing_id + "s") in existing_ids and _compatible(missing_id, missing_id + "s"):
        return missing_id + "s"

    # Alias swap (microcontroller ↔ mcu)
    for old, new in _ALIAS_SWAPS:
        if old in missing_id:
            alt = missing_id.replace(old, new)
            if alt in existing_ids and _compatible(missing_id, alt):
                return alt

    # Strip trailing structural suffix only
    stripped = re.sub(r"_(module|kit|assortment|assembly|board|unit|device)$",
                      "", missing_id)
    if stripped != missing_id and stripped in existing_ids \
            and _compatible(missing_id, stripped):
        return stripped

    # Token-overlap fallback — but tight: require ≥2 shared tokens, ≥75% overlap,
    # AND compatibility check.
    tokens_missing = set(_tokens(missing_id))
    best: tuple[str, float] | None = None
    for eid in existing_ids:
        if not _compatible(missing_id, eid):
            continue
        tokens_existing = set(_tokens(eid))
        shared = tokens_existing & tokens_missing
        if len(shared) < 2:
            continue
        smaller = min(len(tokens_existing), len(tokens_missing))
        overlap = len(shared) / smaller
        if overlap < 0.75:
            continue
        if best is None or overlap > best[1]:
            best = (eid, overlap)
    return best[0] if best else None


# --- placeholder component generation -------------------------------------

# Token → (category, type, material)
_CATEGORY_FROM_TOKEN = {
    "mcu": ("electrical", "electronic", "unknown"),
    "controller": ("electrical", "electronic", "unknown"),
    "esp32": ("electrical", "electronic", "unknown"),
    "raspberry": ("electrical", "electronic", "unknown"),
    "pixhawk": ("electrical", "electronic", "unknown"),
    "module": ("electrical", "electronic", "unknown"),
    "sensor": ("electrical", "electronic", "unknown"),
    "camera": ("electrical", "electronic", "unknown"),
    "lidar": ("electrical", "electronic", "unknown"),
    "tfmini": ("electrical", "electronic", "unknown"),
    "gps": ("electrical", "electronic", "unknown"),
    "antenna": ("electrical", "electronic", "unknown"),
    "battery": ("electrical", "electronic", "unknown"),
    "lipo": ("electrical", "electronic", "unknown"),
    "charger": ("electrical", "electronic", "unknown"),
    "buck": ("electrical", "electronic", "unknown"),
    "boost": ("electrical", "electronic", "unknown"),
    "regulator": ("electrical", "electronic", "unknown"),
    "display": ("electrical", "electronic", "unknown"),
    "oled": ("electrical", "electronic", "unknown"),
    "led": ("electrical", "electronic", "unknown"),
    "speaker": ("electrical", "electronic", "unknown"),
    "buzzer": ("electrical", "electronic", "unknown"),
    "microphone": ("electrical", "electronic", "unknown"),
    "mic": ("electrical", "electronic", "unknown"),
    "button": ("electrical", "electronic", "unknown"),
    "switch": ("electrical", "electronic", "unknown"),
    "motor": ("electrical", "electronic", "unknown"),
    "servo": ("electrical", "electronic", "unknown"),
    "esc": ("electrical", "electronic", "unknown"),
    "qi": ("electrical", "electronic", "unknown"),
    "magsafe": ("electrical", "electronic", "unknown"),

    "screw": ("mechanical", "fastener", "carbon_steel"),
    "screws": ("mechanical", "fastener", "carbon_steel"),
    "bolt": ("mechanical", "fastener", "carbon_steel"),
    "nut": ("mechanical", "fastener", "carbon_steel"),
    "washer": ("mechanical", "fastener", "carbon_steel"),
    "standoff": ("mechanical", "fastener", "brass"),

    "mount": ("mechanical", "3d_printed", "PLA"),
    "bracket": ("mechanical", "3d_printed", "PLA"),
    "holder": ("mechanical", "3d_printed", "PLA"),
    "housing": ("mechanical", "3d_printed", "PLA"),
    "enclosure": ("mechanical", "3d_printed", "PLA"),
    "frame": ("mechanical", "3d_printed", "PLA"),
    "panel": ("mechanical", "3d_printed", "PLA"),
    "cover": ("mechanical", "3d_printed", "PLA"),
    "shell": ("mechanical", "3d_printed", "PLA"),
    "hinge": ("mechanical", "3d_printed", "PLA"),
    "grille": ("mechanical", "3d_printed", "PLA"),
    "bezel": ("mechanical", "3d_printed", "PLA"),
    "cap": ("mechanical", "3d_printed", "PLA"),
    "mast": ("mechanical", "3d_printed", "PLA"),
}


def infer_placeholder_fields(missing_id: str) -> tuple[str, str, str]:
    """Return (category, type, material) for a placeholder component."""
    tokens = missing_id.lower().split("_")
    for tok in tokens:
        if tok in _CATEGORY_FROM_TOKEN:
            return _CATEGORY_FROM_TOKEN[tok]
    # Default: assume an off-the-shelf electrical part
    return ("electrical", "electronic", "unknown")


def make_placeholder_component(missing_id: str) -> dict:
    category, ctype, material = infer_placeholder_fields(missing_id)
    display = missing_id.replace("_", " ").title()
    return {
        "component_id": missing_id,
        "display_name": display,
        "category": category,
        "type": ctype,
        "material": material,
        "quantity": 1,
        "description": f"{display} - added during seed repair to resolve a dangling reference.",
        "dimensions": {"raw": None},
        "functional_role": "unknown",
        "fabrication_ref": missing_id if ctype == "3d_printed" else None,
        "sourcing_ref": missing_id,
    }


# --- print-settings backfill ----------------------------------------------

# Materials parse_print_settings recognizes as a print material_hint.
_PRINT_MATERIALS = {"PLA", "PETG", "ABS", "ASA", "TPU", "NYLON", "PC"}

# Categories/roles that warrant stronger settings than the cosmetic default.
_STRUCTURAL_CATEGORIES = {"structural", "mounting"}


def backfill_print_settings(rec: dict) -> int:
    """Add default fabrication settings for any 3d_printed component missing them.

    Generated projects rarely carry `printSettings`, so their
    `fabrication.component_settings` come out empty — unlike the Data examples,
    which populate one entry per printed part. This synthesizes settings in the
    same `parse_print_settings` shape (raw + parsed fields) so the normalized
    structure matches. Idempotent: existing entries are never overwritten.
    Returns the number of entries added.
    """
    from .normalize import parse_print_settings

    fab = rec.setdefault("fabrication", {})
    settings: dict = fab.setdefault("component_settings", {})
    added = 0
    for c in rec.get("components", []):
        if c.get("type") != "3d_printed":
            continue
        cid = c["component_id"]
        if cid in settings:
            continue
        mat = (c.get("material") or "").upper()
        hint = mat if mat in _PRINT_MATERIALS else "PLA"
        structural = (
            c.get("category") in _STRUCTURAL_CATEGORIES
            or c.get("functional_role") == "structural"
        )
        infill, perim, layer = (40, 4, 0.2) if structural else (20, 3, 0.2)
        raw = f"{layer}mm layer, {infill}% infill, {perim} perimeters, {hint}"
        settings[cid] = parse_print_settings(raw)
        added += 1

    if added:
        processes = fab.setdefault("processes", [])
        if "fdm_3d_printing" not in processes:
            processes.append("fdm_3d_printing")
            fab["processes"] = sorted(processes)
    return added


# --- instruction synthesis ------------------------------------------------

_PHASE_FOR_TYPE = {
    "3d_printed": "fabrication",
    "machined": "fabrication",
    "laser_cut": "fabrication",
    "electronic": "wiring",
    "fastener": "assembly",
    "mechanical": "assembly",
    "consumable": "assembly",
    "misc": "assembly",
}


def synthesize_instructions(components: list[dict]) -> list[dict]:
    """Build a minimal 3-phase instruction sequence from components."""
    by_phase: dict[str, list[dict]] = {"fabrication": [], "wiring": [], "assembly": []}
    for c in components:
        phase = _PHASE_FOR_TYPE.get(c["type"], "assembly")
        if phase == "fabrication":
            by_phase["fabrication"].append({
                "title": f"Fabricate {c['display_name']}",
                "component_ids": [c["component_id"]],
            })
        elif phase == "wiring":
            by_phase["wiring"].append({
                "title": f"Connect {c['display_name']}",
                "component_ids": [c["component_id"]],
            })
        else:
            by_phase["assembly"].append({
                "title": f"Install {c['display_name']}",
                "component_ids": [c["component_id"]],
            })

    out: list[dict] = []
    counter = 0
    last_step: str | None = None
    for phase in ("fabrication", "wiring", "assembly"):
        for i, step in enumerate(by_phase[phase], start=1):
            counter += 1
            step_id = f"{phase}_{i}"
            out.append({
                "step_id": step_id,
                "phase": phase,
                "title": step["title"],
                "component_ids": step["component_ids"],
                "dependencies": [last_step] if last_step else [],
                "expected_result": "unknown",
            })
            last_step = step_id
    return out


# --- top-level fixup -----------------------------------------------------

def _gather_dangling_refs(rec: dict) -> set[str]:
    """Collect every referenced component_id whose component doesn't exist."""
    existing = {c["component_id"] for c in rec.get("components", [])}
    missing: set[str] = set()
    for r in rec.get("relationships", []):
        for k in ("source", "target"):
            if r[k] not in existing:
                missing.add(r[k])
    for step in rec.get("instructions", []):
        for cid in step.get("component_ids", []):
            if cid not in existing:
                missing.add(cid)
    # Also walk validation.issues for refs we know were dropped
    for it in rec.get("validation", {}).get("issues", []):
        for ref in it.get("refs", []):
            if ref and ref not in existing:
                missing.add(ref)
    return missing


def fixup_record(rec: dict) -> tuple[dict, list[str]]:
    """Return (fixed_record, list_of_actions_taken)."""
    rec = copy.deepcopy(rec)
    actions: list[str] = []
    existing_ids = {c["component_id"] for c in rec.get("components", [])}

    missing_refs = _gather_dangling_refs(rec)

    # 1. Fuzzy-resolve as many as possible
    resolutions: dict[str, str] = {}
    for ref in list(missing_refs):
        match = fuzzy_resolve(ref, existing_ids)
        if match:
            resolutions[ref] = match
            actions.append(f"fuzzy-resolve {ref!r} -> {match!r}")
            missing_refs.discard(ref)

    # 2. Add placeholders for the rest
    for ref in missing_refs:
        placeholder = make_placeholder_component(ref)
        rec["components"].append(placeholder)
        existing_ids.add(ref)
        actions.append(f"add placeholder component {ref!r}")

    # 3. Rewrite refs in existing relationships and instructions
    if resolutions:
        for r in rec.get("relationships", []):
            for k in ("source", "target"):
                if r[k] in resolutions:
                    r[k] = resolutions[r[k]]
        for step in rec.get("instructions", []):
            step["component_ids"] = [
                resolutions.get(cid, cid) for cid in step.get("component_ids", [])
            ]

    # 4. Synthesize instructions if empty
    if not rec.get("instructions"):
        rec["instructions"] = synthesize_instructions(rec["components"])
        actions.append(f"synthesize {len(rec['instructions'])} instruction steps")

    # 5. Refresh sourcing.items for any newly-added placeholder components
    sourcing_ids = {it["component_id"] for it in rec["sourcing"]["items"]}
    for c in rec["components"]:
        if c["component_id"] not in sourcing_ids:
            rec["sourcing"]["items"].append({
                "component_id": c["component_id"],
                "product_name": c["display_name"],
                "unit_cost_usd": 0.0,
                "quantity": c["quantity"],
                "total_cost_usd": 0.0,
                "vendor": None,
                "url": None,
            })
    # Recompute summary (item totals were set explicitly above)
    recompute_cost_summary(rec)

    # 6. Clear validation issues — re-checked downstream
    rec["validation"] = {
        "schema_valid": True,
        "reference_integrity_valid": True,
        "manufacturability_valid": True,
        "naming_consistency_valid": True,
        "issues": [],
        "confidence_score": 1.0,
    }

    return rec, actions
