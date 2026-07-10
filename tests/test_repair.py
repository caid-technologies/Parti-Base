"""Gate tests for synth/repair.py — the model-output repair layer.

The fixtures mirror the two real failure classes seen from out/parti-base:
truncated JSON (token budget hit mid-object) and non-snake_case ids
('motor_driver_h-bridge') that break every cross-reference.

Runnable two ways:
    pytest tests/test_repair.py
    python tests/test_repair.py        # no pytest needed
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from synth.repair import (  # noqa: E402
    fix_ids,
    prune_truncated_tail,
    repair_record,
    salvage_json,
)


def _comp(cid: str, **kw) -> dict:
    c = {"component_id": cid, "display_name": cid, "category": "electronics",
         "type": "sensor", "material": "abs", "quantity": 1,
         "description": "x", "dimensions": {"raw": "1x1x1mm"},
         "functional_role": "misc"}
    c.update(kw)
    return c


# --- salvage_json ------------------------------------------------------------

def test_salvage_valid_json_untouched():
    obj, notes = salvage_json('{"components": []}')
    assert obj == {"components": []}
    assert notes == []


def test_salvage_fenced():
    obj, notes = salvage_json('```json\n{"a": 1}\n```')
    assert obj == {"a": 1}
    assert notes == []


def test_salvage_truncated_mid_object():
    # the exact eval failure shape: budget hit mid-component, JSON never closes
    text = ('{"components": [' + json.dumps(_comp("led_5mm")) +
            ', {"component_id": "push_button_23", "display_name": "Bu')
    obj, notes = salvage_json(text)
    assert isinstance(obj, dict)
    assert notes  # syntax repair was needed and reported
    assert obj["components"][0]["component_id"] == "led_5mm"


def test_salvage_garbage_returns_none():
    obj, notes = salvage_json("I could not produce a design, sorry.")
    assert obj is None
    assert notes


# --- prune_truncated_tail ----------------------------------------------------

def test_prune_drops_half_written_tail():
    obj = {"components": [_comp("a"), _comp("b"),
                          {"component_id": "c", "display_name": "C"}]}
    obj, notes = prune_truncated_tail(obj)
    assert [c["component_id"] for c in obj["components"]] == ["a", "b"]
    assert notes == ["dropped incomplete trailing item in components"]


def test_prune_keeps_complete_tail():
    obj = {"components": [_comp("a"), _comp("b")]}
    obj, notes = prune_truncated_tail(obj)
    assert len(obj["components"]) == 2 and notes == []


def test_prune_keeps_sparse_non_tail_items():
    # only the TAIL is truncation debris; a sparse middle item is content
    obj = {"components": [_comp("a"), {"component_id": "b"}, _comp("c")]}
    obj, notes = prune_truncated_tail(obj)
    assert len(obj["components"]) == 3 and notes == []


# --- fix_ids -----------------------------------------------------------------

def test_fix_ids_rewrites_declaration_and_every_reference():
    # the real mode A failure: hyphen in an id, referenced from everywhere
    obj = {
        "components": [_comp("motor_driver_h-bridge"), _comp("esp32")],
        "relationships": [{"source": "esp32", "relation": "controls",
                           "target": "motor_driver_h-bridge"}],
        "instructions": [{"step_id": "Step-1", "component_ids":
                          ["motor_driver_h-bridge"], "dependencies": []},
                         {"step_id": "step_2", "component_ids": [],
                          "dependencies": ["Step-1"]}],
        "sourcing": {"items": [{"component_id": "motor_driver_h-bridge"}]},
        "fabrication": {"component_settings":
                        {"motor_driver_h-bridge": {"process": "none"}}},
    }
    obj, notes = fix_ids(obj)
    fixed = "motor_driver_h_bridge"
    assert obj["components"][0]["component_id"] == fixed
    assert obj["relationships"][0]["target"] == fixed
    assert obj["instructions"][0]["component_ids"] == [fixed]
    assert obj["instructions"][0]["step_id"] == "step_1"
    assert obj["instructions"][1]["dependencies"] == ["step_1"]
    assert obj["sourcing"]["items"][0]["component_id"] == fixed
    assert list(obj["fabrication"]["component_settings"]) == [fixed]
    assert notes  # every rewrite is reported


def test_fix_ids_dedupes_collisions():
    # two ids that snake to the same string must stay distinct
    obj = {"components": [_comp("Led-1"), _comp("led_1")]}
    obj, _ = fix_ids(obj)
    ids = [c["component_id"] for c in obj["components"]]
    assert ids[0] != ids[1] and ids[0] == "led_1"


def test_fix_ids_clean_record_is_untouched():
    obj = {"components": [_comp("led_5mm")],
           "relationships": [{"source": "led_5mm", "relation": "mounts_to",
                              "target": "led_5mm"}]}
    before = json.dumps(obj, sort_keys=True)
    obj, notes = fix_ids(obj)
    assert json.dumps(obj, sort_keys=True) == before and notes == []


# --- repair_record (full pipeline) -------------------------------------------

def test_repair_record_end_to_end_truncation_plus_ids():
    text = ('{"components": [' + json.dumps(_comp("h-bridge_driver")) +
            ', {"component_id": "led_5mm", "display_na')
    obj, notes = repair_record(text)
    assert obj is not None
    assert [c["component_id"] for c in obj["components"]] == ["h_bridge_driver"]
    assert len(notes) >= 3  # syntax + prune + id rewrite all reported


def test_repair_record_valid_input_passthrough():
    obj, notes = repair_record('{"components": []}')
    assert obj == {"components": []} and notes == []


def test_repair_record_never_invents_content():
    # a record missing 'components' stays missing — repair fixes syntax and
    # naming, not semantics
    obj, notes = repair_record('{"relationships": []}')
    assert "components" not in obj


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"{len(fns)} passed")
