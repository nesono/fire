#!/usr/bin/env python3
"""Tests for refreshing and publishing diagnostics of open documents."""

from pathlib import Path

import pytest
from lsprotocol import types as lsp

from fire.lsp.publisher import DiagnosticsPublisher

_A = "file:///repo/a.sysreq.md"
_B = "file:///repo/b.sysreq.md"


def _diag(message: str) -> lsp.Diagnostic:
    rng = lsp.Range(lsp.Position(0, 0), lsp.Position(0, 1))
    return lsp.Diagnostic(range=rng, message=message)


class _FakeAnalyzer:
    def __init__(self) -> None:
        self.results: dict[str, list[lsp.Diagnostic]] = {}
        self.overlays: list[dict[Path, str]] = []

    def diagnose(self, uri, text, overlay):
        self.overlays.append(dict(overlay))
        return self.results.get(uri, [])


@pytest.fixture
def analyzer() -> _FakeAnalyzer:
    return _FakeAnalyzer()


@pytest.fixture
def published() -> list[tuple[str, list[lsp.Diagnostic]]]:
    return []


@pytest.fixture
def publisher(analyzer, published) -> DiagnosticsPublisher:
    return DiagnosticsPublisher(analyzer, lambda uri, d: published.append((uri, d)))


class TestRefresh:
    def test_publishes_new_diagnostics(self, publisher, analyzer, published):
        analyzer.results[_A] = [_diag("x")]
        publisher.refresh({_A: "text"})
        assert published == [(_A, [_diag("x")])]

    def test_unchanged_diagnostics_are_not_republished(
        self, publisher, analyzer, published
    ):
        analyzer.results[_A] = [_diag("x")]
        publisher.refresh({_A: "text"})
        publisher.refresh({_A: "text"})
        assert len(published) == 1

    def test_changed_diagnostics_are_republished(self, publisher, analyzer, published):
        analyzer.results[_A] = [_diag("x")]
        publisher.refresh({_A: "text"})
        analyzer.results[_A] = []
        publisher.refresh({_A: "text"})
        assert published[-1] == (_A, [])

    def test_clean_new_document_publishes_nothing(self, publisher, published):
        publisher.refresh({_A: "text"})
        assert published == []

    def test_closed_document_is_cleared_once(self, publisher, analyzer, published):
        analyzer.results[_A] = [_diag("x")]
        publisher.refresh({_A: "text"})
        publisher.refresh({})
        publisher.refresh({})
        assert published[1:] == [(_A, [])]

    def test_every_open_document_is_refreshed(self, publisher, analyzer, published):
        analyzer.results[_A] = [_diag("a")]
        analyzer.results[_B] = [_diag("b")]
        publisher.refresh({_A: "1", _B: "2"})
        assert {uri for uri, _ in published} == {_A, _B}


class TestOverlay:
    def test_overlay_holds_all_open_file_documents(self, publisher, analyzer):
        publisher.refresh({_A: "one", _B: "two", "untitled:1": "three"})
        assert analyzer.overlays[0] == {
            Path("/repo/a.sysreq.md"): "one",
            Path("/repo/b.sysreq.md"): "two",
        }


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
