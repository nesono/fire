#!/usr/bin/env python3
"""Tests for outline symbols of requirement and parameter files."""

import pytest
from lsprotocol import types as lsp

from fire.lsp.document_parser import Position, Range
from fire.lsp.symbols import parameter_symbols, requirement_symbols

_REQS = """# Title

## REQ-A

SIL: ASIL-D | Sec: false | Version: 4 | Parent: [P](/p.md?version=1#P)

Text of A.

---

## REQ-B

Version: 2

Text of B.

"""

_PARAMS = """# Comment
max_speed_v1:
  value: 30.0
  unit: m/s

max_speed_v2:
  value: 35.0
  unit: m/s
wheel_count_v1:
  value: 4
"""


class TestRequirementSymbols:
    def test_names_and_selection_ranges(self):
        a, b = requirement_symbols(_REQS)
        assert (a.name, b.name) == ("REQ-A", "REQ-B")
        assert a.selection_range == Range(Position(2, 3), Position(2, 8))

    def test_range_runs_to_the_last_line_before_the_next_requirement(self):
        a, b = requirement_symbols(_REQS)
        assert a.range == Range(Position(2, 0), Position(8, 3))
        assert b.range == Range(Position(10, 0), Position(14, 10))

    def test_detail_lists_metadata_without_parent_links(self):
        a, b = requirement_symbols(_REQS)
        assert a.detail == "SIL: ASIL-D | Sec: false | Version: 4"
        assert b.detail == "Version: 2"

    def test_requirement_without_metadata_has_empty_detail(self):
        (symbol,) = requirement_symbols("## R-1\n\nText.\n")
        assert symbol.detail == ""

    def test_kind(self):
        assert requirement_symbols("## R-1\n")[0].kind == lsp.SymbolKind.Key

    def test_headings_in_code_fences_are_not_symbols(self):
        text = "```\n## FAKE\n```\n\n## REAL\n"
        assert [s.name for s in requirement_symbols(text)] == ["REAL"]

    def test_no_requirements(self):
        assert requirement_symbols("# Only a title\n") == []


class TestParameterSymbols:
    def test_one_symbol_per_version_key_in_file_order(self):
        names = [s.name for s in parameter_symbols(_PARAMS)]
        assert names == ["max_speed_v1", "max_speed_v2", "wheel_count_v1"]

    def test_selection_range_is_the_key(self):
        first = parameter_symbols(_PARAMS)[0]
        assert first.selection_range == Range(Position(1, 0), Position(1, 12))

    def test_range_covers_the_entry_but_not_trailing_blank_lines(self):
        first, second, third = parameter_symbols(_PARAMS)
        assert first.range == Range(Position(1, 0), Position(3, 11))
        assert second.range == Range(Position(5, 0), Position(7, 11))
        assert third.range == Range(Position(8, 0), Position(9, 10))

    def test_kind(self):
        assert parameter_symbols("a_v1:\n")[0].kind == lsp.SymbolKind.Constant

    def test_no_parameters(self):
        assert parameter_symbols("# nothing\n") == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
