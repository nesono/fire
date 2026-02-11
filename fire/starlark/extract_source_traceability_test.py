"""Tests for fire/starlark/extract_source_traceability.py"""

import sys

import pytest

from fire.starlark import extract_source_traceability


class TestParseVersionedReq:
    """Tests for parse_versioned_req function."""

    def test_with_version(self):
        req_id, version = extract_source_traceability.parse_versioned_req(
            "REQ_BC_FORCE?version=1"
        )
        assert req_id == "REQ_BC_FORCE"
        assert version == 1

    def test_without_version(self):
        req_id, version = extract_source_traceability.parse_versioned_req(
            "REQ_BC_FORCE"
        )
        assert req_id == "REQ_BC_FORCE"
        assert version is None

    def test_higher_version(self):
        req_id, version = extract_source_traceability.parse_versioned_req(
            "REQ-VEL-001?version=42"
        )
        assert req_id == "REQ-VEL-001"
        assert version == 42

    def test_empty_query(self):
        req_id, version = extract_source_traceability.parse_versioned_req(
            "REQ_BC_FORCE?"
        )
        assert req_id == "REQ_BC_FORCE"
        assert version is None


class TestExtractRequirementsFromFile:
    """Tests for extract_requirements_from_file function."""

    def test_single_requirement(self, tmp_path):
        req_file = tmp_path / "REQ-001.md"
        req_file.write_text(
            "# Speed Limit\n\n"
            "## REQ-001\n\n"
            "SIL: ASIL-B | Sec: False | Version: 1\n\n"
            "Description.\n"
        )
        req_map, error = extract_source_traceability.extract_requirements_from_file(
            str(req_file)
        )
        assert error is None
        assert req_map == {"REQ-001": 1}

    def test_multiple_requirements(self, tmp_path):
        req_file = tmp_path / "reqs.md"
        req_file.write_text(
            "## REQ-A\n\n"
            "SIL: ASIL-B | Sec: False | Version: 1\n\n"
            "First.\n\n"
            "## REQ-B\n\n"
            "SIL: ASIL-C | Sec: False | Version: 2\n\n"
            "Second.\n"
        )
        req_map, error = extract_source_traceability.extract_requirements_from_file(
            str(req_file)
        )
        assert error is None
        assert req_map == {"REQ-A": 1, "REQ-B": 2}

    def test_nonexistent_file(self):
        req_map, error = extract_source_traceability.extract_requirements_from_file(
            "/nonexistent/file.md"
        )
        assert req_map == {}
        assert error is not None

    def test_file_with_no_requirements(self, tmp_path):
        req_file = tmp_path / "empty.md"
        req_file.write_text("# Just a document\n\nNo requirements here.\n")
        req_map, error = extract_source_traceability.extract_requirements_from_file(
            str(req_file)
        )
        assert error is None
        assert req_map == {}

    def test_requirement_without_metadata(self, tmp_path):
        req_file = tmp_path / "REQ-001.md"
        req_file.write_text("## REQ-001\n\nNo metadata line.\n")
        req_map, error = extract_source_traceability.extract_requirements_from_file(
            str(req_file)
        )
        assert error is None
        assert req_map == {"REQ-001": None}


class TestValidateMapping:
    """Tests for validate_mapping function."""

    def test_valid_mapping(self):
        mapping = {"src/foo.cc": ["REQ-001?version=1"]}
        available = {"REQ-001": 1}
        output, errors = extract_source_traceability.validate_mapping(
            mapping, available, "implements"
        )
        assert errors == []
        assert output == {"src/foo.cc": [{"req_id": "REQ-001", "version": 1}]}

    def test_unknown_requirement(self):
        mapping = {"src/foo.cc": ["REQ-MISSING?version=1"]}
        available = {"REQ-001": 1}
        output, errors = extract_source_traceability.validate_mapping(
            mapping, available, "implements"
        )
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_missing_version(self):
        mapping = {"src/foo.cc": ["REQ-001"]}
        available = {"REQ-001": 1}
        output, errors = extract_source_traceability.validate_mapping(
            mapping, available, "implements"
        )
        assert len(errors) == 1
        assert "missing ?version=" in errors[0]

    def test_future_version_is_error(self):
        mapping = {"src/foo.cc": ["REQ-001?version=5"]}
        available = {"REQ-001": 2}
        output, errors = extract_source_traceability.validate_mapping(
            mapping, available, "implements"
        )
        assert len(errors) == 1
        assert "only at version=2" in errors[0]

    def test_outdated_version_is_warning_not_error(self, capsys):
        mapping = {"src/foo.cc": ["REQ-001?version=1"]}
        available = {"REQ-001": 3}
        output, errors = extract_source_traceability.validate_mapping(
            mapping, available, "implements"
        )
        assert errors == []
        assert output == {"src/foo.cc": [{"req_id": "REQ-001", "version": 1}]}
        captured = capsys.readouterr()
        assert "OUTDATED" in captured.out

    def test_multiple_refs_per_file(self):
        mapping = {"src/foo.cc": ["REQ-A?version=1", "REQ-B?version=2"]}
        available = {"REQ-A": 1, "REQ-B": 2}
        output, errors = extract_source_traceability.validate_mapping(
            mapping, available, "verifies"
        )
        assert errors == []
        assert len(output["src/foo.cc"]) == 2

    def test_multiple_files(self):
        mapping = {
            "src/a.cc": ["REQ-A?version=1"],
            "src/b.cc": ["REQ-B?version=1"],
        }
        available = {"REQ-A": 1, "REQ-B": 1}
        output, errors = extract_source_traceability.validate_mapping(
            mapping, available, "implements"
        )
        assert errors == []
        assert "src/a.cc" in output
        assert "src/b.cc" in output


class TestBuildTraceOutput:
    """Tests for build_trace_output function."""

    def test_empty(self):
        result = extract_source_traceability.build_trace_output({}, {})
        assert result == {}

    def test_implements_only(self):
        impl = {"src/foo.cc": [{"req_id": "REQ-001", "version": 1}]}
        result = extract_source_traceability.build_trace_output(impl, {})
        assert result == {"implements": impl}
        assert "verifies" not in result

    def test_verifies_only(self):
        ver = {"test/foo_test.cc": [{"req_id": "REQ-001", "version": 1}]}
        result = extract_source_traceability.build_trace_output({}, ver)
        assert result == {"verifies": ver}
        assert "implements" not in result

    def test_both(self):
        impl = {"src/foo.cc": [{"req_id": "REQ-001", "version": 1}]}
        ver = {"test/foo_test.cc": [{"req_id": "REQ-001", "version": 1}]}
        result = extract_source_traceability.build_trace_output(impl, ver)
        assert result == {"implements": impl, "verifies": ver}


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
