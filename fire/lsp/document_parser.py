#!/usr/bin/env python3
"""Position-aware parser for FIRE requirement documents.

Unlike ``fire.starlark.metadata_parsing``, which joins lines and drops offsets,
this parser keeps the line/character range of every node so editor tooling can
point at the exact text that a diagnostic or completion refers to.

Characters are counted in Python code points, not UTF-16 code units.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from fire.starlark import markdown_common, metadata_parsing, path_common, patterns

_HEADING_RE: Final = re.compile(r"^## (\S.*?)\s*$")
_LINK_RE: Final = re.compile(markdown_common.MARKDOWN_LINK_PATTERN)
_TODO_RE: Final = re.compile(r"TODO(?:\([^)\s]*\))?")
_FIELD_SEPARATOR: Final = "|"
_FENCE_MARKERS: Final = ("```", "~~~")
_FIELD_KEYS: Final = ["sil", "sec", "version", "parent"]


@dataclass(frozen=True)
class Position:
    line: int
    character: int


@dataclass(frozen=True)
class Range:
    start: Position
    end: Position


@dataclass(frozen=True)
class MetadataField:
    key: str
    key_range: Range
    value: str
    value_range: Range


@dataclass(frozen=True)
class Link:
    text: str
    text_range: Range
    url: str
    url_range: Range
    path: str
    version: int | None
    anchor: str | None


@dataclass(frozen=True)
class Todo:
    text: str
    range: Range
    valid: bool


@dataclass(frozen=True)
class Requirement:
    id: str
    id_range: Range
    fields: list[MetadataField] = field(default_factory=list)


def _range(line: int, start: int, end: int) -> Range:
    return Range(Position(line, start), Position(line, end))


def _parse_segment(line_no: int, text: str, offset: int) -> MetadataField | None:
    key, sep, rest = text.partition(":")
    if not sep or not key.strip():
        return None
    key_start = offset + len(key) - len(key.lstrip())
    value = rest.strip()
    value_start = offset + len(key) + 1 + len(rest) - len(rest.lstrip())
    return MetadataField(
        key=key.strip(),
        key_range=_range(line_no, key_start, key_start + len(key.strip())),
        value=value,
        value_range=_range(line_no, value_start, value_start + len(value)),
    )


def _parse_line_fields(line_no: int, line: str) -> list[MetadataField]:
    fields: list[MetadataField] = []
    offset = 0
    for segment in line.split(_FIELD_SEPARATOR):
        parsed = _parse_segment(line_no, segment, offset)
        if parsed:
            fields.append(parsed)
        offset += len(segment) + 1
    return fields


def _parse_metadata(lines: list[str], heading_index: int) -> list[MetadataField]:
    fields: list[MetadataField] = []
    previous = ""
    for i in range(heading_index + 1, len(lines)):
        stripped = lines[i].strip()
        if not stripped and not fields:
            continue
        if not stripped or (fields and not previous.endswith(_FIELD_SEPARATOR)):
            break
        if not metadata_parsing.is_metadata_line(stripped, _FIELD_KEYS):
            break
        fields.extend(_parse_line_fields(i, lines[i]))
        previous = stripped
        if not stripped.endswith(_FIELD_SEPARATOR):
            break
    return fields


def _fenced_lines(lines: list[str]) -> set[int]:
    """Return indices of lines inside, or delimiting, fenced code blocks."""
    fenced: set[int] = set()
    fence: str | None = None
    for index, line in enumerate(lines):
        marker = line.lstrip()[:3]
        is_marker = marker in _FENCE_MARKERS
        if fence is not None or is_marker:
            fenced.add(index)
        if is_marker:
            fence = None if fence == marker else (fence or marker)
    return fenced


def parse_requirements(text: str) -> list[Requirement]:
    """Return every ``## ID`` requirement heading with its metadata fields."""
    lines = text.split("\n")
    fenced = _fenced_lines(lines)
    requirements: list[Requirement] = []
    for index, line in enumerate(lines):
        match = _HEADING_RE.match(line)
        if match and index not in fenced:
            id_range = _range(index, match.start(1), match.end(1))
            fields = _parse_metadata(lines, index)
            requirements.append(Requirement(match.group(1), id_range, fields))
    return requirements


def _split_url(url: str) -> tuple[str, int | None, str | None]:
    _, version = path_common.extract_version_from_url(url)
    path, _, anchor = url.partition("#")
    return path.split("?")[0], version, anchor or None


def _link_from_match(line_no: int, match: re.Match[str]) -> Link:
    path, version, anchor = _split_url(match.group(2))
    return Link(
        text=match.group(1),
        text_range=_range(line_no, match.start(1), match.end(1)),
        url=match.group(2),
        url_range=_range(line_no, match.start(2), match.end(2)),
        path=path,
        version=version,
        anchor=anchor,
    )


def parse_links(text: str) -> list[Link]:
    """Return every inline ``[text](url)`` link with its ranges."""
    return [
        _link_from_match(index, match)
        for index, line in enumerate(text.split("\n"))
        for match in _LINK_RE.finditer(line)
    ]


def parse_todos(text: str) -> list[Todo]:
    """Return every ``TODO`` marker, flagging those not in ``TODO(KEY-1)`` form."""
    return [
        Todo(
            text=match.group(0),
            range=_range(index, match.start(), match.end()),
            valid=bool(patterns.TODO_PATTERN.fullmatch(match.group(0))),
        )
        for index, line in enumerate(text.split("\n"))
        for match in _TODO_RE.finditer(line)
    ]
