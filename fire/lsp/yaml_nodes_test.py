#!/usr/bin/env python3
"""Tests for the position-aware YAML layer."""

import pytest

from fire.lsp.document_parser import Position, Range
from fire.lsp.yaml_nodes import (
    YamlSyntaxError,
    load_yaml,
    locate,
    parse_yaml,
    top_level_keys,
)

_TEXT = """max_speed_v1:
  value: 30.0
  unit: m/s
  description: Maximum speed

braking_table_v1:
  type: table
  columns:
    - name: velocity
      unit: m/s
  rows:
    - [10.0, 7.1]
    - [20.0, 28.6]
"""


def _at(text: str, needle: str, occurrence: int = 0) -> Range:
    offset = -1
    for _ in range(occurrence + 1):
        offset = text.index(needle, offset + 1)
    line = text.count("\n", 0, offset)
    start = offset - (text.rfind("\n", 0, offset) + 1)
    return Range(Position(line, start), Position(line, start + len(needle)))


class TestParseYaml:
    def test_empty_text_has_no_document(self):
        assert parse_yaml("") is None
        assert parse_yaml("# only a comment\n") is None

    def test_syntax_error_reports_message_and_position(self):
        with pytest.raises(YamlSyntaxError) as raised:
            parse_yaml("a:\n  b: [1, 2\nc: 3\n")
        assert raised.value.range.start.line >= 1
        assert raised.value.message

    def test_syntax_error_in_a_mapping(self):
        with pytest.raises(YamlSyntaxError):
            parse_yaml("a: b: c\n")


class TestTopLevelKeys:
    def test_keys_with_ranges(self):
        keys = top_level_keys(parse_yaml(_TEXT))
        assert list(keys) == ["max_speed_v1", "braking_table_v1"]
        assert keys["max_speed_v1"] == _at(_TEXT, "max_speed_v1")
        assert keys["braking_table_v1"] == _at(_TEXT, "braking_table_v1")

    def test_a_list_document_has_no_keys(self):
        assert top_level_keys(parse_yaml("- a\n- b\n")) == {}

    def test_no_document(self):
        assert top_level_keys(None) == {}


class TestLocate:
    def test_scalar_value_and_its_key(self):
        located = locate(parse_yaml(_TEXT), ["max_speed_v1", "unit"])
        assert located.value == _at(_TEXT, "m/s")
        assert located.key == _at(_TEXT, "unit")
        assert located.is_scalar

    def test_numeric_scalar(self):
        located = locate(parse_yaml(_TEXT), ["max_speed_v1", "value"])
        assert located.value == _at(_TEXT, "30.0")

    def test_mapping_value_is_not_a_scalar(self):
        located = locate(parse_yaml(_TEXT), ["max_speed_v1"])
        assert not located.is_scalar
        assert located.key == _at(_TEXT, "max_speed_v1")

    def test_sequence_items(self):
        root = parse_yaml(_TEXT)
        first = locate(root, ["braking_table_v1", "rows", 0])
        second = locate(root, ["braking_table_v1", "rows", 1])
        assert first.value == _at(_TEXT, "[10.0, 7.1]")
        assert second.value == _at(_TEXT, "[20.0, 28.6]")

    def test_nested_sequence_of_mappings(self):
        located = locate(parse_yaml(_TEXT), ["braking_table_v1", "columns", 0, "name"])
        assert located.value == _at(_TEXT, "velocity")

    @pytest.mark.parametrize(
        "path",
        [
            ["nope"],
            ["max_speed_v1", "nope"],
            ["braking_table_v1", "rows", 5],
            ["max_speed_v1", "unit", "deeper"],
            ["max_speed_v1", 0],
        ],
    )
    def test_unknown_paths(self, path):
        assert locate(parse_yaml(_TEXT), path) is None

    def test_empty_path_is_the_document(self):
        assert locate(parse_yaml(_TEXT), []) is not None

    def test_no_document(self):
        assert locate(None, ["a"]) is None


class TestLoadYaml:
    def test_loads_plain_data(self):
        assert load_yaml("a: 1\nb: [x, y]\n") == {"a": 1, "b": ["x", "y"]}

    def test_unsupported_tags_are_syntax_errors(self):
        with pytest.raises(YamlSyntaxError):
            load_yaml("a: !!python/object:os.system {}\n")

    def test_invalid_yaml(self):
        with pytest.raises(YamlSyntaxError):
            load_yaml("a: b: c\n")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
