#!/usr/bin/env python3
"""Quick fixes for the diagnostics the server produces.

Actions are computed from the document text and its diagnostics, in the
parser's code-point positions; the caller converts the edits to UTF-16.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from fire.lsp.diagnostic import Diagnostic
from fire.lsp.document_parser import (
    Link,
    Position,
    Range,
    Requirement,
    parse_links,
    parse_requirements,
)
from fire.starlark.config_models import DocumentTypeDefinition, FieldDefinition

_VERSION_RE: Final = re.compile(r"version=(\d+)")
_TODO_TEMPLATE: Final = "TODO(KEY-1234)"
_SEPARATOR: Final = " | "


@dataclass(frozen=True)
class Edit:
    range: Range
    new_text: str


@dataclass(frozen=True)
class Action:
    title: str
    edits: tuple[Edit, ...]
    preferred: bool = False


def _touches(diagnostic: Range, selection: Range) -> bool:
    """True if the selection is on a line the diagnostic spans.

    Matching whole lines keeps the fix available with the cursor anywhere on
    the line, as editors such as Neovim only send the cursor position.
    """
    return (
        diagnostic.start.line <= selection.end.line
        and selection.start.line <= diagnostic.end.line
    )


def _within_line(range_: Range, start: int, end: int) -> Range:
    line = range_.start.line
    base = range_.start.character
    return Range(Position(line, base + start), Position(line, base + end))


def _segment(lines: list[str], range_: Range) -> str:
    line = lines[range_.start.line]
    return line[range_.start.character : range_.end.character]


def _stale_edit(lines: list[str], diagnostic: Diagnostic) -> Edit | None:
    latest = (diagnostic.data or {}).get("latest")
    match = _VERSION_RE.search(_segment(lines, diagnostic.range))
    if latest is None or match is None:
        return None
    return Edit(_within_line(diagnostic.range, *match.span(1)), str(latest))


def _stale_actions(
    lines: list[str], diagnostics: list[Diagnostic], selection: Range
) -> list[Action]:
    stale = [d for d in diagnostics if d.code == "FIRE015"]
    actions = []
    for diagnostic in stale:
        edit = _stale_edit(lines, diagnostic)
        if edit and _touches(diagnostic.range, selection):
            latest = diagnostic.data["latest"]
            actions.append(Action(f"Update link to version {latest}", (edit,), True))
    edits = [e for d in stale if (e := _stale_edit(lines, d))]
    if len(edits) > 1 and actions:
        title = f"Update all {len(edits)} stale links in this file"
        actions.append(Action(title, tuple(edits)))
    return actions


def _version_insertion(lines: list[str], link: Link, latest: int) -> Edit:
    segment = _segment(lines, link.url_range)
    anchor = segment.find("#")
    position = len(segment) if anchor < 0 else anchor
    separator = "&" if "?" in segment else "?"
    at = _within_line(link.url_range, position, position)
    return Edit(at, f"{separator}version={latest}")


def _missing_version_actions(
    text: str,
    lines: list[str],
    diagnostics: list[Diagnostic],
    selection: Range,
    latest_version: Callable[[Link], int | None],
) -> list[Action]:
    wanted = [
        d.range
        for d in diagnostics
        if d.code == "FIRE010" and _touches(d.range, selection)
    ]
    actions = []
    for link in parse_links(text):
        latest = latest_version(link) if link.url_range in wanted else None
        if latest is not None:
            edit = _version_insertion(lines, link, latest)
            actions.append(Action(f"Add ?version={latest}", (edit,), True))
    return list(dict.fromkeys(actions))


def _todo_actions(diagnostics: list[Diagnostic], selection: Range) -> list[Action]:
    return [
        Action(
            f"Replace with {_TODO_TEMPLATE}",
            (Edit(d.range, _TODO_TEMPLATE),),
            True,
        )
        for d in diagnostics
        if d.code == "FIRE004" and _touches(d.range, selection)
    ]


def _requirements_by_heading(text: str) -> dict[Range, Requirement]:
    return {r.id_range: r for r in parse_requirements(text)}


def _field_values(field: FieldDefinition) -> list[str]:
    if field.type == "enum":
        return list(field.values or [])
    if field.type == "bool":
        return ["true", "false"]
    return []


def _placeholders(field: FieldDefinition) -> list[str]:
    """Values to offer for a field that has none yet."""
    if field.type == "int":
        return [str(field.min_value or 1)]
    if field.allow_todo:
        return [_TODO_TEMPLATE]
    return _field_values(field)


def _value_actions(
    diagnostics: list[Diagnostic],
    selection: Range,
    fields: dict[str, FieldDefinition],
) -> list[Action]:
    actions = []
    for d in diagnostics:
        field = fields.get((d.data or {}).get("field", ""))
        if d.code != "FIRE005" or field is None or not _touches(d.range, selection):
            continue
        for value in _field_values(field):
            title = f"Change {field.display_name} to {value}"
            actions.append(Action(title, (Edit(d.range, value),)))
    return actions


def _missing_field_actions(
    text: str,
    diagnostics: list[Diagnostic],
    selection: Range,
    fields: dict[str, FieldDefinition],
) -> list[Action]:
    requirements = _requirements_by_heading(text)
    actions = []
    for d in diagnostics:
        field = fields.get((d.data or {}).get("field", ""))
        requirement = requirements.get(d.range)
        if d.code != "FIRE006" or field is None or not requirement:
            continue
        if not requirement.fields or not _touches(d.range, selection):
            continue
        end = requirement.fields[-1].value_range.end
        for value in _placeholders(field):
            new_text = f"{_SEPARATOR}{field.display_name}: {value}"
            title = f"Add {field.display_name}: {value}"
            actions.append(Action(title, (Edit(Range(end, end), new_text),)))
    return actions


def _skeleton(
    doc_type: DocumentTypeDefinition, fields: dict[str, FieldDefinition]
) -> str:
    parts = []
    for name in doc_type.required_fields:
        values = _placeholders(fields[name])
        parts.append(f"{fields[name].display_name}: {values[0] if values else ''}")
    return _SEPARATOR.join(parts)


def _skeleton_actions(
    text: str,
    diagnostics: list[Diagnostic],
    selection: Range,
    doc_type: DocumentTypeDefinition,
    fields: dict[str, FieldDefinition],
) -> list[Action]:
    lines = text.split("\n")
    actions = []
    for d in diagnostics:
        if d.code != "FIRE003" or not _touches(d.range, selection):
            continue
        end = Position(d.range.start.line, len(lines[d.range.start.line].rstrip()))
        new_text = f"\n\n{_skeleton(doc_type, fields)}"
        title = "Insert metadata line"
        actions.append(Action(title, (Edit(Range(end, end), new_text),), True))
    return actions


def code_actions(
    text: str,
    diagnostics: list[Diagnostic],
    selection: Range,
    latest_version: Callable[[Link], int | None],
    doc_type: DocumentTypeDefinition,
    fields: dict[str, FieldDefinition],
) -> list[Action]:
    """Return the quick fixes for the diagnostics that touch *selection*.

    *latest_version* gives the newest version of a link's target, if it
    resolves. *doc_type* and *fields* come from the FIRE configuration.
    """
    lines = text.split("\n")
    return [
        *_stale_actions(lines, diagnostics, selection),
        *_missing_version_actions(text, lines, diagnostics, selection, latest_version),
        *_todo_actions(diagnostics, selection),
        *_skeleton_actions(text, diagnostics, selection, doc_type, fields),
        *_missing_field_actions(text, diagnostics, selection, fields),
        *_value_actions(diagnostics, selection, fields),
    ]
