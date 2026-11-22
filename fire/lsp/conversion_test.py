#!/usr/bin/env python3
"""Tests for converting FIRE diagnostics to LSP diagnostics."""

import pytest
from lsprotocol import types as lsp

from fire.lsp.conversion import to_lsp_diagnostic
from fire.lsp.diagnostic import Diagnostic, Severity
from fire.lsp.document_parser import Position, Range


def _diag(line: int, start: int, end: int) -> Diagnostic:
    rng = Range(Position(line, start), Position(line, end))
    return Diagnostic(rng, Severity.WARNING, "FIRE999", "message")


class TestToLspDiagnostic:
    def test_fields_are_carried_over(self):
        result = to_lsp_diagnostic(_diag(1, 2, 5), ["", "abcdefg"])
        assert result.code == "FIRE999"
        assert result.message == "message"
        assert result.source == "fire"
        assert result.severity == lsp.DiagnosticSeverity.Warning

    def test_range_for_ascii_text(self):
        result = to_lsp_diagnostic(_diag(1, 2, 5), ["", "abcdefg"])
        assert result.range == lsp.Range(lsp.Position(1, 2), lsp.Position(1, 5))

    def test_columns_are_utf16_code_units(self):
        lines = ["😀 abc"]
        result = to_lsp_diagnostic(_diag(0, 2, 5), lines)
        assert result.range.start.character == 3
        assert result.range.end.character == 6

    def test_bmp_characters_count_once(self):
        result = to_lsp_diagnostic(_diag(0, 2, 3), ["±5 x"])
        assert result.range.start.character == 2

    def test_range_past_known_lines_is_kept(self):
        result = to_lsp_diagnostic(_diag(3, 0, 1), ["only"])
        assert result.range.start == lsp.Position(3, 0)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
