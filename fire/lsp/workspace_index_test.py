#!/usr/bin/env python3
"""Tests for the cached workspace-wide symbol index."""

import os
from pathlib import Path

import pytest
from lsprotocol import types as lsp

from fire.lsp.document_types import DocumentTypes
from fire.lsp.workspace_index import WorkspaceIndex

_TYPES = DocumentTypes.for_suffixes((".sysreq.md", ".swreq.md"))
_REQ = "## REQ-A\n\nSIL: QM | Sec: false | Version: 1\n"
_PARAMS = "max_speed_v1:\n  value: 1\n"


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "reqs").mkdir()
    (tmp_path / "reqs" / "a.sysreq.md").write_text(_REQ)
    (tmp_path / "params.yaml").write_text(_PARAMS)
    return tmp_path


def _names(index: WorkspaceIndex, overlay=None) -> list[str]:
    return [s.name for s in index.symbols(overlay or {})]


class TestScan:
    def test_finds_requirements_and_parameters(self, root):
        assert _names(WorkspaceIndex(root, _TYPES)) == ["max_speed_v1", "REQ-A"]

    def test_symbol_location_and_container(self, root):
        symbols = {s.name: s for s in WorkspaceIndex(root, _TYPES).symbols({})}
        req = symbols["REQ-A"]
        assert req.location.uri == (root / "reqs" / "a.sysreq.md").resolve().as_uri()
        assert req.location.range.start == lsp.Position(0, 3)
        assert req.container == "reqs/a.sysreq.md"
        assert req.kind == lsp.SymbolKind.Key
        assert symbols["max_speed_v1"].kind == lsp.SymbolKind.Constant

    def test_files_of_other_types_are_ignored(self, root):
        (root / "README.md").write_text(_REQ)
        (root / "notes.txt").write_text(_REQ)
        assert "REQ-A" in _names(WorkspaceIndex(root, _TYPES))
        assert _names(WorkspaceIndex(root, _TYPES)).count("REQ-A") == 1

    @pytest.mark.parametrize(
        "ignored", [".git", ".github", "bazel-bin", "node_modules"]
    )
    def test_ignored_directories_are_not_scanned(self, root, ignored):
        (root / ignored).mkdir()
        (root / ignored / "x.sysreq.md").write_text("## REQ-HIDDEN\n")
        assert "REQ-HIDDEN" not in _names(WorkspaceIndex(root, _TYPES))

    def test_symlinked_directories_are_not_followed(self, root, tmp_path_factory):
        outside = tmp_path_factory.mktemp("outside")
        (outside / "x.sysreq.md").write_text("## REQ-OUTSIDE\n")
        (root / "link").symlink_to(outside, target_is_directory=True)
        assert "REQ-OUTSIDE" not in _names(WorkspaceIndex(root, _TYPES))

    def test_results_are_ordered_by_path_then_position(self, root):
        (root / "reqs" / "b.sysreq.md").write_text("## REQ-C\n\n## REQ-B\n")
        names = _names(WorkspaceIndex(root, _TYPES))
        assert names == ["max_speed_v1", "REQ-A", "REQ-C", "REQ-B"]


class TestCache:
    def test_unchanged_files_are_served_from_the_cache(self, root):
        index = WorkspaceIndex(root, _TYPES)
        path = root / "reqs" / "a.sysreq.md"
        stamp = path.stat().st_mtime_ns
        index.symbols({})
        path.write_text(_REQ.replace("REQ-A", "REQ-Z"))
        os.utime(path, ns=(stamp, stamp))
        assert "REQ-A" in _names(index)

    def test_modified_files_are_reparsed(self, root):
        index = WorkspaceIndex(root, _TYPES)
        index.symbols({})
        path = root / "reqs" / "a.sysreq.md"
        path.write_text(_REQ.replace("REQ-A", "REQ-Z"))
        later = path.stat().st_mtime_ns + 10_000_000_000
        os.utime(path, ns=(later, later))
        assert "REQ-Z" in _names(index)
        assert "REQ-A" not in _names(index)

    def test_deleted_files_disappear(self, root):
        index = WorkspaceIndex(root, _TYPES)
        index.symbols({})
        (root / "params.yaml").unlink()
        assert "max_speed_v1" not in _names(index)

    def test_new_files_appear(self, root):
        index = WorkspaceIndex(root, _TYPES)
        index.symbols({})
        (root / "new.swreq.md").write_text("## REQ-NEW\n")
        assert "REQ-NEW" in _names(index)


class TestOverlay:
    def test_open_document_wins_over_disk(self, root):
        overlay = {root / "reqs" / "a.sysreq.md": "## REQ-EDITED\n"}
        names = _names(WorkspaceIndex(root, _TYPES), overlay)
        assert "REQ-EDITED" in names
        assert "REQ-A" not in names

    def test_unsaved_new_document_is_included(self, root):
        overlay = {root / "unsaved.sysreq.md": "## REQ-UNSAVED\n"}
        assert "REQ-UNSAVED" in _names(WorkspaceIndex(root, _TYPES), overlay)

    def test_overlay_does_not_leak_into_the_cache(self, root):
        index = WorkspaceIndex(root, _TYPES)
        index.symbols({root / "reqs" / "a.sysreq.md": "## REQ-EDITED\n"})
        assert "REQ-A" in _names(index)

    def test_overlay_outside_the_root_is_ignored(self, root, tmp_path_factory):
        other = tmp_path_factory.mktemp("other") / "x.sysreq.md"
        assert "REQ-FAR" not in _names(
            WorkspaceIndex(root, _TYPES), {other: "## REQ-FAR\n"}
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
