#!/usr/bin/env python3
"""Tests for extracting definitions from requirement and parameter files."""

import pytest

from fire.lsp.document_parser import Position, Range
from fire.lsp.index import parameters_in, requirements_in

_REQS = """# Doc

## REQ-A

SIL: QM | Sec: false | Version: 4

Text.

## REQ-B

Version: 2

## REQ-C

No metadata.
"""

_PARAMS = """max_speed_v1:
  value: 30.0
  unit: m/s
  description: speed

max_speed_v2:
  value: 35.0
  unit: m/s
  description: speed

wheel_count_v1:
  value: 4
  unit: "1"
  description: wheels
"""


class TestRequirementsIn:
    def test_ids_and_versions(self):
        found = requirements_in(_REQS)
        assert {k: v.version for k, v in found.items()} == {
            "REQ-A": 4,
            "REQ-B": 2,
            "REQ-C": None,
        }

    def test_id_range(self):
        assert requirements_in(_REQS)["REQ-A"].range == Range(
            Position(2, 3), Position(2, 8)
        )

    def test_first_definition_wins(self):
        text = "## R-1\n\nVersion: 1\n\n## R-1\n\nVersion: 9\n"
        assert requirements_in(text)["R-1"].version == 1

    def test_non_integer_version_is_unknown(self):
        assert requirements_in("## R-1\n\nVersion: x\n")["R-1"].version is None


class TestParametersIn:
    def test_versions_per_base_name(self):
        found = parameters_in(_PARAMS)
        assert sorted(found["max_speed"].versions) == [1, 2]
        assert sorted(found["wheel_count"].versions) == [1]

    def test_version_key_range(self):
        rng = parameters_in(_PARAMS)["max_speed"].versions[2]
        assert rng == Range(Position(5, 0), Position(5, 12))

    def test_nested_keys_are_not_parameters(self):
        text = "a_v1:\n  b_v1: 1\n"
        assert list(parameters_in(text)) == ["a"]

    def test_similar_names_do_not_collide(self):
        found = parameters_in("max_speed_v1:\n  value: 1\n")
        assert "speed" not in found
        assert "max_speed" in found

    def test_keys_without_version_suffix_are_ignored(self):
        assert parameters_in("max_speed:\n  value: 1\n") == {}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
