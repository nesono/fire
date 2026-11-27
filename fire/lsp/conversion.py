#!/usr/bin/env python3
"""Convert FIRE diagnostics to Language Server Protocol diagnostics."""

from __future__ import annotations

from typing import Final

from lsprotocol import types as lsp

from fire.lsp.diagnostic import Diagnostic, Severity
from fire.lsp.code_actions import Action
from fire.lsp.completion import Candidate
from fire.lsp.document_parser import Position, Range
from fire.lsp.symbols import Symbol

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


def to_lsp_range(range_: Range, lines: list[str]) -> lsp.Range:
    return lsp.Range(_position(lines, range_.start), _position(lines, range_.end))


def _code_point_column(line: str, utf16_column: int) -> int:
    units = 0
    for index, char in enumerate(line):
        units += 2 if ord(char) > 0xFFFF else 1
        if units > utf16_column:
            return index
    return len(line)


def from_lsp_position(position: lsp.Position, lines: list[str]) -> Position:
    """Convert a UTF-16 LSP position to the parser's code-point position."""
    if position.line >= len(lines):
        return Position(position.line, position.character)
    column = _code_point_column(lines[position.line], position.character)
    return Position(position.line, column)


def to_lsp_diagnostic(diagnostic: Diagnostic, lines: list[str]) -> lsp.Diagnostic:
    return lsp.Diagnostic(
        range=to_lsp_range(diagnostic.range, lines),
        message=diagnostic.message,
        severity=_SEVERITIES[diagnostic.severity],
        code=diagnostic.code,
        source=_SOURCE,
        data=diagnostic.data,
    )


def to_lsp_symbol(symbol: Symbol, lines: list[str]) -> lsp.DocumentSymbol:
    return lsp.DocumentSymbol(
        name=symbol.name,
        kind=symbol.kind,
        range=to_lsp_range(symbol.range, lines),
        selection_range=to_lsp_range(symbol.selection_range, lines),
        detail=symbol.detail or None,
    )


def to_lsp_completion_item(
    candidate: Candidate, lines: list[str]
) -> lsp.CompletionItem:
    snippet = candidate.snippet
    return lsp.CompletionItem(
        label=candidate.label,
        kind=candidate.kind,
        detail=candidate.detail or None,
        documentation=candidate.documentation or None,
        sort_text=candidate.sort_text,
        filter_text=candidate.filter_text,
        text_edit=lsp.TextEdit(
            to_lsp_range(candidate.replace, lines), candidate.new_text
        ),
        insert_text_format=(
            lsp.InsertTextFormat.Snippet if snippet else lsp.InsertTextFormat.PlainText
        ),
    )


def to_lsp_code_action(action: Action, uri: str, lines: list[str]) -> lsp.CodeAction:
    edits = [
        lsp.TextEdit(to_lsp_range(edit.range, lines), edit.new_text)
        for edit in action.edits
    ]
    return lsp.CodeAction(
        title=action.title,
        kind=(
            lsp.CodeActionKind.RefactorRewrite
            if action.refactor
            else lsp.CodeActionKind.QuickFix
        ),
        is_preferred=action.preferred or None,
        edit=lsp.WorkspaceEdit(changes={uri: edits}),
    )
