#!/usr/bin/env python3
"""Match and rank workspace symbols against a search query."""

from __future__ import annotations

from collections.abc import Iterable

from fire.lsp.workspace_index import IndexedSymbol

_PREFIX, _SUBSTRING, _SUBSEQUENCE = range(3)


def _rank(name: str, query: str) -> int | None:
    """Lower is better; ``None`` means no match."""
    if name.startswith(query):
        return _PREFIX
    if query in name:
        return _SUBSTRING
    remaining = iter(name)
    if all(char in remaining for char in query):
        return _SUBSEQUENCE
    return None


def search_symbols(
    symbols: Iterable[IndexedSymbol], query: str, limit: int
) -> list[IndexedSymbol]:
    """Return up to *limit* symbols matching *query*, best matches first.

    Matching is case-insensitive: prefix matches rank before substring matches,
    which rank before in-order character matches. Ties keep their input order.
    """
    needle = query.strip().lower()
    ranked = [(_rank(s.name.lower(), needle), s) for s in symbols]
    matches = sorted(((r, s) for r, s in ranked if r is not None), key=lambda m: m[0])
    return [symbol for _, symbol in matches[:limit]]
