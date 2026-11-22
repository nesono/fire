#!/usr/bin/env python3
"""Language server that publishes FIRE diagnostics for open documents."""

from __future__ import annotations

from lsprotocol import types as lsp
from pygls.lsp.server import LanguageServer

from fire.lsp.analysis import Analyzer
from fire.starlark.config_models import FireConfig, load_config

_NAME = "fire-ls"
_VERSION = "0.1.0"


def _publish(
    server: LanguageServer, uri: str, diagnostics: list[lsp.Diagnostic]
) -> None:
    server.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
    )


def create_server(config: FireConfig | None = None) -> LanguageServer:
    """Create a server using *config*, or the built-in default configuration."""
    analyzer = Analyzer(config or load_config())
    server = LanguageServer(_NAME, _VERSION)

    def analyze(uri: str) -> None:
        text = server.workspace.get_text_document(uri).source
        _publish(server, uri, analyzer.diagnose(uri, text))

    @server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
    def did_open(params: lsp.DidOpenTextDocumentParams) -> None:
        analyze(params.text_document.uri)

    @server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params: lsp.DidChangeTextDocumentParams) -> None:
        analyze(params.text_document.uri)

    @server.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
    def did_close(params: lsp.DidCloseTextDocumentParams) -> None:
        _publish(server, params.text_document.uri, [])

    return server
