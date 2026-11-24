#!/usr/bin/env python3
"""Tests for diagnostics on parameter YAML files."""

import pytest

from fire.lsp.diagnostic import Severity
from fire.lsp.document_parser import Position, Range
from fire.lsp.parameter_diagnostics import (
    diagnose_parameters,
    looks_like_parameter_file,
)

_VALID = """max_speed_v1:
  value: 30.0
  unit: m/s
  description: Maximum speed

wheel_count_v1:
  value: 4
  unit: "1"
  description: Wheels
"""


def _at(text: str, needle: str, occurrence: int = 0) -> Range:
    offset = -1
    for _ in range(occurrence + 1):
        offset = text.index(needle, offset + 1)
    line = text.count("\n", 0, offset)
    start = offset - (text.rfind("\n", 0, offset) + 1)
    return Range(Position(line, start), Position(line, start + len(needle)))


def _param(key: str, body: str = "value: 1\n  unit: m\n  description: d") -> str:
    return f"{key}:\n  {body}\n"


class TestValidFiles:
    def test_valid_file_has_no_diagnostics(self):
        assert diagnose_parameters(_VALID) == []

    def test_two_consecutive_versions_are_fine(self):
        text = _param("a_v1") + _param("a_v2")
        assert diagnose_parameters(text) == []

    def test_valid_table(self):
        text = (
            "t_v1:\n  type: table\n  description: d\n  columns:\n    - name: x\n"
            "      unit: m\n  rows:\n    - [1.0]\n    - [2.0]\n"
        )
        assert diagnose_parameters(text) == []


class TestSyntaxErrors:
    def test_invalid_yaml(self):
        (diag,) = diagnose_parameters("a_v1:\n  value: [1, 2\nb_v1: 3\n")
        assert (diag.code, diag.severity) == ("FIRE017", Severity.ERROR)
        assert diag.range.start.line >= 1

    def test_unsupported_tag(self):
        (diag,) = diagnose_parameters("a_v1: !!python/object:os.system {}\n")
        assert diag.code == "FIRE017"


class TestFieldErrors:
    def test_missing_unit_is_one_diagnostic_at_the_parameter(self):
        text = "a_v1:\n  value: 1\n  description: d\n"
        (diag,) = diagnose_parameters(text)
        assert (diag.code, diag.severity) == ("FIRE018", Severity.ERROR)
        assert diag.range == _at(text, "a_v1")
        assert "unit" in diag.message

    def test_no_noise_from_other_parameter_types(self):
        text = "a_v1:\n  value: 1\n  description: d\n"
        (diag,) = diagnose_parameters(text)
        assert "Parameter'" not in diag.message and "I64" not in diag.message

    def test_empty_description_points_at_the_value(self):
        text = "a_v1:\n  value: 1\n  unit: m\n  description: ''\n"
        (diag,) = diagnose_parameters(text)
        assert diag.range == _at(text, "''")

    def test_unknown_field_points_at_its_key(self):
        text = _param("a_v1", "value: 1\n  unit: m\n  description: d\n  extra: 1")
        (diag,) = diagnose_parameters(text)
        assert diag.range == _at(text, "extra")

    def test_scalar_where_a_parameter_is_expected_points_at_the_scalar(self):
        text = "a_v1: 5\n"
        (diag,) = diagnose_parameters(text)
        assert diag.range == _at(text, "5")
        assert "mapping" in diag.message

    def test_only_the_broken_parameter_is_reported(self):
        text = _VALID + "broken_v1:\n  value: 1\n  description: d\n"
        (diag,) = diagnose_parameters(text)
        assert diag.range == _at(text, "broken_v1")

    def test_table_without_rows(self):
        text = "t_v1:\n  type: table\n  description: d\n  columns:\n    - name: x\n      unit: m\n"
        diagnostics = diagnose_parameters(text)
        assert [d.range for d in diagnostics] == [_at(text, "t_v1")]


class TestRootLevelErrors:
    def test_key_that_does_not_match_the_pattern(self):
        text = _param("maxSpeed_v1")
        (diag,) = diagnose_parameters(text)
        assert diag.range == _at(text, "maxSpeed_v1")
        assert "must match pattern" in diag.message

    def test_version_gap_points_at_both_keys(self):
        text = _param("a_v1") + _param("a_v3")
        ranges = [d.range for d in diagnose_parameters(text)]
        assert ranges == [_at(text, "a_v1"), _at(text, "a_v3")]

    def test_more_than_two_versions(self):
        text = _param("a_v1") + _param("a_v2") + _param("a_v3")
        diagnostics = diagnose_parameters(text)
        assert len(diagnostics) == 3
        assert all("must not exceed two" in d.message for d in diagnostics)

    def test_explicit_type_on_a_scalar(self):
        text = _param("a_v1", "type: f64\n  value: 1.0\n  unit: m\n  description: d")
        (diag,) = diagnose_parameters(text)
        assert diag.range == _at(text, "a_v1")
        assert "type" in diag.message

    def test_table_row_shape(self):
        text = (
            "t_v1:\n  type: table\n  description: d\n  columns:\n    - name: x\n"
            "      unit: m\n  rows:\n    - [1.0, 2.0]\n"
        )
        (diag,) = diagnose_parameters(text)
        assert diag.range == _at(text, "t_v1")
        assert "Row 0" in diag.message

    def test_parameters_generating_the_same_identifier(self):
        text = _param("speed_v1") + _param(
            "speed_m_v1", "value: 1\n  unit: '1'\n  description: d"
        )
        ranges = [d.range for d in diagnose_parameters(text)]
        assert ranges == [_at(text, "speed_v1"), _at(text, "speed_m_v1")]

    def test_non_finite_value(self):
        text = _param("a_v1", "value: .nan\n  unit: m\n  description: d")
        (diag,) = diagnose_parameters(text)
        assert diag.range == _at(text, "a_v1")

    def test_document_that_is_not_a_mapping(self):
        (diag,) = diagnose_parameters("- a\n- b\n")
        assert diag.code == "FIRE018"
        assert diag.range.start == Position(0, 0)


class TestLooksLikeParameterFile:
    def test_valid_parameter_file(self):
        assert looks_like_parameter_file(_VALID)

    def test_a_wrongly_cased_key_still_counts(self):
        assert looks_like_parameter_file("maxSpeed_v1:\n  value: 1\n")

    def test_a_file_with_a_syntax_error_still_counts(self):
        assert looks_like_parameter_file("a_v1:\n  value: [1, 2\n")

    def test_the_first_version_marker_is_enough(self):
        assert looks_like_parameter_file("# comment\n\nb_v2:\n  value: 1\n")

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "name: ci\non: push\njobs:\n  build:\n    runs-on: ubuntu\n",
            "services:\n  web_v1:\n    image: x\n",
            "# a_v1:\n",
            "version: 1\nname_version1: x\n",
            "- a_v1: 1\n",
        ],
    )
    def test_other_yaml_files_do_not(self, text):
        assert not looks_like_parameter_file(text)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
