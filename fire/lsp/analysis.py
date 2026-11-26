#!/usr/bin/env python3
"""Analyze one document: pick its metadata model and produce LSP diagnostics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Final

from lsprotocol import types as lsp

from fire.lsp.code_actions import code_actions
from fire.lsp.completion import metadata_candidates
from fire.lsp.conversion import (
    from_lsp_position,
    to_lsp_code_action,
    to_lsp_completion_item,
    to_lsp_diagnostic,
    to_lsp_range,
    to_lsp_symbol,
)
from fire.lsp.diagnostics import diagnose_requirements
from fire.lsp.document_parser import Range as ParsedRange
from fire.lsp.link_index import LinkIndex
from fire.lsp.link_completion import link_candidates
from fire.lsp.link_insertion import link_insertion_candidates
from fire.lsp.link_targets import LinkTarget, LinkTargetIndex
from fire.lsp.navigation import definition_at
from fire.lsp.parameter_completion import WorkspaceUnits, parameter_candidates
from fire.lsp.parameter_diagnostics import (
    diagnose_parameters,
    looks_like_parameter_file,
)
from fire.lsp.reference_diagnostics import ReferenceChecker
from fire.lsp.references import (
    ReferenceTarget,
    declaration_range,
    find_references,
    target_at,
)
from fire.lsp.symbol_search import search_symbols
from fire.lsp.symbols import parameter_symbols, requirement_symbols
from fire.lsp.unit_index import UnitIndex
from fire.lsp.uris import uri_to_path
from fire.lsp.workspace import Workspace, find_workspace_root
from fire.lsp.workspace_index import WorkspaceIndex
from fire.starlark.config_models import DocumentTypeDefinition, FireConfig
from fire.starlark.dynamic_requirement_model import (
    build_models_from_config,
    model_for_suffix,
)


_YAML_SUFFIX: Final = ".yaml"
_WORKSPACE_SYMBOL_LIMIT: Final = 200


def _root_of(path: Path) -> Path | None:
    root = find_workspace_root(path)
    if root is None and path.is_dir():
        root = path
    return root.resolve() if root else None


class Analyzer:
    """Validates documents against the document types of a FIRE config."""

    def __init__(self, config: FireConfig) -> None:
        self._config = config
        self._models = build_models_from_config(config)
        self._suffixes = tuple(dt.suffix for dt in config.document_types.values())
        self._indexes: dict[Path, WorkspaceIndex] = {}
        self._link_indexes: dict[Path, LinkIndex] = {}
        self._target_indexes: dict[Path, LinkTargetIndex] = {}
        self._unit_indexes: dict[Path, UnitIndex] = {}

    def _workspace(self, path: Path, overlay: Mapping[Path, str]) -> Workspace | None:
        root = find_workspace_root(path)
        return Workspace(root, overlay) if root else None

    def _references(
        self, path: Path, overlay: Mapping[Path, str]
    ) -> ReferenceChecker | None:
        workspace = self._workspace(path, overlay)
        return ReferenceChecker(workspace, self._suffixes) if workspace else None

    def diagnose(
        self, uri: str, text: str, overlay: Mapping[Path, str] | None = None
    ) -> list[lsp.Diagnostic]:
        """Diagnose one document; *overlay* holds unsaved content of other files."""
        path = uri_to_path(uri)
        if path is None:
            return []
        if path.suffix == _YAML_SUFFIX:
            return self._diagnose_parameters(text)
        model = model_for_suffix(self._config, self._models, str(path))
        if model is None:
            return []
        lines = text.split("\n")
        return [
            to_lsp_diagnostic(diagnostic, lines)
            for diagnostic in diagnose_requirements(
                text, model, self._references(path, overlay or {})
            )
        ]

    def code_actions(
        self,
        uri: str,
        text: str,
        selection: lsp.Range,
        overlay: Mapping[Path, str] | None = None,
    ) -> list[lsp.CodeAction]:
        """Return quick fixes for the diagnostics of a requirement document."""
        path = uri_to_path(uri)
        if path is None or path.suffix == _YAML_SUFFIX:
            return []
        model = model_for_suffix(self._config, self._models, str(path))
        if model is None:
            return []
        references = self._references(path, overlay or {})
        diagnostics = diagnose_requirements(text, model, references)
        lines = text.split("\n")
        wanted = ParsedRange(
            from_lsp_position(selection.start, lines),
            from_lsp_position(selection.end, lines),
        )
        latest = references.latest_version if references else (lambda link: None)
        actions = code_actions(text, diagnostics, wanted, latest)
        return [to_lsp_code_action(action, uri, lines) for action in actions]

    def _document_type(self, path: Path) -> DocumentTypeDefinition | None:
        for doc_type in self._config.document_types.values():
            if str(path).endswith(doc_type.suffix):
                return doc_type
        return None

    def _link_targets(
        self, root: Path, overlay: Mapping[Path, str]
    ) -> list[LinkTarget]:
        if root not in self._target_indexes:
            self._target_indexes[root] = LinkTargetIndex(root, self._suffixes)
        return self._target_indexes[root].targets(overlay)

    def _link_files(self, root: Path, overlay: Mapping[Path, str]) -> list[str]:
        """Repository-relative paths of the files that define symbols to link to."""
        symbols = self._index_for(root).symbols(overlay)
        return sorted({"/" + symbol.container for symbol in symbols})

    def _workspace_units(
        self, path: Path, overlay: Mapping[Path, str]
    ) -> WorkspaceUnits:
        root = find_workspace_root(path)
        if root is None:
            return WorkspaceUnits([], None)
        root = root.resolve()
        if root not in self._unit_indexes:
            self._unit_indexes[root] = UnitIndex(root)
        return self._unit_indexes[root].workspace_units(overlay)

    def _parameter_completions(
        self, path: Path, text: str, position: lsp.Position, overlay: Mapping[Path, str]
    ) -> list[lsp.CompletionItem]:
        if not looks_like_parameter_file(text):
            return []
        lines = text.split("\n")
        cursor = from_lsp_position(position, lines)

        def units() -> WorkspaceUnits:
            return self._workspace_units(path, overlay)

        candidates = parameter_candidates(text, cursor, units)
        return [to_lsp_completion_item(c, lines) for c in candidates]

    def completions(
        self,
        uri: str,
        text: str,
        position: lsp.Position,
        overlay: Mapping[Path, str] | None = None,
    ) -> list[lsp.CompletionItem]:
        """Complete requirement documents (metadata, links) and parameter files."""
        path = uri_to_path(uri)
        if path is not None and path.suffix == _YAML_SUFFIX:
            return self._parameter_completions(path, text, position, overlay or {})
        doc_type = self._document_type(path) if path else None
        if path is None or doc_type is None:
            return []
        lines = text.split("\n")
        cursor = from_lsp_position(position, lines)
        fields = self._config.field_definitions
        candidates = metadata_candidates(text, cursor, doc_type, fields)
        workspace = self._workspace(path, overlay or {})
        if workspace is not None:

            def files() -> list[str]:
                return self._link_files(workspace.root, overlay or {})

            candidates += link_candidates(text, cursor, workspace, files)

            def targets() -> list[LinkTarget]:
                return self._link_targets(workspace.root, overlay or {})

            candidates += link_insertion_candidates(text, cursor, targets)
        return [to_lsp_completion_item(c, lines) for c in candidates]

    def _diagnose_parameters(self, text: str) -> list[lsp.Diagnostic]:
        if not looks_like_parameter_file(text):
            return []
        lines = text.split("\n")
        return [to_lsp_diagnostic(d, lines) for d in diagnose_parameters(text)]

    def definition(
        self,
        uri: str,
        text: str,
        position: lsp.Position,
        overlay: Mapping[Path, str] | None = None,
    ) -> lsp.Location | None:
        """Return where the link at *position* in a FIRE document is defined."""
        path = uri_to_path(uri)
        if (
            path is None
            or model_for_suffix(self._config, self._models, str(path)) is None
        ):
            return None
        workspace = self._workspace(path, overlay or {})
        if workspace is None:
            return None
        cursor = from_lsp_position(position, text.split("\n"))
        target = definition_at(text, cursor, workspace, self._suffixes)
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
        elif model_for_suffix(self._config, self._models, str(path)) is not None:
            symbols = requirement_symbols(text)
        else:
            return []
        lines = text.split("\n")
        return [to_lsp_symbol(symbol, lines) for symbol in symbols]

    def _index_for(self, root: Path) -> WorkspaceIndex:
        if root not in self._indexes:
            self._indexes[root] = WorkspaceIndex(root, self._suffixes)
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
            self._link_indexes[root] = LinkIndex(root, self._suffixes)
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
        target = target_at(text, cursor, path.resolve(), workspace, self._suffixes)
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
        return model_for_suffix(self._config, self._models, str(path)) is not None
