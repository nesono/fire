#!/usr/bin/env python3
"""Tests for completing the parts of a link URL."""

from pathlib import Path

import pytest
from lsprotocol import types as lsp

from fire.lsp.document_parser import Position, Range
from fire.lsp.link_completion import link_candidates
from fire.lsp.workspace import Workspace

_CURSOR = "§"
_REQS = "## REQ-A\n\nSIL: QM | Sec: false | Version: 3\n\n## REQ-B\n\nVersion: 1\n"
_PARAMS = "max_speed_v1:\n  value: 1\nmax_speed_v2:\n  value: 2\nwheel_count_v1:\n  value: 4\n"
_FILES = ["/params.yaml", "/reqs.sysreq.md"]


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    (tmp_path / "reqs.sysreq.md").write_text(_REQS)
    (tmp_path / "params.yaml").write_text(_PARAMS)
    return Workspace(tmp_path)


def _candidates(workspace, marked: str, files=_FILES):
    before, _, after = marked.partition(_CURSOR)
    line = before.count("\n")
    character = len(before) - (before.rfind("\n") + 1)
    return link_candidates(
        before + after, Position(line, character), workspace, lambda: files
    )


def _labels(workspace, marked: str) -> list[str]:
    return [c.label for c in _candidates(workspace, marked)]


class TestPaths:
    def test_all_files_after_the_opening_parenthesis(self, workspace):
        assert _labels(workspace, "See [REQ-A](§") == _FILES

    def test_path_shape(self, workspace):
        prefix = "See [@x]("
        params, _ = _candidates(workspace, prefix + "/§")
        assert params.new_text == "/params.yaml"
        assert params.kind == lsp.CompletionItemKind.File
        assert params.replace == Range(
            Position(0, len(prefix)), Position(0, len(prefix) + 1)
        )

    def test_typed_prefix_is_replaced(self, workspace):
        prefix = "See [x]("
        candidate = _candidates(workspace, prefix + "/re§")[0]
        assert candidate.replace == Range(
            Position(0, len(prefix)), Position(0, len(prefix) + 3)
        )

    def test_a_path_without_a_leading_slash_is_replaced_too(self, workspace):
        candidate = _candidates(workspace, "[x](re§")[0]
        assert candidate.replace == Range(Position(0, 4), Position(0, 6))

    def test_file_kind_is_in_the_detail(self, workspace):
        params, reqs = _candidates(workspace, "[x](§")
        assert (params.detail, reqs.detail) == ("parameter file", "requirement file")

    def test_reference_style_definition_line(self, workspace):
        assert _labels(workspace, "[1]: /§") == _FILES

    def test_nothing_outside_a_link_url(self, workspace):
        for marked in ("plain §", "[text]§", "[text](/a.md)§ more", "[1] §"):
            assert _candidates(workspace, marked) == []


class TestQuery:
    def test_version_parameter_is_offered_after_the_question_mark(self, workspace):
        line = "[x](/reqs.sysreq.md?"
        (candidate,) = _candidates(workspace, line + "§")
        assert candidate.new_text == "version="
        assert candidate.replace == Range(
            Position(0, len(line)), Position(0, len(line))
        )


class TestVersions:
    def test_requirement_current_version(self, workspace):
        (candidate,) = _candidates(workspace, "[REQ-A](/reqs.sysreq.md?version=§")
        assert (candidate.label, candidate.new_text) == ("3", "3")
        assert candidate.detail == "current version"

    def test_typed_digits_are_replaced(self, workspace):
        line = "[REQ-A](/reqs.sysreq.md?version="
        (candidate,) = _candidates(workspace, line + "1§")
        assert candidate.replace == Range(
            Position(0, len(line)), Position(0, len(line) + 1)
        )

    def test_parameter_versions_latest_first(self, workspace):
        candidates = _candidates(workspace, "[@max_speed](/params.yaml?version=§")
        assert [c.label for c in candidates] == ["2", "1"]
        assert [c.detail for c in candidates] == ["latest", "older"]

    def test_unknown_id_has_no_version(self, workspace):
        assert _candidates(workspace, "[REQ-Z](/reqs.sysreq.md?version=§") == []

    def test_missing_file_has_no_version(self, workspace):
        assert _candidates(workspace, "[REQ-A](/gone.sysreq.md?version=§") == []

    def test_the_anchor_after_the_cursor_names_the_target(self, workspace):
        marked = "[1]: /reqs.sysreq.md?version=§#REQ-B"
        assert [c.label for c in _candidates(workspace, marked)] == ["1"]

    def test_link_text_is_used_for_definition_labels(self, workspace):
        marked = "[@wheel_count]: /params.yaml?version=§"
        assert [c.label for c in _candidates(workspace, marked)] == ["1"]


class TestAnchors:
    def test_requirement_ids_with_their_versions(self, workspace):
        candidates = _candidates(workspace, "[x](/reqs.sysreq.md?version=3#§")
        assert [(c.label, c.detail) for c in candidates] == [
            ("REQ-A", "version 3"),
            ("REQ-B", "version 1"),
        ]
        assert candidates[0].kind == lsp.CompletionItemKind.Reference

    def test_parameter_base_names(self, workspace):
        candidates = _candidates(workspace, "[x](/params.yaml?version=1#§")
        assert [c.label for c in candidates] == ["max_speed", "wheel_count"]

    def test_typed_prefix_is_replaced(self, workspace):
        line = "[x](/reqs.sysreq.md?version=3#"
        candidate = _candidates(workspace, line + "RE§")[0]
        assert candidate.replace == Range(
            Position(0, len(line)), Position(0, len(line) + 2)
        )

    def test_the_linked_id_comes_first(self, workspace):
        candidates = _candidates(workspace, "[REQ-B](/reqs.sysreq.md?version=1#§")
        ordered = sorted(candidates, key=lambda c: c.sort_text)
        assert ordered[0].label == "REQ-B"

    def test_missing_file_has_no_anchors(self, workspace):
        assert _candidates(workspace, "[x](/gone.sysreq.md?version=1#§") == []


class TestLaziness:
    def test_files_are_only_listed_for_a_path(self, workspace):
        calls = []

        def files():
            calls.append(1)
            return _FILES

        for marked in (
            "[x](/reqs.sysreq.md?version=§",
            "[x](/reqs.sysreq.md?version=3#§",
            "plain §",
        ):
            before, _, after = marked.partition(_CURSOR)
            link_candidates(before + after, Position(0, len(before)), workspace, files)
        assert calls == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
