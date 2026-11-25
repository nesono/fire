#!/usr/bin/env python3
"""A cached index of the units used in the parameter files of a workspace."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from fire.lsp.file_index import FileIndex
from fire.lsp.parameter_completion import WorkspaceUnits
from fire.lsp.parameter_diagnostics import looks_like_parameter_file

_UNIT_RE: Final = re.compile(r"^\s*(?:-\s+)?unit:[ \t]*(?P<value>.+?)\s*$")
_QUOTES: Final = ("'", '"')


@dataclass(frozen=True)
class _UnitUse:
    value: str
    quoted: bool


def _unit_of(line: str) -> _UnitUse | None:
    match = _UNIT_RE.match(line)
    if match is None:
        return None
    value = match["value"].split(" #")[0].strip()
    quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in _QUOTES
    value = value[1:-1] if quoted else value
    return _UnitUse(value, quoted) if value else None


class UnitIndex(FileIndex[_UnitUse]):
    def __init__(self, root: Path) -> None:
        super().__init__(root, (".yaml",))

    def units(self, overlay: Mapping[Path, str]) -> list[str]:
        """Return the units in use, the most frequent first."""
        return list(self.workspace_units(overlay).units)

    def workspace_units(self, overlay: Mapping[Path, str]) -> WorkspaceUnits:
        """The units in use, most frequent first, and whether most are quoted."""
        uses = self.items(overlay)
        counts = Counter(use.value for use in uses)
        ordered = sorted(counts.items(), key=lambda c: (-c[1], c[0]))
        quoted = sum(use.quoted for use in uses)
        majority = None if quoted * 2 == len(uses) else quoted * 2 > len(uses)
        return WorkspaceUnits([unit for unit, _ in ordered], majority)

    def _parse(self, path: Path, text: str) -> list[_UnitUse]:
        if not looks_like_parameter_file(text):
            return []
        uses = (_unit_of(line) for line in text.split("\n"))
        return [use for use in uses if use is not None]
