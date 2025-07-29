"""Specification-driven tests for KLMD parser functionality."""

import json
from pathlib import Path
from typing import Any

import pytest


def run_spec_test(test_case: dict[str, Any], spec_group: str) -> None:
    """Run a specification test case."""
    markdown = test_case["markdown"]
    expected_html = test_case["html"]
    test_id = test_case["id"]
    description = test_case["description"]

    # Process markdown with KLMD parser
    # FIXME: Not implemented yet!
    actual_html = markdown

    # Compare actual vs expected output
    # Use pytest's comparison for better error reporting
    if actual_html != expected_html:
        pytest.fail(
            f"{spec_group}.{test_id} test failed: {description}\n"
            f"Input: {markdown}\n"
            f"Expected: {expected_html}\n"
            f"Actual: {actual_html}",
        )


def load_spec_groups() -> list[tuple[str, list[dict[str, Any]]]]:
    """Load spec groups for parametrization."""
    spec_file = Path(__file__).parent / "specification.json"
    with spec_file.open() as f:
        spec_json = json.load(f)
    return list(spec_json.items())


@pytest.mark.parametrize(("group_name", "test_cases"), load_spec_groups())
def test_klmd_specification(group_name: str, test_cases: list[dict[str, Any]]) -> None:
    """Test KLMD specification by group."""
    for test_case in test_cases:
        run_spec_test(test_case, group_name)
