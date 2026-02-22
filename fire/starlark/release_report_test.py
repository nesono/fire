#!/usr/bin/env python3
"""Unit tests for release report draft parsers."""

import pytest

from fire.starlark import release_report


def test_parse_source_traceability_data():
    data = {
        "implements": {
            "src/brake.cc": [{"req_id": "REQ-1", "version": 2}],
        },
        "verifies": {
            "tests/brake_test.cc": [{"req_id": "REQ-1", "version": 2}],
        },
    }
    entries = release_report.parse_source_traceability_data(data, "trace.json")

    assert entries == [
        {
            "type": "impl",
            "requirement": "REQ-1",
            "source": "src/brake.cc",
            "version": 2,
        },
        {
            "type": "verif",
            "requirement": "REQ-1",
            "source": "tests/brake_test.cc",
            "version": 2,
        },
    ]


def test_parse_exemptions_valid():
    data = [
        {
            "requirement": "REQ-1",
            "kind": "impl",
            "justification": "Deferred for prototype release",
            "owner": "team-abc",
        }
    ]
    entries = release_report.parse_exemptions(data, "exemptions.yaml")

    assert entries[0]["kind"] == "impl"
    assert entries[0]["requirement"] == "REQ-1"


def test_parse_exemptions_requires_justification():
    data = [{"requirement": "REQ-1", "kind": "impl"}]
    with pytest.raises(ValueError, match="justification"):
        release_report.parse_exemptions(data, "exemptions.yaml")


def test_extract_todos():
    content = """
    TODO(ABC-123) needs follow-up
    Another TODO(DEF-9) line
    """
    todos = release_report.extract_todos(content)
    assert todos == ["TODO(ABC-123)", "TODO(DEF-9)"]


def test_parse_requirement_sections_and_metadata():
    content = """
## REQ-ALPHA-001
SIL: ASIL-B | Sec: false | Version: 2 | Parent: [REQ-BASE-001](/base.md?version=1#REQ-BASE-001)

Requirement text with [REQ-BASE-001](/base.md?version=1#REQ-BASE-001).

## REQ-BETA-002
SIL: ASIL-A | Sec: true | Version: 1
Body without references.
"""
    sections = release_report.parse_requirement_sections(content)

    assert [section["id"] for section in sections] == ["REQ-ALPHA-001", "REQ-BETA-002"]
    assert sections[0]["metadata"]["version"] == 2
    assert "parent" in sections[0]["metadata"]


def test_collect_requirement_reference_versions():
    content = """
## REQ-ALPHA-001
SIL: ASIL-B | Sec: false | Version: 2

See [REQ-BASE-001](/base.md?version=1#REQ-BASE-001).
"""
    sections = release_report.parse_requirement_sections(content)
    refs = release_report.collect_requirement_references(sections[0])

    assert refs == [("REQ-BASE-001", 1)]


def test_build_parameter_version_map():
    data = {
        "max_speed_v1": {"value": 1, "unit": "m/s", "description": "x"},
        "min_speed_v2": {"value": 2, "unit": "m/s", "description": "y"},
    }
    param_versions = release_report.build_param_version_map(data, "params.yaml")

    assert param_versions == {"max_speed": 1, "min_speed": 2}


def test_find_stale_requirement_references():
    content = """
## REQ-ALPHA-001
SIL: ASIL-B | Sec: false | Version: 2 | Parent: [REQ-BASE-001](/base.md?version=1#REQ-BASE-001)

See [REQ-BASE-001](/base.md?version=1#REQ-BASE-001).
"""
    sections = release_report.parse_requirement_sections(content)
    requirement_versions = {"REQ-BASE-001": 2}

    stale = release_report.find_stale_requirement_references(
        sections, requirement_versions
    )

    assert stale == [("REQ-ALPHA-001", "REQ-BASE-001", 1, 2)]


def test_generate_release_report_basic(tmp_path):
    req_content = """
## REQ-BASE-001
SIL: ASIL-B | Sec: false | Version: 2

## REQ-ALPHA-001
SIL: ASIL-B | Sec: false | Version: 1 | Parent: [REQ-BASE-001](/base.md?version=1#REQ-BASE-001)

Uses param [@max_speed](/params.yaml?version=1#max_speed).
"""
    param_content = """
max_speed_v1:
  value: 1
  unit: m/s
  description: max
"""
    trace_json = """
{
  "implements": {
    "src/impl.py": [
      {"req_id": "REQ-ALPHA-001", "version": 1}
    ]
  },
  "verifies": {
    "tests/test_impl.py": [
      {"req_id": "REQ-ALPHA-001", "version": 1}
    ]
  }
}
"""
    req_path = tmp_path / "req.md"
    param_path = tmp_path / "params.yaml"
    trace_path = tmp_path / "trace.json"
    req_path.write_text(req_content)
    param_path.write_text(param_content)
    trace_path.write_text(trace_json)

    report = release_report.generate_release_report(
        requirement_paths=[str(req_path)],
        parameter_paths=[str(param_path)],
        source_trace_paths=[str(trace_path)],
        exemptions_path=None,
        product_name="Demo",
    )

    assert "# Release Readiness Report: Demo" in report
    assert "## Version Consistency" in report
    assert "## TODO Inventory" in report
    assert "## Implementation & Verification Coverage" in report
    assert "```mermaid" in report


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
