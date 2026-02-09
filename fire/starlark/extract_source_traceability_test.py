"""Tests for fire/starlark/extract_source_traceability.py"""

import sys

import pytest

from fire.starlark import extract_source_traceability


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
        reqs, error = extract_source_traceability.extract_requirements_from_file(
            str(req_file)
        )
        assert error is None
        assert len(reqs) == 1
        assert reqs[0]["req_id"] == "REQ-001"
        assert reqs[0]["path"] == str(req_file)
        assert reqs[0]["version"] == 1

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
        reqs, error = extract_source_traceability.extract_requirements_from_file(
            str(req_file)
        )
        assert error is None
        assert len(reqs) == 2
        assert reqs[0]["req_id"] == "REQ-A"
        assert reqs[0]["version"] == 1
        assert reqs[1]["req_id"] == "REQ-B"
        assert reqs[1]["version"] == 2

    def test_nonexistent_file(self):
        reqs, error = extract_source_traceability.extract_requirements_from_file(
            "/nonexistent/file.md"
        )
        assert reqs == []
        assert error is not None

    def test_file_with_no_requirements(self, tmp_path):
        req_file = tmp_path / "empty.md"
        req_file.write_text("# Just a document\n\nNo requirements here.\n")
        reqs, error = extract_source_traceability.extract_requirements_from_file(
            str(req_file)
        )
        assert error is None
        assert reqs == []

    def test_requirement_without_metadata(self, tmp_path):
        req_file = tmp_path / "REQ-001.md"
        req_file.write_text("## REQ-001\n\nNo metadata line.\n")
        reqs, error = extract_source_traceability.extract_requirements_from_file(
            str(req_file)
        )
        assert error is None
        assert len(reqs) == 1
        assert reqs[0]["req_id"] == "REQ-001"
        assert "version" not in reqs[0]


class TestBuildTraceOutput:
    """Tests for build_trace_output function."""

    def test_empty(self):
        result = extract_source_traceability.build_trace_output([], [])
        assert result == {"sources": {}}

    def test_single_source_single_requirement(self):
        reqs = [{"req_id": "REQ-001", "path": "req.md", "version": 1}]
        result = extract_source_traceability.build_trace_output(["src/foo.cc"], reqs)
        assert result == {
            "sources": {
                "src/foo.cc": [{"req_id": "REQ-001", "path": "req.md", "version": 1}]
            }
        }

    def test_multiple_sources_share_requirements(self):
        reqs = [{"req_id": "REQ-001", "path": "req.md", "version": 1}]
        result = extract_source_traceability.build_trace_output(
            ["src/foo.cc", "src/foo_test.py"], reqs
        )
        assert "src/foo.cc" in result["sources"]
        assert "src/foo_test.py" in result["sources"]
        assert result["sources"]["src/foo.cc"] == result["sources"]["src/foo_test.py"]

    def test_sources_get_independent_copies(self):
        """Verify each source gets its own list (not shared reference)."""
        reqs = [{"req_id": "REQ-001", "path": "req.md", "version": 1}]
        result = extract_source_traceability.build_trace_output(["a.cc", "b.cc"], reqs)
        result["sources"]["a.cc"].append({"req_id": "EXTRA"})
        assert len(result["sources"]["b.cc"]) == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
