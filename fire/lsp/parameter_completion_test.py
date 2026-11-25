#!/usr/bin/env python3
"""Tests for completion in parameter YAML files."""

import pytest
from lsprotocol import types as lsp

from fire.lsp.document_parser import Position, Range
from fire.lsp.parameter_completion import (
    COMMON_UNITS,
    WorkspaceUnits,
    parameter_candidates,
)

_CURSOR = "§"
_SCALAR = "max_speed_v1:\n  value: 30.0\n  description: Speed\n  §\n"
_TABLE = "t_v1:\n  type: table\n  description: d\n  columns:\n    - name: x\n      unit: m\n  §\n"


def _complete(marked: str, known_units=(), workspace_quoted=None):
    before, _, after = marked.partition(_CURSOR)
    line = before.count("\n")
    character = len(before) - (before.rfind("\n") + 1)
    workspace = WorkspaceUnits(list(known_units), workspace_quoted)
    return parameter_candidates(
        before + after, Position(line, character), lambda: workspace
    )


def _labels(marked: str, known_units=()) -> list[str]:
    return [c.label for c in _complete(marked, known_units)]


class TestParameterKeys:
    def test_scalar_fields_not_yet_present(self):
        assert _labels(_SCALAR) == ["unit", "type"]

    def test_empty_parameter_offers_everything(self):
        assert _labels("a_v1:\n  §\n") == ["value", "unit", "description", "type"]

    def test_candidate_shape(self):
        unit = _complete("a_v1:\n  §\n")[1]
        assert unit.new_text == "unit: "
        assert unit.kind == lsp.CompletionItemKind.Property
        assert unit.replace == Range(Position(1, 2), Position(1, 2))

    def test_typed_prefix_is_replaced(self):
        candidate = _complete("a_v1:\n  un§\n")[0]
        assert candidate.replace == Range(Position(1, 2), Position(1, 4))

    def test_a_table_offers_the_table_fields(self):
        assert _labels(_TABLE) == ["rows"]

    def test_table_before_rows_and_columns(self):
        text = "t_v1:\n  type: table\n  §\n"
        assert _labels(text) == ["description", "columns", "rows"]

    def test_second_parameter_in_the_file(self):
        text = (
            "a_v1:\n  value: 1\n  unit: m\n  description: d\nb_v1:\n  value: 2\n  §\n"
        )
        assert _labels(text) == ["unit", "description", "type"]

    def test_the_key_being_edited_does_not_count_as_present(self):
        assert "unit" in _labels("a_v1:\n  value: 1\n  un§it: m\n")

    def test_parameter_names_are_not_completed(self):
        assert _labels("§\n") == []
        assert _labels("a_v1:\n  value: 1\nb§\n") == []


class TestColumnKeys:
    def test_new_list_item(self):
        text = "t_v1:\n  type: table\n  columns:\n    - §\n"
        assert _labels(text) == ["name", "unit"]

    def test_marker_and_prefix(self):
        text = "t_v1:\n  type: table\n  columns:\n    - na§\n"
        candidate = _complete(text)[0]
        assert candidate.replace == Range(Position(3, 6), Position(3, 8))

    def test_continuation_line_skips_keys_of_the_item(self):
        text = "t_v1:\n  type: table\n  columns:\n    - name: x\n      §\n"
        assert _labels(text) == ["unit"]

    def test_a_new_item_starts_over(self):
        text = (
            "t_v1:\n  type: table\n  columns:\n    - name: x\n      unit: m\n    - §\n"
        )
        assert _labels(text) == ["name", "unit"]

    def test_rows_have_no_keys(self):
        text = "t_v1:\n  type: table\n  rows:\n    - [1, §\n"
        assert _labels(text) == []


