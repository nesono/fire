#!/usr/bin/env python3
"""Completion in parameter YAML files: field names, ``type`` and ``unit``.

The text is scanned by indentation rather than parsed, because a file being
edited is often not valid YAML. Positions are code points.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Final

import yaml
from lsprotocol import types as lsp

from fire.lsp.completion import Candidate
from fire.lsp.document_parser import Position, Range

COMMON_UNITS: Final = (
    "1", "count", "bool", "m", "mm", "km", "m/s", "km/h", "m/s^2", "s", "ms", "Hz",
    "kg", "N", "Pa", "bar", "°C", "V", "A", "W", "rad", "°", "%", "rpm",
)  # fmt: skip
_SCALAR_KEYS: Final = ("value", "unit", "description")
_TABLE_KEYS: Final = ("description", "columns", "rows")
_COLUMN_KEYS: Final = ("name", "unit")
_KEY_RE: Final = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*):")
_KEY_VALUE_RE: Final = re.compile(
    r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*):[ \t]*(?P<typed>[^ \t]*)$"
)
_LIST_MARKER: Final = "- "


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_content(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def _parent(lines: list[str], index: int, indent: int) -> int | None:
    """The nearest line above *index* that is indented less than *indent*."""
    for i in range(index - 1, -1, -1):
        if _is_content(lines[i]) and _indent(lines[i]) < indent:
            return i
    return None


def _key_of(line: str) -> str | None:
    content = line.strip()
    content = (
        content[len(_LIST_MARKER) :] if content.startswith(_LIST_MARKER) else content
    )
    match = _KEY_RE.match(content)
    return match["key"] if match else None


def _block_end(lines: list[str], start: int, indent: int) -> int:
    """The first line after *start* that is not indented more than *indent*."""
    for i in range(start + 1, len(lines)):
        if _is_content(lines[i]) and _indent(lines[i]) <= indent:
            return i
    return len(lines)


def _sibling_keys(lines: list[str], first: int, last: int, skip: int) -> dict[str, str]:
    """Keys of the lines in ``first..last`` (exclusive) with their text, but not *skip*."""
    found: dict[str, str] = {}
    for i in range(first, last):
        key = _key_of(lines[i]) if i != skip else None
        if key and _is_content(lines[i]):
            found[key] = lines[i].split(":", 1)[1].strip()
    return found


def _property(key: str, replace: Range, detail: str, order: int) -> Candidate:
    new_text = f"{key}:" if key in ("columns", "rows") else f"{key}: "
    return Candidate(
        key, new_text, replace, lsp.CompletionItemKind.Property, detail=detail,
        sort_text=f"{order:02d}",
    )  # fmt: skip


def _parameter_keys(
    lines: list[str], index: int, top: int, replace: Range
) -> list[Candidate]:
    end = _block_end(lines, top, 0)
    present = _sibling_keys(lines, top + 1, end, index)
    is_table = present.get("type") == "table"
    keys = list(_TABLE_KEYS if is_table else (*_SCALAR_KEYS, "type"))
    detail = "table field" if is_table else "parameter field"
    return [
        _property(key, replace, "only for tables" if key == "type" else detail, order)
        for order, key in enumerate(keys)
        if key not in present
    ]


def _column_keys(
    lines: list[str], index: int, item: int, replace: Range
) -> list[Candidate]:
    end = _block_end(lines, item, _indent(lines[item]))
    present = _sibling_keys(lines, item, end, index)
    return [
        _property(key, replace, "column field", order)
        for order, key in enumerate(_COLUMN_KEYS)
        if key not in present
    ]


def _key_candidates(
    lines: list[str], index: int, replace: Range, indent: int
) -> list[Candidate]:
    if indent == 0:
        return []
    parent = _parent(lines, index, indent)
    if parent is None:
        return []
    parent_text, has_marker = lines[parent].strip(), lines[index].lstrip().startswith(
        _LIST_MARKER
    )
    if _indent(lines[parent]) == 0 and not has_marker:
        return _parameter_keys(lines, index, parent, replace)
    if parent_text == "columns:" and has_marker:
        return _column_keys(lines, index, index, replace)
    if parent_text.startswith(_LIST_MARKER) and not has_marker:
        grandparent = _parent(lines, parent, _indent(lines[parent]))
        if grandparent is not None and lines[grandparent].strip() == "columns:":
            return _column_keys(lines, index, parent, replace)
    return []


def _yaml_text(unit: str) -> str:
    """*unit* as a YAML scalar: quoted if it would not read back as this text."""
    dumped = yaml.safe_dump(unit, width=10_000, allow_unicode=True).splitlines()[0]
    quoted = dumped[:1] in ("'", '"')
    return f'"{unit}"' if quoted and '"' not in unit else dumped


def _unit_candidates(known: Sequence[str], replace: Range) -> list[Candidate]:
    units = [(unit, "used in this workspace") for unit in known]
    units += [(unit, "common unit") for unit in COMMON_UNITS if unit not in known]
    seen: set[str] = set()
    return [
        Candidate(
            unit,
            _yaml_text(unit),
            replace,
            lsp.CompletionItemKind.Unit,
            detail=detail,
            filter_text=unit,
        )  # fmt: skip
        for unit, detail in units
        if not (unit in seen or seen.add(unit))
    ]


def _value_candidates(
    key: str, replace: Range, known_units: Callable[[], Sequence[str]]
) -> list[Candidate]:
    if key == "unit":
        return _unit_candidates(known_units(), replace)
    if key == "type":
        kind = lsp.CompletionItemKind.EnumMember
        return [
            Candidate("table", "table", replace, kind, detail="the only explicit type")
        ]
    return []


def parameter_candidates(
    text: str, position: Position, known_units: Callable[[], Sequence[str]]
) -> list[Candidate]:
    """Complete field names, ``type`` and ``unit`` in a parameter YAML file.

    *known_units* returns the units used elsewhere in the workspace and is only
    called when a unit is being completed.
    """
    lines = text.split("\n")
    if position.line >= len(lines):
        return []
    line, cursor = position.line, position.character
    before = lines[line][:cursor]
    indent = _indent(before)
    marker = len(_LIST_MARKER) if before[indent:].startswith(_LIST_MARKER) else 0
    content = before[indent + marker :]
    value = _KEY_VALUE_RE.match(content)
    if value is not None:
        replace = Range(
            Position(line, cursor - len(value["typed"])), Position(line, cursor)
        )
        return _value_candidates(value["key"], replace, known_units)
    replace = Range(Position(line, indent + marker), Position(line, cursor))
    return [] if ":" in content else _key_candidates(lines, line, replace, indent)
