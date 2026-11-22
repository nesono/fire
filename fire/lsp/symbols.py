#!/usr/bin/env python3
"""Outline symbols for requirement files and parameter files."""

from __future__ import annotations

from dataclasses import dataclass

from lsprotocol import types as lsp

from fire.lsp.document_parser import Position, Range, parse_requirements
from fire.lsp.index import parameters_in


@dataclass(frozen=True)
class Symbol:
    name: str
    detail: str
    kind: lsp.SymbolKind
    range: Range
    selection_range: Range


def _block_range(lines: list[str], start: int, next_start: int) -> Range:
    """Span from line *start* to the last non-blank line before *next_start*."""
    end = next_start - 1
    while end > start and not lines[end].strip():
        end -= 1
    return Range(Position(start, 0), Position(end, len(lines[end])))


def requirement_symbols(text: str) -> list[Symbol]:
    """One symbol per requirement heading, spanning its whole section."""
    lines = text.split("\n")
    requirements = parse_requirements(text)
    starts = [r.id_range.start.line for r in requirements] + [len(lines)]
    return [
        Symbol(
            name=requirement.id,
            detail=" | ".join(
                f"{f.key}: {f.value}"
                for f in requirement.fields
                if f.key.lower() != "parent"
            ),
            kind=lsp.SymbolKind.Key,
            range=_block_range(lines, starts[index], starts[index + 1]),
            selection_range=requirement.id_range,
        )
        for index, requirement in enumerate(requirements)
    ]


def parameter_symbols(text: str) -> list[Symbol]:
    """One symbol per ``name_vN`` key, in file order."""
    lines = text.split("\n")
    keys = sorted(
        (rng.start.line, f"{info.name}_v{version}", rng)
        for info in parameters_in(text).values()
        for version, rng in info.versions.items()
    )
    starts = [line for line, _, _ in keys] + [len(lines)]
    return [
        Symbol(
            name=name,
            detail="",
            kind=lsp.SymbolKind.Constant,
            range=_block_range(lines, starts[index], starts[index + 1]),
            selection_range=key_range,
        )
        for index, (_, name, key_range) in enumerate(keys)
    ]
