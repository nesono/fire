#!/usr/bin/env python3
"""Tests for matching and ranking workspace symbols by query."""

import pytest
from lsprotocol import types as lsp

from fire.lsp.symbol_search import search_symbols
from fire.lsp.workspace_index import IndexedSymbol

_RANGE = lsp.Range(lsp.Position(0, 0), lsp.Position(0, 1))


def _symbol(name: str) -> IndexedSymbol:
    location = lsp.Location(uri="file:///x", range=_RANGE)
    return IndexedSymbol(name, lsp.SymbolKind.Key, location, "x.md")


_SYMBOLS = [
    _symbol(n)
    for n in ("REQ-BRK-001", "REQ-VEL-001", "max_speed_v1", "BRK_HELPER", "speed_v1")
]


def _names(query: str, limit: int = 100) -> list[str]:
    return [s.name for s in search_symbols(_SYMBOLS, query, limit)]


class TestSearchSymbols:
    def test_empty_query_returns_everything_in_order(self):
        assert _names("") == [s.name for s in _SYMBOLS]

    def test_match_is_case_insensitive(self):
        assert _names("brk") == ["BRK_HELPER", "REQ-BRK-001"]

    def test_prefix_matches_rank_before_substring_matches(self):
        assert _names("speed") == ["speed_v1", "max_speed_v1"]

    def test_subsequence_matches_rank_last(self):
        assert _names("rbk1") == ["REQ-BRK-001"]
        assert _names("v1")[:2] == ["max_speed_v1", "speed_v1"]

    def test_no_match(self):
        assert _names("zzz") == []

    def test_limit(self):
        assert len(_names("", limit=2)) == 2

    def test_surrounding_whitespace_is_ignored(self):
        assert _names("  brk ") == _names("brk")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
