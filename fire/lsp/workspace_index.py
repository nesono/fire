#!/usr/bin/env python3
"""A cached index of the symbols in every requirement and parameter file."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from lsprotocol import types as lsp

from fire.lsp.conversion import to_lsp_range
from fire.lsp.document_types import DocumentTypes
from fire.lsp.file_index import FileIndex
from fire.lsp.symbols import parameter_symbols, requirement_symbols

_YAML_SUFFIX: Final = ".yaml"


@dataclass(frozen=True)
class IndexedSymbol:
    name: str
    kind: lsp.SymbolKind
    location: lsp.Location
    container: str


class WorkspaceIndex(FileIndex[IndexedSymbol]):
    def __init__(self, root: Path, types: DocumentTypes) -> None:
        def accepts(relative_path: str) -> bool:
            return types.is_document(relative_path) or relative_path.endswith(
                _YAML_SUFFIX
            )

        super().__init__(root, accepts)

    def symbols(self, overlay: Mapping[Path, str]) -> list[IndexedSymbol]:
        """Return the symbols of all indexed files, ordered by path then line."""
        return self.items(overlay)

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
