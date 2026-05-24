#!/usr/bin/env python3
"""Tests for version_tracking helpers."""

import pytest

from fire.starlark.version_tracking import (
    build_param_version_map,
    build_requirement_version_map,
    merge_param_versions,
)


class TestBuildParamVersionMap:
    def test_none_returns_empty(self):
        assert build_param_version_map(None, "test.yaml") == {}

    def test_non_mapping_raises(self):
        with pytest.raises(ValueError, match="expected mapping"):
            build_param_version_map([1, 2], "test.yaml")

    def test_extracts_versioned_keys(self):
        data = {
            "speed_v1": {},
            "speed_v2": {},
            "wheel_count_v1": {},
        }
        assert build_param_version_map(data, "p.yaml") == {
            "speed": 2,
            "wheel_count": 1,
        }

    def test_skips_keys_without_version_suffix(self):
        data = {"plain": {}, "speed_v3": {}}
        assert build_param_version_map(data, "p.yaml") == {"speed": 3}

    def test_takes_highest_version_per_name(self):
        data = {"speed_v1": {}, "speed_v2": {}}
        assert build_param_version_map(data, "p.yaml") == {"speed": 2}


class TestBuildRequirementVersionMap:
    def test_empty_sections(self):
        assert build_requirement_version_map([]) == {}

    def test_collects_versions(self):
        sections = [
            {"id": "REQ-1", "metadata": {"version": 1}},
            {"id": "REQ-2", "metadata": {"version": 3}},
        ]
        assert build_requirement_version_map(sections) == {
            "REQ-1": 1,
            "REQ-2": 3,
        }

    def test_skips_sections_with_non_int_version(self):
        sections = [
            {"id": "REQ-1", "metadata": {"version": "TODO(X-1)"}},
            {"id": "REQ-2", "metadata": {"version": 2}},
        ]
        assert build_requirement_version_map(sections) == {"REQ-2": 2}

    def test_skips_sections_without_version(self):
        sections = [
            {"id": "REQ-1", "metadata": {}},
            {"id": "REQ-2", "metadata": {"version": 5}},
        ]
        assert build_requirement_version_map(sections) == {"REQ-2": 5}


class TestMergeParamVersions:
    def test_empty(self):
        assert merge_param_versions([]) == {}

    def test_single_map(self):
        assert merge_param_versions([{"x": 1, "y": 2}]) == {"x": 1, "y": 2}

    def test_merges_distinct_names(self):
        a = {"x": 1}
        b = {"y": 2}
        assert merge_param_versions([a, b]) == {"x": 1, "y": 2}

    def test_takes_highest_version(self):
        a = {"x": 1, "y": 3}
        b = {"x": 2, "y": 2}
        assert merge_param_versions([a, b]) == {"x": 2, "y": 3}

    def test_order_independent(self):
        a = {"x": 5}
        b = {"x": 2}
        assert merge_param_versions([a, b]) == {"x": 5}
        assert merge_param_versions([b, a]) == {"x": 5}
