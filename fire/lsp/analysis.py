#!/usr/bin/env python3
"""Analyze one document: pick its metadata model and produce LSP diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from lsprotocol import types as lsp

from fire.lsp.conversion import to_lsp_diagnostic
from fire.lsp.diagnostics import diagnose_requirements
from fire.lsp.reference_diagnostics import ReferenceChecker
from fire.lsp.uris import uri_to_path
from fire.lsp.workspace import Workspace, find_workspace_root
from fire.starlark.config_models import FireConfig
from fire.starlark.dynamic_requirement_model import (
    build_models_from_config,
    model_for_suffix,
)


class Analyzer:
    """Validates documents against the document types of a FIRE config."""

    def __init__(self, config: FireConfig) -> None:
        self._config = config
        self._models = build_models_from_config(config)
        self._suffixes = tuple(dt.suffix for dt in config.document_types.values())

    def _references(
        self, path: Path, overlay: Mapping[Path, str]
    ) -> ReferenceChecker | None:
        root = find_workspace_root(path)
        if root is None:
            return None
        return ReferenceChecker(Workspace(root, overlay), self._suffixes)

    def diagnose(
        self, uri: str, text: str, overlay: Mapping[Path, str] | None = None
    ) -> list[lsp.Diagnostic]:
        """Diagnose one document; *overlay* holds unsaved content of other files."""
        path = uri_to_path(uri)
        if path is None:
            return []
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
