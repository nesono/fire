#!/usr/bin/env python3
"""Analyze one document: pick its metadata model and produce LSP diagnostics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Final

from lsprotocol import types as lsp
from pydantic import BaseModel

from fire.lsp.conversion import (
    from_lsp_position,
    to_lsp_diagnostic,
    to_lsp_range,
    to_lsp_symbol,
)
from fire.lsp.diagnostics import diagnose_requirements
from fire.lsp.document_types import DocumentTypes, GlobRule
from fire.lsp.link_index import LinkIndex
from fire.lsp.navigation import definition_at
from fire.lsp.reference_diagnostics import ReferenceChecker
from fire.lsp.references import (
    ReferenceTarget,
    declaration_range,
    find_references,
    target_at,
)
from fire.lsp.symbol_search import search_symbols
from fire.lsp.symbols import parameter_symbols, requirement_symbols
from fire.lsp.uris import uri_to_path
from fire.lsp.workspace import Workspace, find_workspace_root
from fire.lsp.workspace_index import WorkspaceIndex
from fire.starlark.config_models import FireConfig
from fire.starlark.dynamic_requirement_model import build_models_from_config


_YAML_SUFFIX: Final = ".yaml"
_WORKSPACE_SYMBOL_LIMIT: Final = 200


def _relative_path(path: Path) -> str:
    """The workspace-relative path used to decide a file's document type."""
    root = find_workspace_root(path)
    try:
        return (
            path.resolve().relative_to(root.resolve()).as_posix()
            if root
            else path.as_posix()
        )
    except ValueError:
        return path.as_posix()


def _root_of(path: Path) -> Path | None:
    root = find_workspace_root(path)
    if root is None and path.is_dir():
        root = path
    return root.resolve() if root else None


class Analyzer:
    """Validates documents against the document types of a FIRE config."""

    def __init__(self, config: FireConfig, glob_rules: Sequence[GlobRule] = ()) -> None:
        self._models = build_models_from_config(config)
        self._types = DocumentTypes.from_config(config, glob_rules)
        self._indexes: dict[Path, WorkspaceIndex] = {}
        self._link_indexes: dict[Path, LinkIndex] = {}

    def _model_for(self, path: Path) -> type[BaseModel] | None:
        type_name = self._types.type_of(_relative_path(path))
        return self._models.get(type_name) if type_name else None

    def _workspace(self, path: Path, overlay: Mapping[Path, str]) -> Workspace | None:
        root = find_workspace_root(path)
        return Workspace(root, overlay) if root else None

    def _references(
        self, path: Path, overlay: Mapping[Path, str]
    ) -> ReferenceChecker | None:
        workspace = self._workspace(path, overlay)
        return ReferenceChecker(workspace, self._types) if workspace else None

    def diagnose(
        self, uri: str, text: str, overlay: Mapping[Path, str] | None = None
    ) -> list[lsp.Diagnostic]:
        """Diagnose one document; *overlay* holds unsaved content of other files."""
        path = uri_to_path(uri)
        if path is None:
            return []
        model = self._model_for(path)
        if model is None:
            return []
        lines = text.split("\n")
        return [
            to_lsp_diagnostic(diagnostic, lines)
            for diagnostic in diagnose_requirements(
                text, model, self._references(path, overlay or {})
            )
        ]

    def definition(
        self,
        uri: str,
        text: str,
        position: lsp.Position,
        overlay: Mapping[Path, str] | None = None,
    ) -> lsp.Location | None:
        """Return where the link at *position* in a FIRE document is defined."""
        path = uri_to_path(uri)
        if path is None or self._model_for(path) is None:
            return None
        workspace = self._workspace(path, overlay or {})
        if workspace is None:
            return None
        cursor = from_lsp_position(position, text.split("\n"))
        target = definition_at(text, cursor, workspace, self._types)
        if target is None:
            return None
        return lsp.Location(
            uri=target.path.as_uri(),
            range=to_lsp_range(target.range, target.text.split("\n")),
        )

    def document_symbols(self, uri: str, text: str) -> list[lsp.DocumentSymbol]:
        """Return the outline of a requirement or parameter file."""
        path = uri_to_path(uri)
        if path is None:
            return []
        if path.suffix == _YAML_SUFFIX:
            symbols = parameter_symbols(text)
        elif self._model_for(path) is not None:
            symbols = requirement_symbols(text)
        else:
            return []
        lines = text.split("\n")
        return [to_lsp_symbol(symbol, lines) for symbol in symbols]

    def _index_for(self, root: Path) -> WorkspaceIndex:
        if root not in self._indexes:
            self._indexes[root] = WorkspaceIndex(root, self._types)
        return self._indexes[root]

    def workspace_symbols(
        self,
        query: str,
        start_paths: Iterable[Path],
        overlay: Mapping[Path, str] | None = None,
    ) -> list[lsp.WorkspaceSymbol]:
        """Search requirement IDs and parameter keys in the workspaces of *start_paths*.

        Each start path (a folder or a file) is mapped to its workspace root.
        """
        roots = dict.fromkeys(r for p in start_paths if (r := _root_of(p)) is not None)
        symbols = [
            symbol
            for root in roots
            for symbol in self._index_for(root).symbols(overlay or {})
        ]
        return [
            lsp.WorkspaceSymbol(
                name=symbol.name,
                kind=symbol.kind,
                location=symbol.location,
                container_name=symbol.container,
            )
            for symbol in search_symbols(symbols, query, _WORKSPACE_SYMBOL_LIMIT)
        ]

    def _link_index_for(self, root: Path) -> LinkIndex:
        if root not in self._link_indexes:
            self._link_indexes[root] = LinkIndex(root, self._types)
        return self._link_indexes[root]

    def _declaration(
        self, target: ReferenceTarget, workspace: Workspace
    ) -> lsp.Location | None:
        """Locate the heading or ``name_vN`` key that *target* refers to."""
        if not target.path.is_relative_to(workspace.root):
            return None
        located = workspace.locate(
            "/" + target.path.relative_to(workspace.root).as_posix()
        )
        found = declaration_range(target, located[1]) if located else None
        if located is None or found is None:
            return None
        return lsp.Location(
            located[0].as_uri(), to_lsp_range(found, located[1].split("\n"))
        )

    def _reference_locations(
        self, target: ReferenceTarget, root: Path, overlay: Mapping[Path, str]
    ) -> list[lsp.Location]:
        links = self._link_index_for(root).links(overlay)
        return [link.location for link in find_references(links, target, root)]

    def references(
        self,
        uri: str,
        text: str,
        position: lsp.Position,
        include_declaration: bool,
        overlay: Mapping[Path, str] | None = None,
    ) -> list[lsp.Location]:
        """Return the links that point at the symbol at *position*.

        The cursor may be on a link, a requirement heading ID, or a parameter
        key. Links to the exact version at the cursor come first.
        """
        path = uri_to_path(uri)
        workspace = self._workspace(path, overlay or {}) if path else None
        if path is None or workspace is None or not self._has_symbols(path):
            return []
        cursor = from_lsp_position(position, text.split("\n"))
        target = target_at(text, cursor, path.resolve(), workspace)
        if target is None:
            return []
        locations = self._reference_locations(target, workspace.root, overlay or {})
        declaration = (
            self._declaration(target, workspace) if include_declaration else None
        )
        return [declaration, *locations] if declaration else locations

    def _has_symbols(self, path: Path) -> bool:
        if path.suffix == _YAML_SUFFIX:
            return True
        return self._model_for(path) is not None