class TestValues:
    def test_type_can_only_be_table(self):
        assert _labels("a_v1:\n  type: §\n") == ["table"]

    def test_units_workspace_first_then_common(self):
        labels = _labels("a_v1:\n  unit: §\n", ["bar", "m/s"])
        assert labels[:2] == ["bar", "m/s"]
        assert set(COMMON_UNITS) <= set(labels)
        assert labels.count("m/s") == 1

    def test_superscript_units_are_offered_without_any_workspace_units(self):
        labels = _labels("a_v1:\n  unit: §\n")
        assert {"m/s", "m/s²", "m²", "m³"} <= set(labels)

    def test_detail_tells_where_a_unit_comes_from(self):
        candidates = _complete("a_v1:\n  unit: §\n", ["bar"])
        assert candidates[0].detail == "used in this workspace"
        assert candidates[-1].detail == "common unit"

    def test_typed_unit_is_replaced(self):
        candidate = _complete("a_v1:\n  unit: m§\n")[0]
        assert candidate.replace == Range(Position(1, 8), Position(1, 9))

    def test_units_that_would_not_parse_as_text_are_quoted_even_in_plain_style(self):
        candidates = _complete("a_v1:\n  unit: §\n", ["1", "%", "m/s"], False)
        by_label = {c.label: c.new_text for c in candidates}
        assert by_label["1"] == '"1"'
        assert by_label["%"] == '"%"'
        assert by_label["m/s"] == "m/s"

    def test_column_units(self):
        text = "t_v1:\n  type: table\n  columns:\n    - name: x\n      unit: §\n"
        assert "m/s" in _labels(text)

    def test_unit_on_a_list_marker_line(self):
        text = "t_v1:\n  type: table\n  columns:\n    - unit: §\n"
        assert "m/s" in _labels(text)

    @pytest.mark.parametrize("key", ["value", "description", "name"])
    def test_free_text_fields_have_no_completions(self, key):
        assert _labels(f"a_v1:\n  {key}: §\n") == []


def _new_text(marked: str, label: str = "m/s", **options) -> str:
    return {c.label: c.new_text for c in _complete(marked, **options)}[label]


class TestQuotingStyle:
    _QUOTED = (
        'a_v1:\n  unit: "m"\nb_v1:\n  unit: "s"\nc_v1:\n  unit: kg\nd_v1:\n  unit: §\n'
    )
    _PLAIN = (
        'a_v1:\n  unit: m\nb_v1:\n  unit: s\nc_v1:\n  unit: "1"\nd_v1:\n  unit: §\n'
    )

    def test_follows_a_file_that_mostly_quotes_units(self):
        assert _new_text(self._QUOTED) == '"m/s"'

    def test_follows_a_file_that_mostly_writes_plain_units(self):
        assert _new_text(self._PLAIN) == "m/s"

    def test_the_document_wins_over_the_workspace(self):
        assert _new_text(self._QUOTED, workspace_quoted=False) == '"m/s"'
        assert _new_text(self._PLAIN, workspace_quoted=True) == "m/s"

    def test_a_tie_falls_back_to_the_workspace(self):
        tie = 'a_v1:\n  unit: "m"\nb_v1:\n  unit: s\nc_v1:\n  unit: §\n'
        assert _new_text(tie, workspace_quoted=False) == "m/s"
        assert _new_text(tie, workspace_quoted=True) == '"m/s"'

    def test_without_any_signal_units_are_quoted(self):
        assert _new_text("a_v1:\n  unit: §\n") == '"m/s"'

    def test_column_units_count_too(self):
        text = 't_v1:\n  type: table\n  columns:\n    - name: x\n      unit: "m"\n    - name: y\n      unit: §\n'
        assert _new_text(text) == '"m/s"'


class TestTypedQuotes:
    def test_an_opening_quote_is_kept_and_part_of_the_replacement(self):
        candidate = {c.label: c for c in _complete('a_v1:\n  unit: "m§\n')}["m/s"]
        assert candidate.new_text == '"m/s"'
        assert candidate.replace == Range(Position(1, 8), Position(1, 10))
        assert candidate.filter_text == '"m/s'

    def test_an_auto_paired_closing_quote_is_consumed(self):
        candidate = {c.label: c for c in _complete('a_v1:\n  unit: "m§"\n')}["m/s"]
        assert candidate.replace == Range(Position(1, 8), Position(1, 11))

    def test_single_quotes_stay_single(self):
        by_label = {c.label: c.new_text for c in _complete("a_v1:\n  unit: 'm§'\n")}
        assert by_label["m/s"] == "'m/s'"

    def test_a_quote_inside_a_unit_is_escaped(self):
        assert (
            _new_text('a_v1:\n  unit: "§"\n', 'a"b', known_units=['a"b']) == '"a\\"b"'
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
