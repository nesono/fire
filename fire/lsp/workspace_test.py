#!/usr/bin/env python3
"""Tests for workspace root discovery and link target reading."""

from pathlib import Path

import pytest

from fire.lsp.workspace import Workspace, find_workspace_root


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "MODULE.bazel").write_text("")
    (tmp_path / "reqs").mkdir()
    (tmp_path / "reqs" / "a.sysreq.md").write_text("## R-1\n")
    (tmp_path / "params.yaml").write_text("x_v1:\n")
    return tmp_path


class TestFindWorkspaceRoot:
    def test_finds_marker_in_ancestor(self, root):
        assert find_workspace_root(root / "reqs" / "a.sysreq.md") == root

    def test_returns_none_without_marker(self, tmp_path):
        assert find_workspace_root(tmp_path / "x.md") is None

    def test_nearest_marker_wins(self, root):
        (root / "reqs" / "WORKSPACE").write_text("")
        assert find_workspace_root(root / "reqs" / "a.sysreq.md") == root / "reqs"


class TestWorkspaceRead:
    def test_reads_repository_relative_path(self, root):
        assert Workspace(root).read("/reqs/a.sysreq.md") == "## R-1\n"

    def test_missing_file_is_none(self, root):
        assert Workspace(root).read("/reqs/missing.md") is None

    def test_path_outside_root_is_none(self, root, tmp_path_factory):
        outside = tmp_path_factory.mktemp("outside") / "secret.md"
        outside.write_text("secret")
        assert Workspace(root).read(f"/../{outside.parent.name}/secret.md") is None

    def test_path_must_start_with_slash(self, root):
        assert Workspace(root).read("reqs/a.sysreq.md") is None

    def test_directory_is_none(self, root):
        assert Workspace(root).read("/reqs") is None

    def test_overlay_wins_over_disk(self, root):
        workspace = Workspace(root, {root / "params.yaml": "y_v1:\n"})
        assert workspace.read("/params.yaml") == "y_v1:\n"

    def test_overlay_serves_unsaved_files(self, root):
        workspace = Workspace(root, {root / "new.md": "## N-1\n"})
        assert workspace.read("/new.md") == "## N-1\n"

    def test_generated_validated_yaml_fallback(self, root):
        (root / "gen_validated.yaml").write_text("g_v1:\n")
        assert Workspace(root).read("/gen.yaml") == "g_v1:\n"


class TestWorkspaceLocate:
    def test_returns_resolved_path_and_text(self, root):
        located = Workspace(root).locate("/reqs/a.sysreq.md")
        assert located == (
            (root / "reqs" / "a.sysreq.md").resolve(),
            "## R-1\n",
        )

    def test_validated_fallback_reports_the_file_actually_read(self, root):
        (root / "gen_validated.yaml").write_text("g_v1:\n")
        located = Workspace(root).locate("/gen.yaml")
        assert located == ((root / "gen_validated.yaml").resolve(), "g_v1:\n")

    def test_overlay_path_is_reported(self, root):
        overlay = {root / "new.md": "## N-1\n"}
        located = Workspace(root, overlay).locate("/new.md")
        assert located == ((root / "new.md").resolve(), "## N-1\n")

    def test_missing_file_is_none(self, root):
        assert Workspace(root).locate("/missing.md") is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
