#!/usr/bin/env python3
"""Tests for the position-aware requirement document parser."""

import pytest

from fire.lsp.document_parser import (
    Position,
    Range,
    parse_links,
    parse_requirements,
    parse_todos,
)


def _range(line: int, start: int, end: int) -> Range:
    return Range(Position(line, start), Position(line, end))


class TestRequirementHeadings:
    def test_heading_id_and_range(self):
        text = "# Title\n\n## REQ-001\n"
        (req,) = parse_requirements(text)
        assert req.id == "REQ-001"
        assert req.id_range == _range(2, 3, 10)

    def test_multiple_headings(self):
        text = "## A-1\n\n---\n\n## B-2\n"
        assert [r.id for r in parse_requirements(text)] == ["A-1", "B-2"]

    def test_subsection_headings_are_ignored(self):
        assert parse_requirements("### Rationale\n# Title\n") == []

    def test_invalid_id_is_still_reported(self):
        (req,) = parse_requirements("## req-lower\n")
        assert req.id == "req-lower"


class TestMetadataFields:
    def test_single_line_fields(self):
        text = "## R-1\n\nSIL: ASIL-D | Sec: false | Version: 4\n"
        (req,) = parse_requirements(text)
        assert [(f.key, f.value) for f in req.fields] == [
            ("SIL", "ASIL-D"),
            ("Sec", "false"),
            ("Version", "4"),
        ]

    def test_field_ranges(self):
        text = "## R-1\n\nSIL: ASIL-D | Version: 4\n"
        (req,) = parse_requirements(text)
        sil, version = req.fields
        assert sil.key_range == _range(2, 0, 3)
        assert sil.value_range == _range(2, 5, 11)
        assert version.key_range == _range(2, 14, 21)
        assert version.value_range == _range(2, 23, 24)

    def test_continuation_lines(self):
        text = "## R-1\n\nSIL: QM | Version: 1 |\nParent: TODO(KEY-1)\n"
        (req,) = parse_requirements(text)
        parent = req.fields[-1]
        assert parent.key == "Parent"
        assert parent.value == "TODO(KEY-1)"
        assert parent.value_range == _range(3, 8, 19)

    def test_multiple_parents_are_separate_fields(self):
        text = "## R-1\n\nVersion: 1 |\nParent: TODO(A-1) |\nParent: TODO(B-2)\n"
        (req,) = parse_requirements(text)
        assert [f.key for f in req.fields] == ["Version", "Parent", "Parent"]

    def test_empty_line_breaks_continuation(self):
        text = "## R-1\n\nSIL: QM |\n\nVersion: 1\n"
        (req,) = parse_requirements(text)
        assert [f.key for f in req.fields] == ["SIL"]

    def test_link_value_containing_colon_and_pipe_free(self):
        text = "## R-1\n\nParent: [R](/a.md?version=1#R)\n"
        (req,) = parse_requirements(text)
        assert req.fields[0].value == "[R](/a.md?version=1#R)"

    def test_heading_without_metadata(self):
        (req,) = parse_requirements("## R-1\n\nSome text.\n")
        assert req.fields == []

    def test_metadata_stops_at_next_heading(self):
        text = "## R-1\n\n## R-2\n\nVersion: 1\n"
        first, second = parse_requirements(text)
        assert first.fields == []
        assert [f.key for f in second.fields] == ["Version"]


class TestLinks:
    def test_requirement_link_parts(self):
        (link,) = parse_links("See [R-1](/a/b.sysreq.md?version=2#R-1).")
        assert link.text == "R-1"
        assert link.url == "/a/b.sysreq.md?version=2#R-1"
        assert link.path == "/a/b.sysreq.md"
        assert link.version == 2
        assert link.anchor == "R-1"

    def test_link_ranges(self):
        (link,) = parse_links("See [R-1](/a.md?version=1#R-1).")
        assert link.text_range == _range(0, 5, 8)
        assert link.url_range == _range(0, 10, 29)

    def test_link_on_later_line_and_multiple_per_line(self):
        first, second = parse_links(
            "text\n[@a](/p.yaml?version=1#a) [@b](/p.yaml?version=1#b)"
        )
        assert (first.text, first.text_range.start.line) == ("@a", 1)
        assert (second.text, second.text_range.start.character) == ("@b", 27)

    def test_missing_version_and_anchor(self):
        (link,) = parse_links("[R-1](/a.sysreq.md)")
        assert link.version is None
        assert link.anchor is None
        assert link.path == "/a.sysreq.md"

    def test_no_links(self):
        assert parse_links("plain [text] only") == []


class TestTodos:
    def test_valid_todo(self):
        (todo,) = parse_todos("Needs TODO(BRK-456) soon")
        assert todo.text == "TODO(BRK-456)"
        assert todo.valid
        assert todo.range == _range(0, 6, 19)

    def test_bare_todo_is_invalid(self):
        (todo,) = parse_todos("a\nTODO fix this")
        assert todo.text == "TODO"
        assert not todo.valid
        assert todo.range == _range(1, 0, 4)

    def test_malformed_todo_is_invalid(self):
        (todo,) = parse_todos("TODO(abc)")
        assert todo.text == "TODO(abc)"
        assert not todo.valid

    def test_no_todos(self):
        assert parse_todos("nothing here") == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
