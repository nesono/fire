#!/usr/bin/env python3
"""Tests for converting FIRE diagnostics to LSP diagnostics."""

import pytest
from lsprotocol import types as lsp

from fire.lsp.conversion import from_lsp_position, to_lsp_diagnostic, to_lsp_range
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


class TestToLspRange:
    def test_converts_both_ends(self):
        rng = Range(Position(0, 2), Position(0, 5))
        assert to_lsp_range(rng, ["😀 abc"]) == lsp.Range(
            lsp.Position(0, 3), lsp.Position(0, 6)
        )


class TestFromLspPosition:
    def test_ascii_is_unchanged(self):
        assert from_lsp_position(lsp.Position(0, 3), ["abcdef"]) == Position(0, 3)

    def test_utf16_columns_become_code_points(self):
        assert from_lsp_position(lsp.Position(0, 3), ["😀 abc"]) == Position(0, 2)

    def test_column_inside_a_surrogate_pair_rounds_down(self):
        assert from_lsp_position(lsp.Position(0, 1), ["😀 abc"]) == Position(0, 0)

    def test_column_past_the_end_is_clamped(self):
        assert from_lsp_position(lsp.Position(0, 99), ["abc"]) == Position(0, 3)

    def test_unknown_line_is_kept(self):
        assert from_lsp_position(lsp.Position(5, 2), ["abc"]) == Position(5, 2)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
