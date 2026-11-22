#!/usr/bin/env python3
"""Locate the workspace root and read repository-relative link targets."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Final

_ROOT_MARKERS: Final = ("MODULE.bazel", "WORKSPACE", "WORKSPACE.bazel")
_YAML_SUFFIX: Final = ".yaml"


def find_workspace_root(start: Path) -> Path | None:
    """Return the nearest ancestor of *start* that holds a Bazel root marker."""
    for directory in (start, *start.parents):
        if any((directory / marker).is_file() for marker in _ROOT_MARKERS):
            return directory
    return None


class Workspace:
    """Reads link targets of the form ``/path/from/root``.

    *overlay* maps absolute paths to unsaved editor content, which wins over
    what is on disk.
    """

    def __init__(self, root: Path, overlay: Mapping[Path, str] | None = None) -> None:
        self.root = root.resolve()
        self._overlay = {p.resolve(): text for p, text in (overlay or {}).items()}

    def read(self, link_path: str) -> str | None:
        """Return the target's text, or ``None`` if it is missing or outside the root."""
        path = self._resolve(link_path)
        if path is None:
            return None
        for candidate in self._candidates(path):
            text = self._read_file(candidate)
            if text is not None:
                return text
        return None

    def _resolve(self, link_path: str) -> Path | None:
        if not link_path.startswith("/"):
            return None
        path = (self.root / link_path[1:]).resolve()
        return path if path.is_relative_to(self.root) else None

    @staticmethod
    def _candidates(path: Path) -> list[Path]:
        # parameter_library emits foo_validated.yaml for a generated foo.yaml
        if path.suffix == _YAML_SUFFIX:
            return [path, path.with_name(f"{path.stem}_validated{_YAML_SUFFIX}")]
        return [path]

    def _read_file(self, path: Path) -> str | None:
        if path in self._overlay:
            return self._overlay[path]
        try:
            return path.read_text(encoding="utf-8") if path.is_file() else None
        except (OSError, UnicodeDecodeError):
            return None
