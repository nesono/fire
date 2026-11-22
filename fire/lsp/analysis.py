#!/usr/bin/env python3
"""Analyze one document: pick its metadata model and produce LSP diagnostics."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from lsprotocol import types as lsp

from fire.lsp.conversion import to_lsp_diagnostic
from fire.lsp.diagnostics import diagnose_requirements
from fire.lsp.reference_diagnostics import ReferenceChecker
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

    def _references(self, path: str) -> ReferenceChecker | None:
        root = find_workspace_root(Path(path))
        if root is None:
            return None
        return ReferenceChecker(Workspace(root), self._suffixes)

    def diagnose(self, uri: str, text: str) -> list[lsp.Diagnostic]:
        path = unquote(urlparse(uri).path)
        model = model_for_suffix(self._config, self._models, path)
        if model is None:
            return []
        lines = text.split("\n")
        return [
            to_lsp_diagnostic(diagnostic, lines)
            for diagnostic in diagnose_requirements(text, model, self._references(path))
        ]
