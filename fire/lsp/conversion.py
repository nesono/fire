#!/usr/bin/env python3
"""Convert FIRE diagnostics to Language Server Protocol diagnostics."""

from __future__ import annotations

from typing import Final

from lsprotocol import types as lsp

from fire.lsp.diagnostic import Diagnostic, Severity
from fire.lsp.document_parser import Position

_SOURCE: Final = "fire"
_SEVERITIES: Final = {
    Severity.ERROR: lsp.DiagnosticSeverity.Error,
    Severity.WARNING: lsp.DiagnosticSeverity.Warning,
    Severity.INFORMATION: lsp.DiagnosticSeverity.Information,
    Severity.HINT: lsp.DiagnosticSeverity.Hint,
}


def _utf16_column(lines: list[str], position: Position) -> int:
    """LSP columns are UTF-16 code units; the parser counts code points."""
    if position.line >= len(lines):
        return position.character
    prefix = lines[position.line][: position.character]
    return len(prefix.encode("utf-16-le")) // 2


def _position(lines: list[str], position: Position) -> lsp.Position:
    return lsp.Position(position.line, _utf16_column(lines, position))


def to_lsp_diagnostic(diagnostic: Diagnostic, lines: list[str]) -> lsp.Diagnostic:
    return lsp.Diagnostic(
        range=lsp.Range(
            _position(lines, diagnostic.range.start),
            _position(lines, diagnostic.range.end),
        ),
        message=diagnostic.message,
        severity=_SEVERITIES[diagnostic.severity],
        code=diagnostic.code,
        source=_SOURCE,
    )
