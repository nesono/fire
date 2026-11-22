#!/usr/bin/env python3
"""Extract what a requirement or parameter file defines, with positions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from fire.lsp.document_parser import Position, Range, Requirement, parse_requirements

_PARAMETER_KEY_RE: Final = re.compile(r"^([a-z][a-z0-9_]*)_v([1-9][0-9]*)\s*:")


@dataclass(frozen=True)
class RequirementInfo:
    id: str
    version: int | None
    range: Range


@dataclass(frozen=True)
class ParameterInfo:
    name: str
    versions: dict[int, Range] = field(default_factory=dict)


def _version_of(requirement: Requirement) -> int | None:
    for metadata in requirement.fields:
        if metadata.key.lower() == "version" and metadata.value.isdigit():
            return int(metadata.value)
    return None


def requirements_in(text: str) -> dict[str, RequirementInfo]:
    """Return requirements by ID. The first definition of an ID wins."""
    found: dict[str, RequirementInfo] = {}
    for requirement in parse_requirements(text):
        info = RequirementInfo(
            requirement.id, _version_of(requirement), requirement.id_range
        )
        found.setdefault(requirement.id, info)
    return found


def parameters_in(text: str) -> dict[str, ParameterInfo]:
    """Return parameters by base name from top-level ``name_vN:`` keys."""
    found: dict[str, ParameterInfo] = {}
    for line_no, line in enumerate(text.split("\n")):
        match = _PARAMETER_KEY_RE.match(line)
        if match:
            name, version = match.group(1), int(match.group(2))
            key_end = match.end(2)
            info = found.setdefault(name, ParameterInfo(name))
            info.versions[version] = Range(
                Position(line_no, 0), Position(line_no, key_end)
            )
    return found
