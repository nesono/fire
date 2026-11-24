#!/usr/bin/env python3
"""Tests for the cached workspace-wide index of parameter and requirement links."""

from pathlib import Path

import pytest
from lsprotocol import types as lsp

from fire.lsp.link_index import LinkIndex

_SUFFIXES = (".sysreq.md", ".swreq.md")
_DOC = """## REQ-A

SIL: QM | Sec: false | Version: 1 | Parent: [REQ-P](/p.sysreq.md?version=2#REQ-P)

See [@max_speed](/params.yaml?version=1#max_speed) and
[docs](https://example.com) and [@rel](params.yaml?version=1#rel).
"""


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "a.sysreq.md").write_text(_DOC)
    return tmp_path


def _links(index: LinkIndex, overlay=None):
    return index.links(overlay or {})


class TestLinkIndex:
    def test_indexes_parameter_and_requirement_links_including_parents(self, root):
        links = _links(LinkIndex(root, _SUFFIXES))
        assert [(link.kind, link.name, link.version, link.path) for link in links] == [
            ("requirement", "REQ-P", 2, "/p.sysreq.md"),
            ("parameter", "max_speed", 1, "/params.yaml"),
        ]

    def test_unchecked_links_are_skipped(self, root):
        names = [link.name for link in _links(LinkIndex(root, _SUFFIXES))]
        assert "rel" not in names
        assert all("example" not in n for n in names)

    def test_parameter_link_without_anchor_uses_the_link_text(self, root):
        (root / "b.sysreq.md").write_text("[@wheel_count](/params.yaml?version=1)\n")
        names = [link.name for link in _links(LinkIndex(root, _SUFFIXES))]
        assert "wheel_count" in names

    def test_location_spans_the_whole_link(self, root):
        link = _links(LinkIndex(root, _SUFFIXES))[1]
        assert link.location.uri == (root / "a.sysreq.md").resolve().as_uri()
        assert link.location.range == lsp.Range(lsp.Position(4, 4), lsp.Position(4, 50))

    def test_columns_are_utf16(self, root):
        (root / "c.sysreq.md").write_text("😀 [@x](/p.yaml?version=1#x)\n")
        links = _links(LinkIndex(root, _SUFFIXES))
        link = next(link for link in links if link.name == "x")
        assert link.location.range.start.character == 3

    def test_only_requirement_files_are_scanned(self, root):
        (root / "params.yaml").write_text("[@y](/p.yaml?version=1#y)\n")
        (root / "README.md").write_text("[@z](/p.yaml?version=1#z)\n")
        names = [link.name for link in _links(LinkIndex(root, _SUFFIXES))]
        assert "y" not in names and "z" not in names

    def test_open_documents_win_over_disk(self, root):
        overlay = {root / "a.sysreq.md": "[@edited](/p.yaml?version=1#edited)\n"}
        names = [link.name for link in _links(LinkIndex(root, _SUFFIXES), overlay)]
        assert names == ["edited"]


class TestReferenceStyleLinks:
    def test_usage_is_indexed_with_the_definitions_target(self, root):
        text = "See [@x][p] here.\n\n[p]: /params.yaml?version=3#x\n"
        (root / "r.sysreq.md").write_text(text)
        link = next(
            entry for entry in _links(LinkIndex(root, _SUFFIXES)) if entry.name == "x"
        )
        assert (link.kind, link.path, link.version) == ("parameter", "/params.yaml", 3)
        assert link.location.range == lsp.Range(lsp.Position(0, 4), lsp.Position(0, 11))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
