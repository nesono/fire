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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
