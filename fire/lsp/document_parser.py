#!/usr/bin/env python3
"""Position-aware parser for FIRE requirement documents.

Unlike ``fire.starlark.metadata_parsing``, which joins lines and drops offsets,
this parser keeps the line/character range of every node so editor tooling can
point at the exact text that a diagnostic or completion refers to.

Characters are counted in Python code points, not UTF-16 code units.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Final

from fire.starlark import metadata_parsing, path_common, patterns

_HEADING_RE: Final = re.compile(r"^## (\S.*?)\s*$")
_USAGE_RE: Final = re.compile(
    r"\[(?P<text>[^\]]+)\](?:\((?P<url>[^)]+)\)|\[(?P<label>[^\]]*)\])?"
)
_DEFINITION_RE: Final = re.compile(r"^ {0,3}\[(?P<label>[^\]]+)\]:[ \t]*(?P<url>\S+)")
_NOT_A_SHORTCUT: Final = "([:"
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
    usage: Range | None = None

    @property
    def span(self) -> Range:
        """The whole link as written, brackets included.

        For a reference-style link this is the usage such as ``[text][1]``; its
        ``url_range`` points at the definition instead.
        """
        if self.usage is not None:
            return self.usage
        line = self.text_range.start.line
        return _range(
            line, self.text_range.start.character - 1, self.url_range.end.character + 1
        )


@dataclass(frozen=True)
class LinkDefinition:
    """A reference-style link definition such as ``[1]: /path?version=2#ID``."""

    label: str
    url: str
    label_range: Range
    url_range: Range


@dataclass(frozen=True)
class UnresolvedReference:
    """An explicit or implicit reference whose label has no definition."""

    label: str
    text: str
    range: Range


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


def _normalize_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def _text_lines(text: str) -> list[str]:
    return text.split("\n")


def parse_link_definitions(text: str) -> dict[str, LinkDefinition]:
    """Return reference-style link definitions by normalized label.

    As in CommonMark, labels ignore case and whitespace differences and the
    first definition of a label wins.
    """
    definitions: dict[str, LinkDefinition] = {}
    for line_no, line in enumerate(_text_lines(text)):
        match = _DEFINITION_RE.match(line)
        if match:
            definition = LinkDefinition(
                label=match.group("label"),
                url=match.group("url"),
                label_range=_range(line_no, *match.span("label")),
                url_range=_range(line_no, *match.span("url")),
            )
            definitions.setdefault(_normalize_label(definition.label), definition)
    return definitions


def _usages(text: str) -> Iterator[tuple[int, re.Match[str], str]]:
    """Yield ``(line, match, line text)`` for every bracketed usage."""
    for line_no, line in enumerate(_text_lines(text)):
        if _DEFINITION_RE.match(line):
            continue
        for match in _USAGE_RE.finditer(line):
            yield line_no, match, line


def _reference_label(match: re.Match[str], line: str) -> str | None:
    """The label a ``[text][label]``, ``[text][]`` or ``[text]`` usage names."""
    explicit = match.group("label")
    if explicit is not None:
        return explicit or match.group("text")
    following = line[match.end() : match.end() + 1]
    if following and following in _NOT_A_SHORTCUT:
        return None
    return match.group("text")


def _inline_link(line_no: int, match: re.Match[str]) -> Link:
    url = match.group("url")
    path, version, anchor = _split_url(url)
    return Link(
        text=match.group("text"),
        text_range=_range(line_no, *match.span("text")),
        url=url,
        url_range=_range(line_no, *match.span("url")),
        path=path,
        version=version,
        anchor=anchor,
    )


def _reference_link(
    line_no: int, match: re.Match[str], definition: LinkDefinition
) -> Link:
    path, version, anchor = _split_url(definition.url)
    return Link(
        text=match.group("text"),
        text_range=_range(line_no, *match.span("text")),
        url=definition.url,
        url_range=definition.url_range,
        path=path,
        version=version,
        anchor=anchor,
        usage=_range(line_no, *match.span()),
    )


def parse_links(text: str) -> list[Link]:
    """Return every link: inline ``[text](url)`` and resolved reference-style.

    A reference-style usage is resolved through its definition; usages whose
    label is undefined are not links.
    """
    definitions = parse_link_definitions(text)
    links: list[Link] = []
    for line_no, match, line in _usages(text):
        if match.group("url") is not None:
            links.append(_inline_link(line_no, match))
            continue
        label = _reference_label(match, line)
        definition = definitions.get(_normalize_label(label)) if label else None
        if definition is not None:
            links.append(_reference_link(line_no, match, definition))
    return links


def parse_unresolved_references(text: str) -> list[UnresolvedReference]:
    """Return explicit and implicit references whose label is not defined.

    Shortcut references such as ``[text]`` are plain text unless defined, so
    they are never reported.
    """
    definitions = parse_link_definitions(text)
    unresolved: list[UnresolvedReference] = []
    for line_no, match, _ in _usages(text):
        label = match.group("label")
        if label is None or match.group("url") is not None:
            continue
        name = label or match.group("text")
        if _normalize_label(name) not in definitions:
            group = "label" if label else "text"
            unresolved.append(
                UnresolvedReference(
                    name, match.group("text"), _range(line_no, *match.span(group))
                )
            )
    return unresolved


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
