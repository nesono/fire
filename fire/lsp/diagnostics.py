#!/usr/bin/env python3
"""Turn parsed requirement documents into editor diagnostics.

Rule codes are stable identifiers (``FIREnnn``) so editors and, later, the
build-time validators can refer to the same rules.
"""

from __future__ import annotations

from pydantic import BaseModel

from fire.lsp import document_parser
from fire.lsp.diagnostic import Diagnostic, Severity, error
from fire.lsp.document_parser import Requirement
from fire.lsp.field_diagnostics import diagnose_fields
from fire.starlark import patterns

__all__ = ["Diagnostic", "Severity", "diagnose_requirements"]


def _heading_diagnostics(requirement: Requirement, seen: set[str]) -> list[Diagnostic]:
    if not patterns.REQ_ID_PATTERN.match(requirement.id):
        return [
            error(
                requirement.id_range,
                "FIRE001",
                f"'{requirement.id}' is not a valid requirement ID "
                "(expected [A-Z][A-Z0-9_-]+)",
            )
        ]
    if requirement.id in seen:
        return [
            error(
                requirement.id_range,
                "FIRE002",
                f"Duplicate requirement ID '{requirement.id}'",
            )
        ]
    seen.add(requirement.id)
    if not requirement.fields:
        return [
            error(
                requirement.id_range,
                "FIRE003",
                f"Requirement '{requirement.id}' has no metadata line",
            )
        ]
    return []


def _todo_diagnostics(text: str) -> list[Diagnostic]:
    return [
        error(
            todo.range,
            "FIRE004",
            f"Bare or malformed TODO '{todo.text}'. Must use format TODO(KEY-1234)",
        )
        for todo in document_parser.parse_todos(text)
        if not todo.valid
    ]


def _requirement_diagnostics(
    requirement: Requirement, seen: set[str], model: type[BaseModel] | None
) -> list[Diagnostic]:
    heading = _heading_diagnostics(requirement, seen)
    if heading or model is None or not requirement.fields:
        return heading
    return diagnose_fields(requirement, model)


def diagnose_requirements(
    text: str, model: type[BaseModel] | None = None
) -> list[Diagnostic]:
    """Return diagnostics for a requirement document, ordered by position.

    When *model* is given, each requirement's metadata is validated against it.
    """
    seen: set[str] = set()
    diagnostics = _todo_diagnostics(text)
    for requirement in document_parser.parse_requirements(text):
        diagnostics.extend(_requirement_diagnostics(requirement, seen, model))
    return sorted(
        diagnostics, key=lambda d: (d.range.start.line, d.range.start.character)
    )
