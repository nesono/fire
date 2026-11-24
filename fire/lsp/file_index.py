#!/usr/bin/env python3
"""A stat-cached scan over the files of a workspace.

Subclasses decide what to extract from each file. Files are re-parsed only when
their modification time or size changes. Open documents are passed in as an
overlay and never enter the cache, so unsaved edits are indexed without being
mistaken for what is on disk.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, TypeVar

T = TypeVar("T")

_IGNORED_NAMES: Final = ("node_modules", "__pycache__")


@dataclass(frozen=True)
class _CacheEntry(Generic[T]):
    stamp: tuple[int, int]
    items: list[T]


def _is_ignored(name: str) -> bool:
    return name.startswith((".", "bazel-")) or name in _IGNORED_NAMES


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


class FileIndex(ABC, Generic[T]):
    """Indexes the files under *root* that *accepts* by root-relative path.

    Hidden directories, ``bazel-*`` outputs, ``node_modules`` and
    ``__pycache__`` are skipped and symlinked directories are not followed.
    """

    def __init__(self, root: Path, accepts: Callable[[str], bool]) -> None:
        self.root = root.resolve()
        self._accepts = accepts
        self._cache: dict[Path, _CacheEntry[T]] = {}

    @abstractmethod
    def _parse(self, path: Path, text: str) -> list[T]:
        """Extract the items of one file."""

    def items(self, overlay: Mapping[Path, str]) -> list[T]:
        """Return the items of all indexed files, ordered by path."""
        open_documents = self._indexed_overlay(overlay)
        on_disk = set(self._walk())
        result: list[T] = []
        for path in sorted(on_disk | set(open_documents), key=self._sort_key):
            if path in open_documents:
                result.extend(self._parse(path, open_documents[path]))
            else:
                result.extend(self._cached(path))
        self._cache = {p: e for p, e in self._cache.items() if p in on_disk}
        return result

    def _sort_key(self, path: Path) -> tuple[str, ...]:
        return path.relative_to(self.root).parts

    def _walk(self) -> Iterator[Path]:
        for directory, dirnames, filenames in os.walk(self.root):
            dirnames[:] = sorted(d for d in dirnames if not _is_ignored(d))
            for filename in filenames:
                path = Path(directory) / filename
                if self._accepts(path.relative_to(self.root).as_posix()):
                    yield path

    def _indexed_overlay(self, overlay: Mapping[Path, str]) -> dict[Path, str]:
        documents = {}
        for path, text in overlay.items():
            resolved = path.resolve()
            if resolved.is_relative_to(self.root) and self._is_indexed(resolved):
                documents[resolved] = text
        return documents

    def _is_indexed(self, path: Path) -> bool:
        relative = path.relative_to(self.root)
        in_ignored_directory = any(_is_ignored(part) for part in relative.parts[:-1])
        return self._accepts(relative.as_posix()) and not in_ignored_directory

    def _cached(self, path: Path) -> list[T]:
        try:
            stat = path.stat()
        except OSError:
            return []
        stamp = (stat.st_mtime_ns, stat.st_size)
        entry = self._cache.get(path)
        if entry is None or entry.stamp != stamp:
            text = _read(path)
            entry = _CacheEntry(stamp, self._parse(path, text) if text else [])
            self._cache[path] = entry
        return entry.items
