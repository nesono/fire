#!/usr/bin/env python3
"""Tests for requirement-file diagnostics."""

import pytest

from fire.lsp.diagnostics import Severity, diagnose_requirements
from fire.lsp.document_parser import Position, Range


def _codes(text: str) -> list[str]:
    return [d.code for d in diagnose_requirements(text)]


_VALID = "## REQ-1\n\nSIL: QM | Sec: false | Version: 1\n\nText.\n"


class TestRequirementDiagnostics:
    def test_valid_document_has_no_diagnostics(self):
        assert diagnose_requirements(_VALID) == []

    def test_invalid_requirement_id(self):
        (diag,) = diagnose_requirements("## req-lower\n\nVersion: 1\n")
        assert diag.code == "FIRE001"
        assert diag.severity == Severity.ERROR
        assert diag.range == Range(Position(0, 3), Position(0, 12))
        assert "req-lower" in diag.message

    def test_duplicate_requirement_id_flags_later_heading(self):
        text = _VALID + "\n---\n\n" + _VALID
        (diag,) = diagnose_requirements(text)
        assert diag.code == "FIRE002"
        assert diag.range.start.line == 8
        assert "REQ-1" in diag.message

    def test_missing_metadata(self):
        (diag,) = diagnose_requirements("## REQ-1\n\nJust text.\n")
        assert diag.code == "FIRE003"
        assert diag.range.start.line == 0

    def test_invalid_id_does_not_also_report_missing_metadata(self):
        assert _codes("## bad id\n\nText.\n") == ["FIRE001"]

    def test_bare_todo(self):
        diags = diagnose_requirements(_VALID + "TODO fix\n")
        assert [d.code for d in diags] == ["FIRE004"]
        assert diags[0].range.start.line == 5

    def test_valid_todo_is_not_reported(self):
        assert diagnose_requirements(_VALID + "TODO(BRK-1) later\n") == []

    def test_diagnostics_are_sorted_by_position(self):
        text = "TODO x\n\n## bad\n"
        lines = [d.range.start.line for d in diagnose_requirements(text)]
        assert lines == sorted(lines)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
