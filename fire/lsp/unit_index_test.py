#!/usr/bin/env python3
"""Tests for the index of units used in a workspace."""

from pathlib import Path

import pytest

from fire.lsp.unit_index import UnitIndex

_PARAMS = """a_v1:
  value: 1
  unit: m/s
  description: d
b_v1:
  value: 2
  unit: "1"
  description: d
c_v1:
  type: table
  columns:
    - name: x
      unit: m/s
    - unit: 'bar'  # pressure
      name: p
"""


def test_units_are_counted_and_unquoted_most_frequent_first(tmp_path: Path):
    (tmp_path / "params.yaml").write_text(_PARAMS)
    assert UnitIndex(tmp_path).units({}) == ["m/s", "1", "bar"]


def test_files_that_are_not_parameter_files_are_ignored(tmp_path: Path):
    (tmp_path / "ci.yaml").write_text("steps:\n  - unit: pytest\n")
    assert UnitIndex(tmp_path).units({}) == []


def test_units_from_several_files_add_up(tmp_path: Path):
    (tmp_path / "a.yaml").write_text("a_v1:\n  unit: kg\n")
    (tmp_path / "b.yaml").write_text("b_v1:\n  unit: kg\nc_v1:\n  unit: N\n")
    assert UnitIndex(tmp_path).units({}) == ["kg", "N"]


def test_open_documents_win_over_disk(tmp_path: Path):
    (tmp_path / "a.yaml").write_text("a_v1:\n  unit: kg\n")
    overlay = {tmp_path / "a.yaml": "a_v1:\n  unit: lbs\n"}
    assert UnitIndex(tmp_path).units(overlay) == ["lbs"]


def test_empty_values_are_skipped(tmp_path: Path):
    (tmp_path / "a.yaml").write_text("a_v1:\n  unit:\n  value: 1\n")
    assert UnitIndex(tmp_path).units({}) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
