#!/usr/bin/env python3
"""Completion candidates for requirement documents.

Candidates are computed from text and a cursor position, in code points, and
carry the range they replace. Converting to the protocol (UTF-16 columns) is
left to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from lsprotocol import types as lsp

from fire.lsp.document_parser import (
    MetadataField,
    Position,
    Range,
    Requirement,
    parse_requirements,
)
from fire.starlark import metadata_parsing
from fire.starlark.config_models import DocumentTypeDefinition, FieldDefinition

_SEPARATOR: Final = "|"
_TODO_LABEL: Final = "TODO(…)"
_TODO_SNIPPET: Final = "TODO(${1:KEY}-${2:1234})"


@dataclass(frozen=True)
class Candidate:
    label: str
    new_text: str
    replace: Range
    kind: lsp.CompletionItemKind
    detail: str = ""
    documentation: str = ""
    sort_text: str | None = None
    snippet: bool = False
    filter_text: str | None = None


def _owning_requirement(
    requirements: list[Requirement], line: int
) -> Requirement | None:
    before = [r for r in requirements if r.id_range.start.line < line]
    return before[-1] if before else None


def _is_metadata_position(
    lines: list[str], heading: int, line: int, known_fields: list[str]
) -> bool:
    """True if *line* is where the metadata of the requirement at *heading* goes."""
    first = next((i for i in range(heading + 1, line + 1) if lines[i].strip()), None)
    if first is None or first == line:
        return True
    if not metadata_parsing.is_metadata_line(lines[first].strip(), known_fields):
        return False
    return all(lines[i].rstrip().endswith(_SEPARATOR) for i in range(first, line))


def _segment(before: str) -> tuple[int, str]:
    """The field being typed: its start column and text, without leading spaces."""
    start = before.rfind(_SEPARATOR) + 1
    segment = before[start:]
    stripped = segment.lstrip()
    return start + len(segment) - len(stripped), stripped


def _cursor_in(field: MetadataField, position: Position) -> bool:
    start, end = field.key_range.start, field.value_range.end
    return (
        start.line == position.line
        and start.character <= position.character <= end.character
    )


def _used_keys(requirement: Requirement, position: Position) -> set[str]:
    return {f.key.lower() for f in requirement.fields if not _cursor_in(f, position)}


def _key_candidates(
    doc_type: DocumentTypeDefinition,
    fields: dict[str, FieldDefinition],
    used: set[str],
    replace: Range,
) -> list[Candidate]:
    required = set(doc_type.required_fields)
    names = [*doc_type.required_fields, *doc_type.optional_fields]
    return [
        Candidate(
            label=fields[name].display_name,
            new_text=f"{fields[name].display_name}: ",
            replace=replace,
            kind=lsp.CompletionItemKind.Property,
            detail="required" if name in required else "optional",
            documentation=fields[name].description,
            sort_text=f"{name not in required:d}{index:03d}",
        )
        for index, name in enumerate(names)
        if fields[name].display_name.lower() not in used
    ]


def _value_candidates(field: FieldDefinition, replace: Range) -> list[Candidate]:
    if field.type == "enum":
        kind, values = lsp.CompletionItemKind.EnumMember, field.values or []
    elif field.type == "bool":
        kind, values = lsp.CompletionItemKind.Value, ["true", "false"]
    else:
        kind, values = lsp.CompletionItemKind.Value, []
    candidates = [
        Candidate(v, v, replace, kind, detail=field.display_name) for v in values
    ]
    if field.allow_todo:
        candidates.append(
            Candidate(
                _TODO_LABEL,
                _TODO_SNIPPET,
                replace,
                lsp.CompletionItemKind.Snippet,
                detail="placeholder for a ticket",
                snippet=True,
            )
        )
    return candidates


def _line_range(line: int, start: int, end: int) -> Range:
    return Range(Position(line, start), Position(line, end))


def metadata_candidates(
    text: str,
    position: Position,
    doc_type: DocumentTypeDefinition,
    fields: dict[str, FieldDefinition],
) -> list[Candidate]:
    """Complete the metadata line of a requirement: field names, then values."""
    lines = text.split("\n")
    requirement = _owning_requirement(parse_requirements(text), position.line)
    known = [f.display_name.lower() for f in fields.values()]
    if requirement is None or not _is_metadata_position(
        lines, requirement.id_range.start.line, position.line, known
    ):
        return []
    column, segment = _segment(lines[position.line][: position.character])
    if ":" not in segment:
        replace = _line_range(position.line, column, position.character)
        used = _used_keys(requirement, position)
        return _key_candidates(doc_type, fields, used, replace)
    key, _, value = segment.partition(":")
    value_column = column + len(key) + 1 + len(value) - len(value.lstrip())
    allowed = {
        fields[n].display_name.lower(): fields[n]
        for n in [*doc_type.required_fields, *doc_type.optional_fields]
    }
    field = allowed.get(key.strip().lower())
    replace = _line_range(position.line, value_column, position.character)
    return _value_candidates(field, replace) if field else []
