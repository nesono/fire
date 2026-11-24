#!/usr/bin/env python3
"""A cached index of everything a link can point at, with the version to link."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from fire.lsp.file_index import FileIndex
from fire.lsp.index import parameters_in, requirements_in

PARAMETER: Final = "parameter"
REQUIREMENT: Final = "requirement"
_YAML_SUFFIX: Final = ".yaml"


@dataclass(frozen=True)
class LinkTarget:
    """A requirement or parameter, with its latest version and repository path."""

    kind: str
    name: str
    version: int | None
    path: str


class LinkTargetIndex(FileIndex[LinkTarget]):
    def __init__(self, root: Path, suffixes: tuple[str, ...]) -> None:
        super().__init__(root, (*suffixes, _YAML_SUFFIX))

    def targets(self, overlay: Mapping[Path, str]) -> list[LinkTarget]:
        """Return all targets, ordered by file then position."""
        return self.items(overlay)

    def _parse(self, path: Path, text: str) -> list[LinkTarget]:
        link_path = "/" + path.relative_to(self.root).as_posix()
        if path.suffix == _YAML_SUFFIX:
            return [
                LinkTarget(PARAMETER, name, max(info.versions), link_path)
                for name, info in parameters_in(text).items()
            ]
        return [
            LinkTarget(REQUIREMENT, info.id, info.version, link_path)
            for info in requirements_in(text).values()
        ]
