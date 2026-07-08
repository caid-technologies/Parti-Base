"""Gate tests for eval_local.py's pure (no-GPU) pieces.

Runnable two ways:
    pytest tests/test_eval_local.py
    python tests/test_eval_local.py        # no pytest needed
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval_local import (  # noqa: E402
    SCORERS,
    detect_mode,
    extract_json,
    f1_from_counts,
    keyset,
    prf,
)


def test_extract_json_fenced():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_prose_wrapped():
    assert extract_json('Here you go: {"a": 1} done') == {"a": 1}


def test_extract_json_plain_nested():
    assert extract_json('{"a": {"b": 2}}') == {"a": {"b": 2}}


def test_extract_json_no_json_raises():
    try:
        extract_json("no json here")
        assert False, "should have raised"
    except json.JSONDecodeError:
        pass


def test_detect_mode():
    assert detect_mode("Mode E — Project→Instructions...") == "E"
    assert detect_mode("nothing") == "?"


def test_score_f_valid_and_invalid():
    ok = {"schema_valid": True, "reference_integrity_valid": True,
          "manufacturability_valid": True, "naming_consistency_valid": True,
          "issues": [], "confidence_score": 0.9}
    assert SCORERS["F"](ok, "") == []
    assert SCORERS["F"](dict(ok, confidence_score=1.5), "")   # out of [0,1]
    assert SCORERS["F"]({}, "")                               # all keys missing


def test_score_d_flags_unknown_component():
    user = json.dumps({"components": [{"component_id": "a"}, {"component_id": "b"}]})
    good = {"relationships": [{"source": "a", "relation": "connects_to", "target": "b"}]}
    bad = {"relationships": [{"source": "a", "relation": "connects_to", "target": "zzz"}]}
    assert SCORERS["D"](good, user) == []
    assert SCORERS["D"](bad, user)


def test_score_e_dependency_ordering():
    user = json.dumps({"components": [{"component_id": "a"}]})
    good = {"instructions": [
        {"step_id": "s1", "phase": "assembly", "component_ids": ["a"], "dependencies": []},
        {"step_id": "s2", "phase": "testing", "component_ids": ["a"], "dependencies": ["s1"]},
    ]}
    forward = {"instructions": [
        {"step_id": "s1", "phase": "assembly", "component_ids": ["a"], "dependencies": ["s2"]},
        {"step_id": "s2", "phase": "testing", "component_ids": ["a"], "dependencies": []},
    ]}
    assert SCORERS["E"](good, user) == []
    assert SCORERS["E"](forward, user)   # depends on a later step


def test_keyset_prf_f1():
    gold = keyset("D", {"relationships": [
        {"source": "a", "relation": "connects_to", "target": "b"}]})
    pred = keyset("D", {"relationships": [
        {"source": "a", "relation": "connects_to", "target": "b"},
        {"source": "x", "relation": "mounted_on", "target": "y"}]})
    tp, fp, fn = prf(pred, gold)
    assert (tp, fp, fn) == (1, 1, 0)
    assert 0 < f1_from_counts(tp, fp, fn) < 1
    assert f1_from_counts(0, 5, 5) == 0.0


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
