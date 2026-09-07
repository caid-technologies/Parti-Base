"""Pre-deployment gate for full-project (Mode B) model responses.

The model's own ``validation`` object is untrusted output. This module parses a
response, runs the repository's deterministic canonical validator, and returns a
small report suitable for CI, a Space, or another inference client.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from synth.validate import validate_normalized


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _issue(code: str, message: str) -> dict[str, Any]:
    return {"severity": "error", "code": code, "message": message, "refs": []}


def parse_model_json(raw_output: str) -> tuple[Any | None, list[dict[str, Any]]]:
    """Parse plain, fenced, or prose-wrapped JSON without hiding repairs."""
    text = raw_output.strip()
    issues: list[dict[str, Any]] = []

    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1).strip()
        issues.append({
            "severity": "warn",
            "code": "json_fence_removed",
            "message": "Removed a Markdown JSON fence before parsing.",
            "refs": [],
        })

    try:
        return json.loads(text), issues
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                value = json.loads(text[start:end + 1])
                issues.append({
                    "severity": "warn",
                    "code": "json_wrapper_removed",
                    "message": "Removed prose around the JSON object before parsing.",
                    "refs": [],
                })
                return value, issues
            except json.JSONDecodeError:
                pass

    return None, [_issue("invalid_json", "The model response is not one complete JSON object.")]


def audit_space_output(raw_output: str) -> dict[str, Any]:
    """Return a deterministic acceptance report for one Mode B response."""
    record, issues = parse_model_json(raw_output)
    if not isinstance(record, dict):
        if record is not None:
            issues.append(_issue("wrong_root_type", "The JSON root must be an object."))
        return {
            "accepted": False,
            "error_count": sum(i["severity"] == "error" for i in issues),
            "warning_count": sum(i["severity"] == "warn" for i in issues),
            "model_validation_ignored": True,
            "issues": issues,
        }

    deterministic_issues = validate_normalized(record, strict=True)
    issues.extend(deterministic_issues)
    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warn"]
    return {
        "accepted": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "model_validation_ignored": True,
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit one raw Mode B response before serving or rendering it."
    )
    parser.add_argument(
        "response",
        nargs="?",
        type=Path,
        help="Text/JSON response file. Reads standard input when omitted.",
    )
    args = parser.parse_args(argv)
    try:
        raw_output = (
            args.response.read_text(encoding="utf-8")
            if args.response
            else sys.stdin.read()
        )
    except OSError as exc:
        print(json.dumps({"accepted": False, "error": str(exc)}, indent=2))
        return 2
    report = audit_space_output(raw_output)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
