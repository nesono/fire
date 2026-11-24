#!/usr/bin/env python3
"""Unit tests for release report draft parsers."""

import json

import pytest

from fire.starlark import release_report
from fire.starlark.config_models import FireConfig


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
    sections = release_report.parse_requirement_sections(content, "reqs.md")

    assert [section["id"] for section in sections] == ["REQ-ALPHA-001", "REQ-BETA-002"]
    assert sections[0]["metadata"]["version"] == 2
    assert "parent" in sections[0]["metadata"]


def test_collect_requirement_reference_versions():
    content = """
## REQ-ALPHA-001
SIL: ASIL-B | Sec: false | Version: 2

See [REQ-BASE-001](/base.md?version=1#REQ-BASE-001).
"""
    sections = release_report.parse_requirement_sections(content, "reqs.md")
    refs = release_report.collect_requirement_references(sections[0])

    assert refs == [("REQ-BASE-001", 1, "/base.md?version=1#REQ-BASE-001")]


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
    sections = release_report.parse_requirement_sections(content, "reqs.md")
    requirement_versions = {"REQ-BASE-001": 2}

    stale = release_report.find_stale_requirement_references(
        sections, requirement_versions
    )

    # Both the Parent reference and the body reference are stale (v1 tracked, v2 current)
    assert stale == [
        ("REQ-ALPHA-001", "REQ-BASE-001", 1, 2),
        ("REQ-ALPHA-001", "REQ-BASE-001", 1, 2),
    ]


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
        product_name="Demo",
    )

    assert "# Release Readiness Report: Demo" in report
    assert "## Version Consistency" in report
    assert "## TODO Inventory" in report
    assert "## Coverage" in report
    assert "```mermaid" in report


def _write_requirement(tmp_path, name, req_id, version):
    path = tmp_path / name
    path.write_text(f"## {req_id}\nSIL: QM | Sec: false | Version: {version}\n")
    return str(path)


def test_report_flags_duplicate_requirement_ids(tmp_path):
    first = _write_requirement(tmp_path, "first.md", "REQ-D-001", 1)
    second = _write_requirement(tmp_path, "second.md", "REQ-D-001", 7)

    report = release_report.generate_release_report([first, second], [], [], "Demo")

    assert "**Status: NOT READY FOR RELEASE**" in report
    assert "Duplicate requirement IDs: **1**" in report
    assert "## Requirement ID Uniqueness" in report
    assert "**REQ-D-001**" in report
    assert f"{first}:1" in report
    assert f"{second}:1" in report


def test_report_states_unique_requirement_ids(tmp_path):
    first = _write_requirement(tmp_path, "first.md", "REQ-A-001", 1)
    second = _write_requirement(tmp_path, "second.md", "REQ-B-001", 1)

    report = release_report.generate_release_report([first, second], [], [], "Demo")

    assert "Duplicate requirement IDs" not in report
    assert "- All requirement IDs are unique." in report


def _write_doc(tmp_path, name, req_id, parent=None):
    parent_field = f" | Parent: [{parent}](/{parent}.sysreq.md?version=1#{parent})"
    path = tmp_path / name
    path.write_text(
        f"## {req_id}\n\nSIL: QM | Sec: false | Version: 1"
        f"{parent_field if parent else ''}\n\nBody.\n"
    )
    return str(path)


def _write_trace(tmp_path, implements=(), verifies=()):
    def entries(ids):
        return {f"src/{r}.py": [{"req_id": r, "version": 1}] for r in ids}

    path = tmp_path / "trace.json"
    path.write_text(
        json.dumps({"implements": entries(implements), "verifies": entries(verifies)})
    )
    return str(path)


def _report(paths, traces=(), config=None):
    return release_report.generate_release_report(
        list(paths), [], list(traces), "Demo", config
    )


class TestCoverageByDocumentType:
    def test_system_requirement_needs_a_child_not_traces(self, tmp_path):
        sys_req = _write_doc(tmp_path, "a.sysreq.md", "REQ-SYS-001")
        sw_req = _write_doc(tmp_path, "b.swreq.md", "REQ-SW-001", "REQ-SYS-001")
        trace = _write_trace(tmp_path, ["REQ-SW-001"], ["REQ-SW-001"])

        report = _report([sys_req, sw_req], [trace])

        assert "**Status: READY FOR RELEASE**" in report
        assert "- All requirements meet the coverage required" in report

    def test_system_requirement_without_child_is_reported(self, tmp_path):
        sys_req = _write_doc(tmp_path, "a.sysreq.md", "REQ-SYS-001")

        report = _report([sys_req])

        assert "**Status: NOT READY FOR RELEASE**" in report
        assert "Missing child requirements: **1**" in report
        assert "### Missing Child Requirements" in report
        assert "- [REQ-SYS-001](" in report.split("### Missing Child Requirements")[1]
        assert "Missing implementation traces" not in report

    def test_child_counts_regardless_of_pinned_parent_version(self, tmp_path):
        sys_req = _write_doc(tmp_path, "a.sysreq.md", "REQ-SYS-001")
        path = tmp_path / "b.swreq.md"
        path.write_text(
            "## REQ-SW-001\n\nSIL: QM | Sec: false | Version: 1 | "
            "Parent: [REQ-SYS-001](/a.sysreq.md?version=7#REQ-SYS-001)\n"
        )

        report = _report([sys_req, str(path)])

        assert "Missing child requirements" not in report

    def test_software_requirement_needs_implementation_and_verification(self, tmp_path):
        sw_req = _write_doc(tmp_path, "b.swreq.md", "REQ-SW-001")

        report = _report([sw_req])

        assert "Missing implementation traces: **1**" in report
        assert "Missing verification traces: **1**" in report
        assert "Missing child requirements" not in report

    def test_regulatory_requirement_needs_only_verification(self, tmp_path):
        reg_req = _write_doc(tmp_path, "c.regreq.md", "REQ-REG-001")

        report = _report([reg_req])
        assert "Missing verification traces: **1**" in report
        assert "Missing implementation traces" not in report

        trace = _write_trace(tmp_path, verifies=["REQ-REG-001"])
        assert "**Status: READY FOR RELEASE**" in _report([reg_req], [trace])

    def test_unknown_suffix_keeps_implementation_and_verification(self, tmp_path):
        plain = _write_doc(tmp_path, "notes.md", "REQ-X-001")

        report = _report([plain])

        assert "Missing implementation traces: **1**" in report
        assert "Missing verification traces: **1**" in report

    def test_configured_coverage_replaces_the_default(self, tmp_path):
        config = FireConfig.model_validate(
            {
                "fire_config_version": 1,
                "field_definitions": {
                    "version": {"display_name": "Version", "type": "int"}
                },
                "document_types": {
                    "handbook": {
                        "suffix": ".handbook.md",
                        "display_name": "Handbook",
                        "required_fields": ["version"],
                        "coverage": [],
                    }
                },
            }
        )
        entry = tmp_path / "hb.handbook.md"
        entry.write_text("## HB-001\n\nVersion: 1\n\nBody.\n")

        report = _report([str(entry)], config=config)

        assert "**Status: READY FOR RELEASE**" in report

    def test_report_lists_the_required_coverage_per_document_type(self, tmp_path):
        sys_req = _write_doc(tmp_path, "a.sysreq.md", "REQ-SYS-001")

        report = _report([sys_req])

        assert "### Required Coverage" in report
        assert "- System Requirement (`.sysreq.md`): child" in report
        assert "- Regulatory Requirement (`.regreq.md`): verification" in report


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
