#!/usr/bin/env python3
"""Re-analyze every open document and publish only what changed.

A document's diagnostics depend on other files, so a change in one document
can alter the diagnostics of another. Refreshing all open documents together
keeps them consistent, and remembering what was last published avoids
notifications that would not change anything on screen.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Protocol

from lsprotocol import types as lsp

from fire.lsp.uris import document_overlay


class _Analyzer(Protocol):
    def diagnose(
        self, uri: str, text: str, overlay: Mapping[Path, str]
    ) -> list[lsp.Diagnostic]: ...


Publish = Callable[[str, list[lsp.Diagnostic]], None]


class DiagnosticsPublisher:
    def __init__(self, analyzer: _Analyzer, publish: Publish) -> None:
        self._analyzer = analyzer
        self._publish = publish
        self._last: dict[str, list[lsp.Diagnostic]] = {}

    def refresh(self, documents: Mapping[str, str]) -> None:
        """Analyze all *documents* (uri to text) and publish any differences."""
        overlay = document_overlay(documents)
        for uri, text in documents.items():
            self._update(uri, self._analyzer.diagnose(uri, text, overlay))
        for uri in set(self._last) - set(documents):
            self._update(uri, [])

    def _update(self, uri: str, diagnostics: list[lsp.Diagnostic]) -> None:
        if self._last.get(uri, []) == diagnostics:
            return
        self._publish(uri, diagnostics)
        if diagnostics:
            self._last[uri] = diagnostics
        else:
            self._last.pop(uri, None)
