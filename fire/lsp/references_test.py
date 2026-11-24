#!/usr/bin/env python3
"""Tests for finding what links point at a requirement or a parameter."""

from pathlib import Path

import pytest
from lsprotocol import types as lsp

from fire.lsp.document_parser import Position, Range
from fire.lsp.link_index import IndexedLink
from fire.lsp.references import (
    ReferenceTarget,
    declaration_range,
    find_references,
    target_at,
)
from fire.lsp.workspace import Workspace

_SUFFIXES = (".sysreq.md",)
_REQS = "## REQ-A\n\nSIL: QM | Sec: false | Version: 3\n\n## REQ-B\n\nVersion: 1\n"
_PARAMS = "max_speed_v1:\n  value: 1\nmax_speed_v2:\n  value: 2\n"


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    (tmp_path / "reqs.sysreq.md").write_text(_REQS)
    (tmp_path / "params.yaml").write_text(_PARAMS)
    return Workspace(tmp_path)


def _target(workspace, path: str, text: str, line: int, character: int):
    full = (workspace.root / path).resolve()
    return target_at(text, Position(line, character), full, workspace, _SUFFIXES)


class TestTargetAt:
    def test_requirement_heading(self, workspace):
        target = _target(workspace, "reqs.sysreq.md", _REQS, 0, 5)
        assert target == ReferenceTarget(
            (workspace.root / "reqs.sysreq.md").resolve(), "requirement", "REQ-A", 3
        )

    def test_cursor_on_the_heading_marker_is_not_the_id(self, workspace):
        assert _target(workspace, "reqs.sysreq.md", _REQS, 0, 1) is None

    def test_parameter_version_key(self, workspace):
        target = _target(workspace, "params.yaml", _PARAMS, 2, 3)
        assert (target.kind, target.name, target.version) == (
            "parameter",
            "max_speed",
            2,
        )

    def test_cursor_in_a_parameter_value_is_not_a_target(self, workspace):
        assert _target(workspace, "params.yaml", _PARAMS, 1, 5) is None

    def test_parameter_link(self, workspace):
        text = "See [@max_speed](/params.yaml?version=1#max_speed).\n"
        target = _target(workspace, "x.sysreq.md", text, 0, 8)
        assert target.path == (workspace.root / "params.yaml").resolve()
        assert (target.kind, target.name, target.version) == (
            "parameter",
            "max_speed",
            1,
        )

    def test_requirement_link(self, workspace):
        text = "See [REQ-B](/reqs.sysreq.md?version=1#REQ-B).\n"
        target = _target(workspace, "x.sysreq.md", text, 0, 8)
        assert (target.kind, target.name) == ("requirement", "REQ-B")

    def test_link_to_a_missing_file_has_no_target(self, workspace):
        text = "See [@x](/gone.yaml?version=1#x).\n"
        assert _target(workspace, "x.sysreq.md", text, 0, 6) is None

    def test_plain_text_has_no_target(self, workspace):
        assert _target(workspace, "x.sysreq.md", "plain text\n", 0, 3) is None


def _link(workspace, path, kind, name, version, source="src.sysreq.md", line=0):
    rng = lsp.Range(lsp.Position(line, 0), lsp.Position(line, 5))
    location = lsp.Location((workspace.root / source).as_uri(), rng)
    return IndexedLink(location, path, kind, name, version)


class TestFindReferences:
    def _params_target(self, workspace, version=2):
        path = (workspace.root / "params.yaml").resolve()
        return ReferenceTarget(path, "parameter", "max_speed", version)

    def test_matches_by_file_kind_and_name(self, workspace):
        links = [
            _link(workspace, "/params.yaml", "parameter", "max_speed", 2, line=1),
            _link(workspace, "/params.yaml", "parameter", "other", 2, line=2),
            _link(workspace, "/other.yaml", "parameter", "max_speed", 2, line=3),
            _link(workspace, "/params.yaml", "requirement", "max_speed", 2, line=4),
        ]
        found = find_references(links, self._params_target(workspace), workspace.root)
        assert [link.location.range.start.line for link in found] == [1]

    def test_links_to_the_exact_version_come_first(self, workspace):
        links = [
            _link(workspace, "/params.yaml", "parameter", "max_speed", 1, line=1),
            _link(workspace, "/params.yaml", "parameter", "max_speed", 2, line=2),
            _link(workspace, "/params.yaml", "parameter", "max_speed", None, line=3),
            _link(workspace, "/params.yaml", "parameter", "max_speed", 2, line=4),
        ]
        found = find_references(links, self._params_target(workspace), workspace.root)
        assert [link.location.range.start.line for link in found] == [2, 4, 1, 3]

    def test_generated_validated_file_counts_as_the_same_file(self, workspace):
        (workspace.root / "gen_validated.yaml").write_text("x_v1:\n")
        target = ReferenceTarget(
            (workspace.root / "gen_validated.yaml").resolve(), "parameter", "x", 1
        )
        links = [_link(workspace, "/gen.yaml", "parameter", "x", 1)]
        assert find_references(links, target, workspace.root) == links

    def test_requirement_references(self, workspace):
        path = (workspace.root / "reqs.sysreq.md").resolve()
        target = ReferenceTarget(path, "requirement", "REQ-A", 3)
        links = [
            _link(workspace, "/reqs.sysreq.md", "requirement", "REQ-A", 3),
            _link(workspace, "/reqs.sysreq.md", "requirement", "REQ-B", 1),
        ]
        assert find_references(links, target, workspace.root) == links[:1]

    def test_no_references(self, workspace):
        assert find_references([], self._params_target(workspace), workspace.root) == []


class TestDeclarationRange:
    def _target(self, workspace, kind, name, version):
        return ReferenceTarget(workspace.root / "x", kind, name, version)

    def test_requirement_heading_id(self, workspace):
        target = self._target(workspace, "requirement", "REQ-B", 1)
        assert declaration_range(target, _REQS) == Range(Position(4, 3), Position(4, 8))

    def test_parameter_key_of_the_version(self, workspace):
        target = self._target(workspace, "parameter", "max_speed", 1)
        assert declaration_range(target, _PARAMS) == Range(
            Position(0, 0), Position(0, 12)
        )

    def test_unknown_parameter_version_uses_the_latest(self, workspace):
        target = self._target(workspace, "parameter", "max_speed", 9)
        assert declaration_range(target, _PARAMS).start.line == 2

    def test_missing_symbol(self, workspace):
        assert (
            declaration_range(self._target(workspace, "requirement", "NOPE", 1), _REQS)
            is None
        )
        assert (
            declaration_range(self._target(workspace, "parameter", "nope", 1), _PARAMS)
            is None
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
