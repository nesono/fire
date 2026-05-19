#!/usr/bin/env python3
"""Parse pipe-separated inline metadata blocks found in requirement files.

Requirement files use a compact one-line (or continuation-line) metadata
format directly under a ``## REQ-ID`` heading::

    Sil: ASIL-D | Sec: false | Version: 1 | Parent: [REQ-XYZ](/path.md?version=1)

This module isolates the parsing logic so it can be shared by both the
cross-reference validator and the release-report generator without
crossing module-private boundaries.
"""

from __future__ import annotations

import re
from typing import Final

from fire.starlark import markdown_common

_METADATA_CONTINUATION_MARKER: Final = "|"
_METADATA_FIELD_SEPARATOR: Final = "|"
_DEFAULT_KNOWN_FIELDS: Final = ("sil", "sec", "version", "parent")


def is_metadata_line(line: str, known_fields: list[str]) -> bool:
    """Return True if *line* looks like an inline metadata line."""
    if _METADATA_FIELD_SEPARATOR in line:
        return True
    if ":" in line and not line.startswith("#"):
        parts = line.split(":", 1)
        key = parts[0].strip().lower()
        return len(parts) == 2 and key in known_fields
    return False


def _should_stop_collection(line: str, collected_lines: list[str]) -> bool:
    """Return True when metadata collection should stop on *line*."""
    if not line:
        return bool(collected_lines)
    if collected_lines and not collected_lines[-1].endswith(
        _METADATA_CONTINUATION_MARKER
    ):
        return True
    return False


def _join_metadata_lines(lines: list[str]) -> str:
    """Join metadata lines and strip the final trailing pipe."""
    joined = " ".join(lines).rstrip()
    if joined.endswith(_METADATA_CONTINUATION_MARKER):
        joined = joined[:-1].rstrip()
    return joined


def extract_next_metadata_line(
    lines: list[str],
    start_index: int,
    known_fields: list[str] | None = None,
) -> str | None:
    """Extract metadata lines after *start_index*, supporting continuations."""
    if known_fields is None:
        known_fields = list(_DEFAULT_KNOWN_FIELDS)
    collected_lines: list[str] = []

    for j in range(start_index + 1, len(lines)):
        next_line = lines[j].strip()

        if not next_line and not collected_lines:
            continue

        if _should_stop_collection(next_line, collected_lines):
            break

        if not is_metadata_line(next_line, known_fields):
            break

        collected_lines.append(next_line)
        if not next_line.endswith(_METADATA_CONTINUATION_MARKER):
            break

    return _join_metadata_lines(collected_lines) if collected_lines else None


def _parse_field_value(value: str) -> int | bool | str:
    """Parse a single metadata field value to its appropriate Python type."""
    if value.startswith("[") and "](" in value:
        match = re.match(markdown_common.MARKDOWN_LINK_PATTERN, value)
        if match:
            return value

    if value.isdigit():
        return int(value)

    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    return value


def parse_metadata_fields(metadata_line: str, req_id: str) -> dict:
    """Parse a pipe-separated metadata line into a frontmatter dictionary.

    Keys are normalized to lowercase. Values are typed via ``_parse_field_value``.
    Multiple ``Parent`` fields are aggregated into a list under ``parent``.
    """
    frontmatter: dict = {"id": req_id}
    parent_values: list = []

    for field in metadata_line.split(_METADATA_FIELD_SEPARATOR):
        field = field.strip()
        if not field or ":" not in field:
            continue

        parts = field.split(":", 1)
        key = parts[0].strip().lower()
        value = parts[1].strip() if len(parts) > 1 else ""

        if key == "parent":
            parent_values.append(_parse_field_value(value))
        else:
            frontmatter[key] = _parse_field_value(value)

    if parent_values:
        frontmatter["parent"] = parent_values

    return frontmatter
