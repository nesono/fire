#!/usr/bin/env python3
"""Tests for the index of what a link can point at."""

from pathlib import Path

import pytest

from fire.lsp.link_targets import LinkTarget, LinkTargetIndex

_SUFFIXES = (".sysreq.md", ".swreq.md")
_REQS = "## REQ-A\n\nSIL: QM | Sec: false | Version: 3\n\n## REQ-NOVER\n\nText.\n"
_PARAMS = "max_speed_v1:\n  value: 1\nmax_speed_v2:\n  value: 2\nwheel_count_v1:\n  value: 4\n"


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "reqs").mkdir()
    (tmp_path / "reqs" / "a.sysreq.md").write_text(_REQS)
    (tmp_path / "params.yaml").write_text(_PARAMS)
    return tmp_path


class TestLinkTargetIndex:
    def test_requirements_and_parameters_with_their_latest_version(self, root):
        targets = LinkTargetIndex(root, _SUFFIXES).targets({})
        assert targets == [
            LinkTarget("parameter", "max_speed", 2, "/params.yaml"),
            LinkTarget("parameter", "wheel_count", 1, "/params.yaml"),
            LinkTarget("requirement", "REQ-A", 3, "/reqs/a.sysreq.md"),
            LinkTarget("requirement", "REQ-NOVER", None, "/reqs/a.sysreq.md"),
        ]

    def test_other_files_are_ignored(self, root):
        (root / "README.md").write_text(_REQS)
        paths = {t.path for t in LinkTargetIndex(root, _SUFFIXES).targets({})}
        assert paths == {"/params.yaml", "/reqs/a.sysreq.md"}

    def test_unsaved_documents_win_over_disk(self, root):
        overlay = {root / "reqs" / "a.sysreq.md": "## REQ-EDITED\n\nVersion: 7\n"}
        targets = LinkTargetIndex(root, _SUFFIXES).targets(overlay)
        assert (
            LinkTarget("requirement", "REQ-EDITED", 7, "/reqs/a.sysreq.md") in targets
        )
        assert all(t.name != "REQ-A" for t in targets)

    def test_unsaved_new_files_are_included(self, root):
        overlay = {root / "new.swreq.md": "## REQ-NEW\n\nVersion: 1\n"}
        targets = LinkTargetIndex(root, _SUFFIXES).targets(overlay)
        assert LinkTarget("requirement", "REQ-NEW", 1, "/new.swreq.md") in targets


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
