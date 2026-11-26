#!/usr/bin/env python3
"""Validate requirement metadata against a config-built Pydantic model.

The same models validate documents at build time. Their errors only name the
field, so this module maps each error back to the range of the offending text.
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails

from fire.lsp.diagnostic import Diagnostic, error
from fire.lsp.document_parser import MetadataField, Requirement
from fire.starlark import markdown_common, metadata_parsing
from fire.starlark.pydantic_tools import format_validation_errors

_SEPARATOR = " | "


def _frontmatter(requirement: Requirement) -> dict:
    line = _SEPARATOR.join(f"{f.key}: {f.value}" for f in requirement.fields)
    return metadata_parsing.parse_metadata_fields(line, requirement.id)


def _fields_named(requirement: Requirement, name: str) -> list[MetadataField]:
    return [f for f in requirement.fields if f.key.lower() == name]


def _parent_diagnostics(requirement: Requirement) -> list[Diagnostic]:
    diagnostics = []
    for parent in _fields_named(requirement, "parent"):
        try:
            markdown_common.validate_parent_link(parent.value)
        except ValueError as exc:
            diagnostics.append(error(parent.value_range, "FIRE008", str(exc)))
    return diagnostics


def _diagnostics_for_error(
    requirement: Requirement, err: ErrorDetails, message: str
) -> list[Diagnostic]:
    name = str(err["loc"][0])
    if err["type"] == "missing":
        data = {"field": name}
        return [error(requirement.id_range, "FIRE006", message, data)]
    fields = _fields_named(requirement, name)
    if err["type"] == "extra_forbidden":
        return [error(f.key_range, "FIRE007", message) for f in fields]
    if name == "parent":
        return _parent_diagnostics(requirement)
    data = {"field": name}
    return [error(f.value_range, "FIRE005", message, data) for f in fields[-1:]]


def diagnose_fields(
    requirement: Requirement, model: type[BaseModel]
) -> list[Diagnostic]:
    """Return diagnostics for *requirement*'s metadata under *model*."""
    try:
        model.model_validate(_frontmatter(requirement))
    except ValidationError as exc:
        messages = format_validation_errors(exc)
        return [
            diagnostic
            for err, message in zip(exc.errors(), messages)
            for diagnostic in _diagnostics_for_error(requirement, err, message)
        ]
    return []
