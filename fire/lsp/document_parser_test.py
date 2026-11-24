#!/usr/bin/env python3
"""Tests for the position-aware requirement document parser."""

import pytest

from fire.lsp.document_parser import (
    Position,
    Range,
    parse_link_definitions,
    parse_links,
    parse_requirements,
    parse_todos,
    parse_unresolved_references,
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

    def test_headings_in_fenced_code_are_ignored(self):
        text = "```markdown\n## REQ-IN-FENCE\n```\n\n## REQ-REAL\n"
        assert [r.id for r in parse_requirements(text)] == ["REQ-REAL"]

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


def _at(text: str, needle: str, occurrence: int = 0) -> Range:
    """The range of the *occurrence*-th *needle* in a multi-line *text*."""
    offset = -1
    for _ in range(occurrence + 1):
        offset = text.index(needle, offset + 1)
    line = text.count("\n", 0, offset)
    start = offset - (text.rfind("\n", 0, offset) + 1)
    return _range(line, start, start + len(needle))


_DEFINITION = "[1]: /a.sysreq.md?version=2#REQ-1"
_EXPLICIT = f"See [REQ-1][1] here.\n\n{_DEFINITION}\n"


class TestLinkDefinitions:
    def test_label_url_and_ranges(self):
        definition = parse_link_definitions(_EXPLICIT)["1"]
        assert definition.url == "/a.sysreq.md?version=2#REQ-1"
        assert definition.label_range == _at(_EXPLICIT, "1", 2)
        assert definition.url_range == _at(_EXPLICIT, "/a.sysreq.md?version=2#REQ-1")

    def test_labels_are_case_and_whitespace_insensitive(self):
        text = "[My  Label]: /a.md\n"
        assert "my label" in parse_link_definitions(text)

    def test_first_definition_wins(self):
        text = "[a]: /first.md\n[a]: /second.md\n"
        assert parse_link_definitions(text)["a"].url == "/first.md"

    def test_must_start_the_line(self):
        assert parse_link_definitions("text [a]: /x.md\n") == {}

    def test_external_definition(self):
        text = "[UN ECE R13-H]: https://unece.org/x\n"
        assert parse_link_definitions(text)["un ece r13-h"].url == "https://unece.org/x"


class TestReferenceStyleLinks:
    def test_explicit_reference(self):
        (link,) = parse_links(_EXPLICIT)
        assert link.text == "REQ-1"
        assert (link.path, link.version, link.anchor) == ("/a.sysreq.md", 2, "REQ-1")
        assert link.text_range == _at(_EXPLICIT, "REQ-1")

    def test_url_range_points_at_the_definition(self):
        (link,) = parse_links(_EXPLICIT)
        assert link.url_range == _at(_EXPLICIT, "/a.sysreq.md?version=2#REQ-1")

    def test_span_is_the_usage(self):
        (link,) = parse_links(_EXPLICIT)
        assert link.span == _at(_EXPLICIT, "[REQ-1][1]")

    def test_implicit_reference(self):
        text = "See [@x][] here.\n\n[@x]: /p.yaml?version=1#x\n"
        (link,) = parse_links(text)
        assert (link.text, link.path, link.anchor) == ("@x", "/p.yaml", "x")
        assert link.span == _at(text, "[@x][]")

    def test_shortcut_reference(self):
        text = "See [@x] here.\n\n[@x]: /p.yaml?version=1#x\n"
        (link,) = parse_links(text)
        assert link.span == _at(text, "[@x]")

    def test_shortcut_followed_by_a_colon_is_not_a_link(self):
        text = "For each pair in [@x]: do it.\n\n[@x]: /p.yaml?version=1#x\n"
        assert parse_links(text) == []

    def test_undefined_shortcut_is_not_a_link(self):
        assert parse_links("see [maybe] later and [ ] checkbox\n") == []

    def test_labels_match_case_insensitively(self):
        text = "See [REQ-1][Ref].\n\n[ref]: /a.md?version=1#REQ-1\n"
        assert len(parse_links(text)) == 1

    def test_one_link_per_usage_of_the_same_definition(self):
        text = "[A][1] and [B][1]\n\n[1]: /a.md?version=1#A\n"
        assert [link.text for link in parse_links(text)] == ["A", "B"]

    def test_inline_links_still_work_next_to_reference_links(self):
        text = "[A](/a.md?version=1#A) and [B][1]\n\n[1]: /b.md?version=1#B\n"
        assert [(link.text, link.path) for link in parse_links(text)] == [
            ("A", "/a.md"),
            ("B", "/b.md"),
        ]

    def test_definition_lines_are_not_usages(self):
        assert parse_links("[1]: /a.md?version=1#A\n[1]: /a.md\n") == []

    def test_inline_span_is_unchanged(self):
        text = "See [@a](/p.yaml?version=1#a) here"
        (link,) = parse_links(text)
        assert link.span == _at(text, "[@a](/p.yaml?version=1#a)")


class TestUnresolvedReferences:
    def test_explicit_label_without_definition(self):
        text = "See [REQ-1][nope] here.\n"
        (ref,) = parse_unresolved_references(text)
        assert (ref.label, ref.text) == ("nope", "REQ-1")
        assert ref.range == _at(text, "nope")

    def test_implicit_label_without_definition(self):
        text = "See [REQ-1][] here.\n"
        (ref,) = parse_unresolved_references(text)
        assert ref.label == "REQ-1"
        assert ref.range == _at(text, "REQ-1")

    def test_defined_labels_are_resolved(self):
        assert parse_unresolved_references(_EXPLICIT) == []

    def test_shortcuts_are_never_unresolved(self):
        assert parse_unresolved_references("see [maybe] later\n") == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
