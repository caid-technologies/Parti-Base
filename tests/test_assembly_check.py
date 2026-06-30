"""Tests for the assembly-instruction compliance gate (synth/assembly_check.py).

Runnable two ways:
    pytest tests/test_assembly_check.py
    python tests/test_assembly_check.py        # no pytest needed
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `synth` importable when run directly (python tests/test_assembly_check.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from synth.assembly_check import (  # noqa: E402
    PLACEHOLDER,
    filter_compliant,
    is_assembly_complete,
)


def _record(project_id: str, instructions: list[dict]) -> dict:
    return {"project": {"project_id": project_id}, "instructions": instructions}


COMPLIANT = _record("compliant_widget", [
    {
        "step_id": "fabricate_1",
        "phase": "fabrication",
        "title": "3D print the enclosure base",
        "component_ids": ["enclosure_base"],
        "dependencies": [],
        "expected_result": "unknown",
        "detail": {
            "summary": "Print the enclosure base in PETG for stiffness.",
            "steps": [
                "Load PETG filament and set the bed to 80C.",
                "Slice the base at 0.2mm layer height, 30% infill.",
                "Print and let the bed cool fully before removing the part.",
            ],
            "tip": "Good first-layer adhesion prevents warping on the wide base.",
        },
    },
])

# Same project but the one step's body is the placeholder marker → must skip.
NON_COMPLIANT = _record("placeholder_widget", [
    {
        "step_id": "fabricate_1",
        "phase": "fabrication",
        "title": "3D print the enclosure base",
        "component_ids": ["enclosure_base"],
        "dependencies": [],
        "expected_result": "unknown",
        "detail": {"summary": PLACEHOLDER, "steps": []},
    },
])


def test_compliant_record_is_complete():
    ok, reason = is_assembly_complete(COMPLIANT)
    assert ok, reason


def test_placeholder_record_is_incomplete():
    ok, reason = is_assembly_complete(NON_COMPLIANT)
    assert not ok
    assert "placeholder" in reason


def test_empty_instructions_is_incomplete():
    ok, reason = is_assembly_complete(_record("empty_widget", []))
    assert not ok
    assert "no instruction steps" in reason


def test_title_only_step_is_incomplete():
    rec = _record("title_only", [{
        "step_id": "s1", "phase": "assembly",
        "title": "Attach the lid", "component_ids": [], "dependencies": [],
        "expected_result": "unknown",
    }])
    ok, reason = is_assembly_complete(rec)
    assert not ok


def test_filter_emits_compliant_and_skips_placeholder():
    kept, summary = filter_compliant([COMPLIANT, NON_COMPLIANT])
    kept_ids = [r["project"]["project_id"] for r in kept]
    assert kept_ids == ["compliant_widget"]          # compliant emitted
    assert summary["seen"] == 2
    assert summary["emitted"] == 1
    assert summary["skipped"] == 1
    skipped_ids = [oid for oid, _ in summary["skipped_ids"]]
    assert skipped_ids == ["placeholder_widget"]      # placeholder skipped


def _run_all() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run_all())
