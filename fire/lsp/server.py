#!/usr/bin/env python3
"""Language server that publishes FIRE diagnostics for open documents."""

from __future__ import annotations

from typing import Final

from lsprotocol import types as lsp
from pygls.lsp.server import LanguageServer

from fire.lsp.analysis import Analyzer
from fire.lsp.publisher import DiagnosticsPublisher
from fire.lsp.uris import document_overlay
from fire.starlark.config_models import FireConfig, load_config

_NAME: Final = "fire-ls"
_VERSION: Final = "0.1.0"
_WATCHED_GLOBS: Final = ("**/*.md", "**/*.yaml")
_WATCH_REGISTRATION_ID: Final = "fire-watch-linked-files"


def _publish(
    server: LanguageServer, uri: str, diagnostics: list[lsp.Diagnostic]
) -> None:
    server.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
    )


def _supports_watching(server: LanguageServer) -> bool:
    workspace = server.client_capabilities.workspace
    watching = workspace.did_change_watched_files if workspace else None
    return bool(watching and watching.dynamic_registration)


def _register_watching(server: LanguageServer) -> None:
    watchers = [lsp.FileSystemWatcher(glob_pattern=g) for g in _WATCHED_GLOBS]
    registration = lsp.Registration(
        id=_WATCH_REGISTRATION_ID,
        method=lsp.WORKSPACE_DID_CHANGE_WATCHED_FILES,
        register_options=lsp.DidChangeWatchedFilesRegistrationOptions(
            watchers=watchers
        ),
    )
    server.client_register_capability(
        lsp.RegistrationParams(registrations=[registration])
    )


def create_server(config: FireConfig | None = None) -> LanguageServer:
    """Create a server using *config*, or the built-in default configuration."""
    server = LanguageServer(_NAME, _VERSION)
    analyzer = Analyzer(config or load_config())
    publisher = DiagnosticsPublisher(
        analyzer, lambda uri, diagnostics: _publish(server, uri, diagnostics)
    )

    def open_documents() -> dict[str, str]:
        documents = server.workspace.text_documents
        return {uri: doc.source for uri, doc in documents.items()}

    def refresh(*_: object) -> None:
        publisher.refresh(open_documents())

    for method in (
        lsp.TEXT_DOCUMENT_DID_OPEN,
        lsp.TEXT_DOCUMENT_DID_CHANGE,
        lsp.TEXT_DOCUMENT_DID_CLOSE,
        lsp.WORKSPACE_DID_CHANGE_WATCHED_FILES,
    ):
        server.feature(method)(refresh)

    @server.feature(lsp.TEXT_DOCUMENT_DEFINITION)
    def definition(params: lsp.DefinitionParams) -> lsp.Location | None:
        documents = open_documents()
        uri = params.text_document.uri
        overlay = document_overlay(documents)
        return analyzer.definition(uri, documents[uri], params.position, overlay)

    @server.feature(lsp.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def document_symbol(params: lsp.DocumentSymbolParams) -> list[lsp.DocumentSymbol]:
        uri = params.text_document.uri
        text = open_documents().get(uri)
        return analyzer.document_symbols(uri, text) if text is not None else []

    @server.feature(lsp.INITIALIZED)
    def initialized(params: lsp.InitializedParams) -> None:
        if _supports_watching(server):
            _register_watching(server)

    return server
