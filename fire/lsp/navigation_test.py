#!/usr/bin/env python3
"""Tests for resolving the definition behind a link."""

from pathlib import Path

import pytest

from fire.lsp.document_parser import Position, Range
from fire.lsp.navigation import definition_at, link_at
from fire.lsp.workspace import Workspace

_SUFFIXES = (".sysreq.md",)
_PARAMS = "max_speed_v1:\n  value: 1\nmax_speed_v2:\n  value: 2\n"
_OTHER = "# Doc\n\n## REQ-OTHER\n\nSIL: QM | Sec: false | Version: 3\n"
_FILE_START = Range(Position(0, 0), Position(0, 0))


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    (tmp_path / "params.yaml").write_text(_PARAMS)
    (tmp_path / "other.sysreq.md").write_text(_OTHER)
    (tmp_path / "notes.md").write_text("# Notes\n")
    return Workspace(tmp_path)


def _param(version: int = 2, name: str = "max_speed", path: str = "/params.yaml"):
    return f"See [@{name}]({path}?version={version}#{name})."


def _definition(workspace, text: str, character: int = 8, line: int = 0):
    return definition_at(text, Position(line, character), workspace, _SUFFIXES)


class TestLinkAt:
    def test_cursor_on_text_or_url(self):
        text = "See [@a](/p.yaml?version=1#a) here"
        assert link_at(text, Position(0, 6)).text == "@a"
        assert link_at(text, Position(0, 20)).text == "@a"

    def test_whole_link_including_brackets_counts(self):
        text = "See [@a](/p.yaml?version=1#a) here"
        assert link_at(text, Position(0, 4)) is not None
        assert link_at(text, Position(0, 28)) is not None

    def test_outside_the_link(self):
        text = "See [@a](/p.yaml?version=1#a) here"
        assert link_at(text, Position(0, 3)) is None
        assert link_at(text, Position(0, 29)) is None
        assert link_at(text, Position(1, 6)) is None

    def test_picks_the_link_under_the_cursor(self):
        text = "[@a](/p.yaml?version=1#a) [@b](/p.yaml?version=1#b)"
        assert link_at(text, Position(0, 28)).text == "@b"


class TestParameterDefinition:
    def test_exact_version(self, workspace):
        target = _definition(workspace, _param(1))
        assert target.path == (workspace.root / "params.yaml").resolve()
        assert target.range == Range(Position(0, 0), Position(0, 12))

    def test_other_version(self, workspace):
        target = _definition(workspace, _param(2))
        assert target.range.start.line == 2

    def test_unknown_version_goes_to_the_latest(self, workspace):
        assert _definition(workspace, _param(9)).range.start.line == 2

    def test_unknown_name_goes_to_the_file(self, workspace):
        target = _definition(workspace, _param(1, name="nope"))
        assert target.range == _FILE_START

    def test_missing_file_has_no_definition(self, workspace):
        assert _definition(workspace, _param(path="/gone.yaml")) is None


class TestRequirementDefinition:
    def _link(self, rid="REQ-OTHER", path="/other.sysreq.md"):
        return f"See [{rid}]({path}?version=3#{rid})."

    def test_goes_to_the_heading_id(self, workspace):
        target = _definition(workspace, self._link())
        assert target.path == (workspace.root / "other.sysreq.md").resolve()
        assert target.range == Range(Position(2, 3), Position(2, 12))

    def test_unknown_id_goes_to_the_file(self, workspace):
        assert _definition(workspace, self._link(rid="REQ-NOPE")).range == _FILE_START

    def test_plain_markdown_goes_to_the_file(self, workspace):
        target = _definition(workspace, self._link(path="/notes.md"))
        assert target.range == _FILE_START

    def test_parent_links_work(self, workspace):
        text = "SIL: QM | Sec: false | Version: 1 | Parent: " + self._link()
        assert _definition(workspace, text, character=55).range.start.line == 2


class TestNoDefinition:
    @pytest.mark.parametrize(
        "link",
        [
            "[docs](https://example.com/x)",
            "[@max_speed](params.yaml?version=1#max_speed)",
            "[@config](<TODO(PARAM-789)>)",
        ],
    )
    def test_unsupported_links(self, workspace, link):
        assert _definition(workspace, link, character=3) is None

    def test_cursor_not_on_a_link(self, workspace):
        assert _definition(workspace, "plain text", character=2) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
