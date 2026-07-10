"""Deterministic repair for model-emitted project JSON.

The fine-tuned model (out/parti-base) fails in two mechanical, fixable ways:

  1. Truncation — long outputs (full records, wiring maps) can hit the token
     budget mid-object, so the JSON never closes. `json_repair` closes the
     brackets; the half-written trailing list item it leaves behind is pruned.
  2. Id drift — ids occasionally break the snake_case contract (e.g.
     'motor_driver_h-bridge'), which also breaks every cross-reference to
     them. Ids are rewritten with normalize.to_snake_id and the SAME mapping
     is applied to every field that references them, so the record's
     reference graph stays intact.

This is the deterministic gate between the model and any consumer: a bug
class the model can't be trusted not to emit becomes structurally
unreachable behind repair_record(). It repairs SYNTAX and NAMING only —
it never invents content, so a record the model got semantically wrong
(missing sections, bad values) still fails validation afterwards.

Entry point:
    obj, notes = repair_record(text)
    obj   parsed (possibly repaired) object, or None if nothing salvageable
    notes list of human-readable strings describing every change made
"""
from __future__ import annotations

import json
import re
from typing import Any

from .normalize import to_snake_id

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


# --- 1. salvage: text -> object --------------------------------------------

def salvage_json(text: str) -> tuple[Any, list[str]]:
    """Parse model output into an object, repairing syntax if needed.

    Strict json.loads first (fenced, whole, or first-{ to last-}); only on
    failure fall back to json_repair, so well-formed output is never touched.
    Returns (object, notes) or (None, notes) if nothing parses.
    """
    t = text.strip()
    m = _FENCE.search(t)
    if m:
        t = m.group(1).strip()
    try:
        return json.loads(t), []
    except json.JSONDecodeError:
        pass
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(t[start:end + 1]), []
        except json.JSONDecodeError:
            pass
    if start == -1:
        return None, ["no JSON object found"]
    import json_repair
    obj = json_repair.loads(t[start:])
    if not isinstance(obj, dict):
        return None, [f"unrepairable: got {type(obj).__name__}, not an object"]
    return obj, ["syntax repaired (unclosed/malformed JSON)"]


def prune_truncated_tail(obj: dict) -> tuple[dict, list[str]]:
    """Drop the half-written trailing list item truncation leaves behind.

    After json_repair closes a truncated record, the LAST element of the list
    that was being written is usually incomplete (a dict missing keys its
    siblings all have). Detect exactly that — last item of a list of dicts,
    key set a proper subset of the first item's — and drop it. Only the tail
    is ever considered, so legitimately sparse items elsewhere are untouched.
    """
    notes: list[str] = []

    def _prune(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                _prune(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list) and len(node) >= 2:
            first, last = node[0], node[-1]
            if (isinstance(first, dict) and isinstance(last, dict)
                    and set(last) < set(first)):
                node.pop()
                notes.append(f"dropped incomplete trailing item in {path}")
            for i, v in enumerate(node):
                _prune(v, f"{path}[{i}]")

    _prune(obj, "")
    return obj, notes


# --- 2. ids: rewrite to snake_case, references included ---------------------

def _snake_map(ids: list[str]) -> dict[str, str]:
    """Old id -> valid snake_case id, deduplicated in first-seen order."""
    mapping: dict[str, str] = {}
    taken: set[str] = set()
    for old in ids:
        if old in mapping:
            continue
        base = to_snake_id(old) or "item"
        new, n = base, 1
        while new in taken:
            n += 1
            new = f"{base}_{n}"
        mapping[old] = new
        taken.add(new)
    return mapping


def fix_ids(obj: dict) -> tuple[dict, list[str]]:
    """Rewrite component/step ids to snake_case, consistently everywhere.

    One mapping per id namespace, applied to the declaration AND every field
    validate.py's reference-integrity layer checks: relationships
    source/target, instruction component_ids and dependencies,
    sourcing.items[].component_id, fabrication.component_settings keys.
    """
    notes: list[str] = []

    comps = obj.get("components")
    comp_map = _snake_map([c["component_id"] for c in comps
                           if isinstance(c, dict) and "component_id" in c]) \
        if isinstance(comps, list) else {}
    steps = obj.get("instructions")
    step_map = _snake_map([s["step_id"] for s in steps
                           if isinstance(s, dict) and "step_id" in s]) \
        if isinstance(steps, list) else {}

    def _sub(mapping: dict[str, str], old: Any, where: str) -> Any:
        if not isinstance(old, str):
            return old
        # Referenced-but-never-declared ids still get snaked so the FORMAT
        # is valid; the dangling reference stays visible to validation.
        new = mapping.get(old, to_snake_id(old) if old else old)
        if new != old:
            notes.append(f"{where}: {old!r} -> {new!r}")
        return new

    if isinstance(comps, list):
        for i, c in enumerate(comps):
            if isinstance(c, dict) and "component_id" in c:
                c["component_id"] = _sub(comp_map, c["component_id"],
                                         f"components[{i}]")
    if isinstance(obj.get("relationships"), list):
        for i, r in enumerate(obj["relationships"]):
            if isinstance(r, dict):
                for end in ("source", "target"):
                    if end in r:
                        r[end] = _sub(comp_map, r[end],
                                      f"relationships[{i}].{end}")
    if isinstance(steps, list):
        for i, s in enumerate(steps):
            if not isinstance(s, dict):
                continue
            if "step_id" in s:
                s["step_id"] = _sub(step_map, s["step_id"],
                                    f"instructions[{i}]")
            if isinstance(s.get("component_ids"), list):
                s["component_ids"] = [
                    _sub(comp_map, cid, f"instructions[{i}].component_ids")
                    for cid in s["component_ids"]]
            if isinstance(s.get("dependencies"), list):
                s["dependencies"] = [
                    _sub(step_map, d, f"instructions[{i}].dependencies")
                    for d in s["dependencies"]]
    sourcing = obj.get("sourcing")
    if isinstance(sourcing, dict) and isinstance(sourcing.get("items"), list):
        for i, item in enumerate(sourcing["items"]):
            if isinstance(item, dict) and "component_id" in item:
                item["component_id"] = _sub(comp_map, item["component_id"],
                                            f"sourcing.items[{i}]")
    fab = obj.get("fabrication")
    if isinstance(fab, dict) and isinstance(fab.get("component_settings"), dict):
        fab["component_settings"] = {
            _sub(comp_map, k, "fabrication.component_settings"): v
            for k, v in fab["component_settings"].items()}

    return obj, notes


# --- entry point -------------------------------------------------------------

def repair_record(text: str) -> tuple[dict | None, list[str]]:
    """Full pipeline: salvage syntax, prune truncation debris, fix ids."""
    obj, notes = salvage_json(text)
    if obj is None or not isinstance(obj, dict):
        return None, notes
    if notes:  # only syntax-repaired output can carry truncation debris
        obj, n2 = prune_truncated_tail(obj)
        notes += n2
    obj, n3 = fix_ids(obj)
    return obj, notes + n3
