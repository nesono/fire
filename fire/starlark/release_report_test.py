#!/usr/bin/env python3
"""Unit tests for release report draft parsers."""

import pytest

from fire.starlark import release_report


def test_parse_trace_entries_valid():
    data = [
        {"type": "impl", "requirement": "REQ-1", "version": 2},
        {"type": "verif", "param": "max_speed", "source": "tests/test_speed.py"},
    ]
    entries = release_report.parse_trace_entries(data, "trace.yaml")

    assert entries[0]["type"] == "impl"
    assert entries[0]["requirement"] == "REQ-1"
    assert entries[1]["type"] == "verif"
    assert entries[1]["param"] == "max_speed"


def test_parse_trace_entries_rejects_unknown_type():
    data = [{"type": "build", "requirement": "REQ-1"}]
    with pytest.raises(ValueError, match="Unknown trace type"):
        release_report.parse_trace_entries(data, "trace.yaml")


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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
