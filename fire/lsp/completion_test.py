#!/usr/bin/env python3
"""Tests for metadata completion in requirement documents."""

import pytest
from lsprotocol import types as lsp

from fire.lsp.completion import metadata_candidates
from fire.lsp.document_parser import Position, Range
from fire.starlark.config_models import DocumentTypeDefinition, load_config

_CONFIG = load_config()
_SYSREQ = _CONFIG.document_types["sysreq"]
_FIELDS = _CONFIG.field_definitions
_CURSOR = "§"


def _complete(marked: str, doc_type: DocumentTypeDefinition = _SYSREQ):
    before, _, after = marked.partition(_CURSOR)
    line = before.count("\n")
    character = len(before) - (before.rfind("\n") + 1)
    return metadata_candidates(
        before + after, Position(line, character), doc_type, _FIELDS
    )


def _labels(marked: str) -> list[str]:
    return [candidate.label for candidate in _complete(marked)]


class TestKeys:
    def test_all_fields_on_the_first_content_line_required_ones_first(self):
        assert _labels("## R-1\n\n§\n") == ["SIL", "Sec", "Version", "Parent"]

    def test_key_candidate_shape(self):
        sil = _complete("## R-1\n\n§\n")[0]
        assert sil.new_text == "SIL: "
        assert sil.kind == lsp.CompletionItemKind.Property
        assert sil.detail == "required"
        assert "Safety Integrity Level" in sil.documentation
        assert sil.replace == Range(Position(2, 0), Position(2, 0))

    def test_optional_fields_are_marked(self):
        parent = _complete("## R-1\n\n§\n")[-1]
        assert (parent.label, parent.detail) == ("Parent", "optional")

    def test_typed_prefix_is_replaced(self):
        candidate = _complete("## R-1\n\nSI§\n")[0]
        assert candidate.replace == Range(Position(2, 0), Position(2, 2))

    def test_fields_already_present_are_not_offered(self):
        assert _labels("## R-1\n\nSIL: QM | §\n") == ["Sec", "Version", "Parent"]

    def test_after_a_separator_the_range_starts_after_the_spaces(self):
        line = "SIL: QM |   "
        candidate = _complete(f"## R-1\n\n{line}§\n")[0]
        assert candidate.replace.start == Position(2, len(line))

    def test_the_field_being_edited_is_still_offered(self):
        assert "Sec" in _labels("## R-1\n\nSIL: QM | Se§c: false\n")

    def test_continuation_line(self):
        assert _labels("## R-1\n\nSIL: QM |\n§\n") == ["Sec", "Version", "Parent"]

    def test_second_requirement_has_its_own_metadata(self):
        marked = "## R-1\n\nSIL: QM | Sec: false | Version: 1\n\n---\n\n## R-2\n\n§\n"
        assert _labels(marked) == ["SIL", "Sec", "Version", "Parent"]

    def test_only_fields_of_the_document_type_are_offered(self):
        only_version = DocumentTypeDefinition(
            suffix=".x.md", display_name="X", required_fields=["version"]
        )
        labels = [c.label for c in _complete("## R-1\n\n§\n", only_version)]
        assert labels == ["Version"]


class TestValues:
    def test_enum_values_and_a_todo_snippet(self):
        labels = _labels("## R-1\n\nSIL: §\n")
        assert labels[:3] == ["ASIL-A", "ASIL-B", "ASIL-C"]
        assert "QM" in labels
        assert labels[-1] == "TODO(…)"

    def test_enum_value_shape(self):
        candidate = _complete("## R-1\n\nSIL: §\n")[0]
        assert candidate.kind == lsp.CompletionItemKind.EnumMember
        assert candidate.new_text == "ASIL-A"
        assert candidate.replace == Range(Position(2, 5), Position(2, 5))

    def test_partially_typed_value_is_replaced(self):
        candidate = _complete("## R-1\n\nSIL: AS§\n")[0]
        assert candidate.replace == Range(Position(2, 5), Position(2, 7))

    def test_todo_snippet(self):
        todo = _complete("## R-1\n\nSIL: §\n")[-1]
        assert todo.snippet
        assert todo.new_text == "TODO(${1:KEY}-${2:1234})"
        assert todo.kind == lsp.CompletionItemKind.Snippet

    def test_booleans(self):
        assert _labels("## R-1\n\nSec: §\n")[:2] == ["true", "false"]

    def test_values_after_a_separator(self):
        assert _labels("## R-1\n\nSIL: QM | Sec: §\n")[:2] == ["true", "false"]

    def test_integer_fields_have_nothing_to_offer(self):
        assert _labels("## R-1\n\nVersion: §\n") == []

    def test_parent_offers_only_a_todo(self):
        assert _labels("## R-1\n\nParent: §\n") == ["TODO(…)"]

    def test_keys_are_matched_case_insensitively(self):
        assert _labels("## R-1\n\nsil: §\n")[0] == "ASIL-A"

    def test_unknown_field_has_no_values(self):
        assert _labels("## R-1\n\nFoo: §\n") == []


class TestOutsideTheMetadataLine:
    @pytest.mark.parametrize(
        "marked",
        [
            "§\n",
            "# Title\n\n§\n",
            "## R-1§\n",
            "## R-1\n\nSIL: QM | Sec: false | Version: 1\n\n§\n",
            "## R-1\n\nSIL: QM | Sec: false | Version: 1\n\nSome text §\n",
            "## R-1\n\nThe system shall work.\n\nmore §\n",
            "## R-1\n\n```\n§\n```\n",
            "```\n## R-1\n\n§\n```\n",
        ],
    )
    def test_nothing_is_offered(self, marked):
        assert _complete(marked) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
