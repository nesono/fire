#!/usr/bin/env python3
"""A cached index of the units used in the parameter files of a workspace."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from fire.lsp.file_index import FileIndex
from fire.lsp.parameter_diagnostics import looks_like_parameter_file

_UNIT_RE: Final = re.compile(r"^\s*(?:-\s+)?unit:[ \t]*(?P<value>.+?)\s*$")
_QUOTES: Final = ("'", '"')


def _unit_of(line: str) -> str | None:
    match = _UNIT_RE.match(line)
    if match is None:
        return None
    value = match["value"].split(" #")[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in _QUOTES:
        value = value[1:-1]
    return value or None


class UnitIndex(FileIndex[str]):
    def __init__(self, root: Path) -> None:
        super().__init__(root, (".yaml",))

    def units(self, overlay: Mapping[Path, str]) -> list[str]:
        """Return the units in use, the most frequent first."""
        counts = Counter(self.items(overlay))
        return [unit for unit, _ in sorted(counts.items(), key=lambda c: (-c[1], c[0]))]

    def _parse(self, path: Path, text: str) -> list[str]:
        if not looks_like_parameter_file(text):
            return []
        units = (_unit_of(line) for line in text.split("\n"))
        return [unit for unit in units if unit is not None]
