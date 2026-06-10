"""Patch specific prompt↔design gaps in normalized seed records.

The semantic audit flagged components implied by the prompt but absent from
the design. This adds them at the source (normalized seed) so the fix
propagates to every downstream variant + mode.

Only the two genuine gaps are patched. `portable_hacking_tool`'s "speaker"
flag is a false positive (it controls EXTERNAL speakers via its Bluetooth
module) and is intentionally left alone.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synth.config import NORMALIZED_DIR
from synth.costs import recompute_cost_summary
from synth.validate import is_valid, validate_normalized

# project_id → component to add + the existing component_id it connects to.
PATCHES: dict[str, dict] = {
    "digital_desk_clock": {
        "component": {
            "component_id": "ir_receiver",
            "display_name": "IR Remote Receiver",
            "category": "electrical",
            "type": "electronic",
            "material": "unknown",
            "quantity": 1,
            "description": "VS1838B 38kHz infrared receiver for the handheld "
                           "remote that adjusts color, time, and settings.",
            "dimensions": {"raw": "7x6x5mm", "length_mm": 7.0,
                           "width_mm": 6.0, "height_mm": 5.0},
            "functional_role": "user_input",
            "fabrication_ref": None,
            "sourcing_ref": "ir_receiver",
        },
        "connect_to": "esp32_s3_mcu",
        "relation_notes": "protocol=GPIO; voltage=3.3V",
        "unit_cost": 0.75,
        "remote": {
            "component_id": "ir_remote",
            "display_name": "IR Remote Control",
            "category": "interface",
            "type": "electronic",
            "material": "unknown",
            "quantity": 1,
            "description": "Handheld 21-key infrared remote to control the clock.",
            "dimensions": {"raw": "85x40x6mm", "length_mm": 85.0,
                           "width_mm": 40.0, "height_mm": 6.0},
            "functional_role": "user_input",
            "fabrication_ref": None,
            "sourcing_ref": "ir_remote",
        },
        "remote_cost": 1.50,
    },
    "river_cleaning_boat": {
        "component": {
            "component_id": "rf_receiver_2_4ghz",
            "display_name": "2.4GHz RC Receiver",
            "category": "electrical",
            "type": "electronic",
            "material": "unknown",
            "quantity": 1,
            "description": "2.4GHz radio receiver paired with a handheld "
                           "transmitter for remote control of the boat.",
            "dimensions": {"raw": "25x15x4mm", "length_mm": 25.0,
                           "width_mm": 15.0, "height_mm": 4.0},
            "functional_role": "wireless",
            "fabrication_ref": None,
            "sourcing_ref": "rf_receiver_2_4ghz",
        },
        "connect_to": None,  # resolved to first MCU/controller at runtime
        "relation_notes": "protocol=PWM; voltage=5V",
        "unit_cost": 8.0,
        "remote": {
            "component_id": "rc_transmitter",
            "display_name": "2.4GHz RC Transmitter",
            "category": "interface",
            "type": "electronic",
            "material": "unknown",
            "quantity": 1,
            "description": "Handheld 2.4GHz transmitter for remote piloting.",
            "dimensions": {"raw": "180x100x60mm", "length_mm": 180.0,
                           "width_mm": 100.0, "height_mm": 60.0},
            "functional_role": "user_input",
            "fabrication_ref": None,
            "sourcing_ref": "rc_transmitter",
        },
        "remote_cost": 22.0,
    },
}


def _first_controller(rec: dict) -> str | None:
    for c in rec["components"]:
        if c.get("functional_role") == "main_controller":
            return c["component_id"]
    for c in rec["components"]:
        if c["category"] == "electrical":
            return c["component_id"]
    return None


def _add_component(rec: dict, comp: dict, unit_cost: float) -> None:
    rec["components"].append(comp)
    rec["sourcing"]["items"].append({
        "component_id": comp["component_id"],
        "product_name": comp["display_name"],
        "unit_cost_usd": unit_cost,
        "quantity": comp["quantity"],
        "total_cost_usd": round(unit_cost * comp["quantity"], 2),
        "vendor": None,
        "url": None,
    })


def patch_seed(pid: str, spec: dict) -> bool:
    path = NORMALIZED_DIR / f"{pid}.json"
    if not path.exists():
        print(f"  [skip] {pid}: not found")
        return False
    rec = json.loads(path.read_text(encoding="utf-8"))
    existing = {c["component_id"] for c in rec["components"]}

    comp = spec["component"]
    if comp["component_id"] in existing:
        print(f"  [skip] {pid}: {comp['component_id']} already present")
        return False

    _add_component(rec, comp, spec["unit_cost"])
    _add_component(rec, spec["remote"], spec["remote_cost"])

    target = spec["connect_to"] or _first_controller(rec)
    # receiver ↔ controller (electrical)
    rec["relationships"].append({
        "source": comp["component_id"],
        "relation": "connects_to",
        "target": target,
        "required": True,
        "notes": spec["relation_notes"],
    })
    # remote → receiver (interface, logical pairing)
    rec["relationships"].append({
        "source": spec["remote"]["component_id"],
        "relation": "connects_to",
        "target": comp["component_id"],
        "required": True,
        "notes": "wireless remote pairing",
    })

    # Add a bring_up step referencing the new receiver.
    rec["instructions"].append({
        "step_id": f"bringup_{comp['component_id']}",
        "phase": "bring_up",
        "title": f"Test {comp['display_name']} and pair with "
                 f"{spec['remote']['display_name']}",
        "component_ids": [comp["component_id"], spec["remote"]["component_id"]],
        "dependencies": [rec["instructions"][-1]["step_id"]] if rec["instructions"] else [],
        "expected_result": "remote commands are received and acted on",
    })

    recompute_cost_summary(rec)
    rec["validation"]["components_total"] = len(rec["components"])

    if not is_valid(rec):
        errs = [i["code"] for i in validate_normalized(rec) if i["severity"] == "error"]
        print(f"  [FAIL] {pid}: patch broke validation: {errs[:4]}")
        return False

    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [ok] {pid}: added {comp['component_id']} + "
          f"{spec['remote']['component_id']}")
    return True


def main() -> int:
    print("Patching prompt-design gaps in normalized seeds...")
    patched = 0
    for pid, spec in PATCHES.items():
        if patch_seed(pid, spec):
            patched += 1
    print(f"\nPatched {patched}/{len(PATCHES)} seeds.")
    print("Note: portable_hacking_tool 'speaker' flag left as-is "
          "(controls external speakers via Bluetooth — not a real gap).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
