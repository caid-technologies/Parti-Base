"""Regression tests for the inference-to-Space trust boundary."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from space_contract import audit_space_output  # noqa: E402


def _valid_record() -> dict:
    return {
        "project": {
            "project_id": "status_light",
            "name": "Status light",
            "category": "electronics",
            "summary": "A USB-powered controller and status LED.",
            "original_prompt": "Build a USB-powered status light.",
            "variant_type": "seed",
            "seed_project_id": "status_light",
        },
        "requirements": {
            "tools": ["multimeter"],
            "assumptions": [],
            "skill_level": "beginner",
            "safety_notes": ["Disconnect USB before changing wiring."],
            "constraints": ["Use USB power."],
        },
        "components": [{
            "component_id": "controller",
            "display_name": "Controller board",
            "category": "control",
            "type": "electronic",
            "material": "FR-4",
            "quantity": 1,
            "description": "USB-powered controller with an onboard LED.",
            "dimensions": {},
            "functional_role": "Drive the status indicator.",
            "fabrication_ref": None,
            "sourcing_ref": "controller",
        }],
        "relationships": [],
        "fabrication": {
            "processes": [],
            "component_settings": {},
            "post_processing": [],
            "tolerances": {},
        },
        "instructions": [{
            "step_id": "step_1",
            "phase": "testing",
            "title": "Power and test",
            "component_ids": ["controller"],
            "dependencies": [],
            "expected_result": "The onboard LED illuminates.",
        }],
        "sourcing": {
            "items": [{
                "component_id": "controller",
                "quantity": 1,
                "unit_cost_usd": 10,
                "total_cost_usd": 10,
            }],
            "cost_summary": {"total_usd": 10},
            "vendors": [],
        },
        "validation": {
            "schema_valid": True,
            "reference_integrity_valid": True,
            "manufacturability_valid": True,
            "naming_consistency_valid": True,
            "issues": [],
            "confidence_score": 0.9,
        },
    }


class SpaceContractTests(unittest.TestCase):
    def test_canonical_response_passes(self):
        report = audit_space_output(json.dumps(_valid_record()))
        self.assertTrue(report["accepted"])
        self.assertEqual(report["error_count"], 0)

    def test_markdown_fence_is_visible_as_a_warning(self):
        report = audit_space_output(f"```json\n{json.dumps(_valid_record())}\n```")
        self.assertTrue(report["accepted"])
        self.assertIn("json_fence_removed", {i["code"] for i in report["issues"]})

    def test_reasoning_snippet_does_not_hide_complete_record(self):
        wrapped = '<think>{"example": true}</think>\n' + json.dumps(_valid_record())
        report = audit_space_output(wrapped)

        self.assertTrue(report["accepted"])
        self.assertIn("json_wrapper_removed", {i["code"] for i in report["issues"]})

    def test_observed_legacy_space_shape_is_blocked(self):
        malformed = {
            "project": {"name": "Air monitor", "summary": "Measures PM2.5"},
            "requirements": ["USB powered"],
            "schematics": {},
            "assembly_steps": [],
            "validation": {
                "schema_valid": True,
                "reference_integrity_valid": True,
                "manufacturability_valid": True,
                "naming_consistency_valid": True,
                "issues": [],
                "confidence_score": 1.0,
            },
        }
        report = audit_space_output(json.dumps(malformed))
        self.assertFalse(report["accepted"])
        self.assertGreater(report["error_count"], 0)
        self.assertTrue(report["model_validation_ignored"])
        messages = " ".join(i["message"] for i in report["issues"])
        self.assertIn("components", messages)
        self.assertIn("requirements", messages)

    def test_invalid_json_is_blocked(self):
        report = audit_space_output("not a blueprint")
        self.assertFalse(report["accepted"])
        self.assertEqual(report["issues"][0]["code"], "invalid_json")


if __name__ == "__main__":
    unittest.main()
