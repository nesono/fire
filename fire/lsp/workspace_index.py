#!/usr/bin/env python3
"""A cached index of the symbols in every requirement and parameter file.

Files are re-parsed only when their modification time or size changes. Open
documents are passed in as an overlay and never enter the cache, so unsaved
edits are searchable without being mistaken for what is on disk.
"""

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from lsprotocol import types as lsp

from fire.lsp.conversion import to_lsp_range
from fire.lsp.symbols import parameter_symbols, requirement_symbols

_YAML_SUFFIX: Final = ".yaml"
_IGNORED_NAMES: Final = ("node_modules", "__pycache__")


@dataclass(frozen=True)
class IndexedSymbol:
    name: str
    kind: lsp.SymbolKind
    location: lsp.Location
    container: str


@dataclass(frozen=True)
class _CacheEntry:
    stamp: tuple[int, int]
    symbols: list[IndexedSymbol]


def _is_ignored(name: str) -> bool:
    return name.startswith((".", "bazel-")) or name in _IGNORED_NAMES


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


class WorkspaceIndex:
    def __init__(self, root: Path, suffixes: tuple[str, ...]) -> None:
        self.root = root.resolve()
        self._suffixes = (*suffixes, _YAML_SUFFIX)
        self._cache: dict[Path, _CacheEntry] = {}

    def symbols(self, overlay: Mapping[Path, str]) -> list[IndexedSymbol]:
        """Return the symbols of all indexed files, ordered by path then line."""
        open_documents = self._indexed_overlay(overlay)
        on_disk = set(self._walk())
        result: list[IndexedSymbol] = []
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
                if filename.endswith(self._suffixes):
                    yield Path(directory) / filename

    def _indexed_overlay(self, overlay: Mapping[Path, str]) -> dict[Path, str]:
        documents = {}
        for path, text in overlay.items():
            resolved = path.resolve()
            if resolved.is_relative_to(self.root) and self._is_indexed(resolved):
                documents[resolved] = text
        return documents

    def _is_indexed(self, path: Path) -> bool:
        parts = path.relative_to(self.root).parts
        has_suffix = path.name.endswith(self._suffixes)
        return has_suffix and not any(_is_ignored(part) for part in parts[:-1])

    def _cached(self, path: Path) -> list[IndexedSymbol]:
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
        return entry.symbols

    def _parse(self, path: Path, text: str) -> list[IndexedSymbol]:
        if path.suffix == _YAML_SUFFIX:
            symbols = parameter_symbols(text)
        else:
            symbols = requirement_symbols(text)
        lines = text.split("\n")
        uri = path.as_uri()
        container = path.relative_to(self.root).as_posix()
        return [
            IndexedSymbol(
                symbol.name,
                symbol.kind,
                lsp.Location(uri, to_lsp_range(symbol.selection_range, lines)),
                container,
            )
            for symbol in symbols
        ]
