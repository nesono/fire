#!/usr/bin/env python3
"""Turn parsed requirement documents into editor diagnostics.

Rule codes are stable identifiers (``FIREnnn``) so editors and, later, the
build-time validators can refer to the same rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from fire.lsp import document_parser
from fire.lsp.document_parser import Range, Requirement
from fire.starlark import patterns


class Severity(IntEnum):
    """Severity values as defined by the Language Server Protocol."""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass(frozen=True)
class Diagnostic:
    range: Range
    severity: Severity
    code: str
    message: str


def _error(range_: Range, code: str, message: str) -> Diagnostic:
    return Diagnostic(range_, Severity.ERROR, code, message)


def _heading_diagnostics(requirement: Requirement, seen: set[str]) -> list[Diagnostic]:
    if not patterns.REQ_ID_PATTERN.match(requirement.id):
        return [
            _error(
                requirement.id_range,
                "FIRE001",
                f"'{requirement.id}' is not a valid requirement ID "
                "(expected [A-Z][A-Z0-9_-]+)",
            )
        ]
    if requirement.id in seen:
        return [
            _error(
                requirement.id_range,
                "FIRE002",
                f"Duplicate requirement ID '{requirement.id}'",
            )
        ]
    seen.add(requirement.id)
    if not requirement.fields:
        return [
            _error(
                requirement.id_range,
                "FIRE003",
                f"Requirement '{requirement.id}' has no metadata line",
            )
        ]
    return []


def _todo_diagnostics(text: str) -> list[Diagnostic]:
    return [
        _error(
            todo.range,
            "FIRE004",
            f"Bare or malformed TODO '{todo.text}'. Must use format TODO(KEY-1234)",
        )
        for todo in document_parser.parse_todos(text)
        if not todo.valid
    ]


def diagnose_requirements(text: str) -> list[Diagnostic]:
    """Return diagnostics for a requirement document, ordered by position."""
    seen: set[str] = set()
    diagnostics = _todo_diagnostics(text)
    for requirement in document_parser.parse_requirements(text):
        diagnostics.extend(_heading_diagnostics(requirement, seen))
    return sorted(
        diagnostics, key=lambda d: (d.range.start.line, d.range.start.character)
    )
