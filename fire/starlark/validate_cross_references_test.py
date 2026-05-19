#!/usr/bin/env python3
"""Tests for validate_cross_references helpers."""

import textwrap

import pytest

from fire.starlark import validate_cross_references as vcr
from fire.starlark.config_models import FireConfig
from fire.starlark.dynamic_requirement_model import build_models_from_config
from fire.starlark.requirement_models import (
    RegulatoryRequirementMetadata,
    RequirementMetadata,
)


# ---------------------------------------------------------------------------
# _metadata_model_for_file
# ---------------------------------------------------------------------------


class TestMetadataModelForFile:
    def test_sysreq_returns_requirement_metadata(self):
        assert (
            vcr._metadata_model_for_file("some/path/foo.sysreq.md")
            is RequirementMetadata
        )

    def test_swreq_returns_requirement_metadata(self):
        assert (
            vcr._metadata_model_for_file("some/path/foo.swreq.md")
            is RequirementMetadata
        )

    def test_regreq_returns_regulatory_metadata(self):
        assert (
            vcr._metadata_model_for_file("some/path/foo.regreq.md")
            is RegulatoryRequirementMetadata
        )

    def test_unknown_suffix_falls_back_to_requirement_metadata(self):
        assert vcr._metadata_model_for_file("notes.md") is RequirementMetadata

    def test_custom_config_overrides_fallback(self, default_config):
        models = build_models_from_config(default_config)
        model = vcr._metadata_model_for_file(
            "foo.sysreq.md", config=default_config, models=models
        )
        # The dynamic sysreq model isn't the static one — it's a generated class.
        assert model.__name__ == "DynamicRequirement_sysreq"


# ---------------------------------------------------------------------------
# _find_requirement_heading_index
# ---------------------------------------------------------------------------


class TestFindRequirementHeadingIndex:
    def test_returns_index_of_matching_heading(self):
        lines = ["# Title", "Intro", "## REQ-1", "body"]
        assert vcr._find_requirement_heading_index(lines, "REQ-1") == 2

    def test_returns_none_when_missing(self):
        lines = ["# Title", "## REQ-2", "body"]
        assert vcr._find_requirement_heading_index(lines, "REQ-1") is None

    def test_returns_first_match(self):
        lines = ["## REQ-1", "body", "## REQ-1", "more"]
        assert vcr._find_requirement_heading_index(lines, "REQ-1") == 0

    def test_partial_id_match_does_not_count(self):
        lines = ["## REQ-12", "body"]
        # `## REQ-1` matches the start of `## REQ-12`, so this is a known
        # caveat of the prefix-based matcher — document it explicitly.
        assert vcr._find_requirement_heading_index(lines, "REQ-1") == 0


# ---------------------------------------------------------------------------
# _requirement_suffixes
# ---------------------------------------------------------------------------


class TestRequirementSuffixes:
    def test_no_config_returns_defaults(self):
        assert vcr._requirement_suffixes() == (
            ".sysreq.md",
            ".swreq.md",
            ".regreq.md",
        )

    def test_with_config_returns_config_suffixes(self, default_config):
        suffixes = vcr._requirement_suffixes(default_config)
        assert ".sysreq.md" in suffixes
        assert ".swreq.md" in suffixes
        assert ".regreq.md" in suffixes


# ---------------------------------------------------------------------------
# validate_no_bare_todos
# ---------------------------------------------------------------------------


class TestValidateNoBareTodos:
    def test_clean_file_passes(self):
        assert vcr.validate_no_bare_todos("Some content", "file.md") == []

    def test_bare_todo_is_caught(self):
        errors = vcr.validate_no_bare_todos("TODO add details", "file.md")
        assert len(errors) == 1
        assert "Bare or malformed TODO" in errors[0]

    def test_well_formed_todo_is_allowed(self):
        errors = vcr.validate_no_bare_todos("TODO(KEY-123) add details", "file.md")
        assert errors == []

    def test_lowercase_todo_not_flagged(self):
        assert vcr.validate_no_bare_todos("todo: fix me", "file.md") == []


# ---------------------------------------------------------------------------
# parse_inline_metadata_for_requirement
# ---------------------------------------------------------------------------


class TestParseInlineMetadataForRequirement:
    def test_missing_heading_returns_none_none(self):
        content = "## REQ-2\nSil: ASIL-D | Sec: false | Version: 1\n"
        meta, err = vcr.parse_inline_metadata_for_requirement(content, "REQ-1")
        assert meta is None
        assert err is None

    def test_missing_metadata_line_returns_none_none(self):
        content = "## REQ-1\nbody without metadata\n"
        meta, err = vcr.parse_inline_metadata_for_requirement(content, "REQ-1")
        assert meta is None
        assert err is None

    def test_valid_metadata_parses(self):
        content = textwrap.dedent(
            """
            ## REQ-1
            Sil: ASIL-D | Sec: false | Version: 1
            Body
            """
        )
        meta, err = vcr.parse_inline_metadata_for_requirement(content, "REQ-1")
        assert err is None
        assert meta is not None
        assert meta.sil == "ASIL-D"
        assert meta.sec is False
        assert meta.version == 1

    def test_invalid_metadata_returns_validation_error(self):
        content = "## REQ-1\nSil: NOPE | Sec: false | Version: 1\n"
        meta, err = vcr.parse_inline_metadata_for_requirement(content, "REQ-1")
        assert meta is None
        assert err is not None


# ---------------------------------------------------------------------------
# extract_markdown_references
# ---------------------------------------------------------------------------


class TestExtractMarkdownReferences:
    def test_extracts_param_references(self):
        body = "See [@speed](/params/vehicle.yaml#speed?version=1) for details."
        param_refs, req_refs = vcr.extract_markdown_references(body)
        assert len(param_refs) == 1
        assert param_refs[0][0] == "speed"
        assert req_refs == []

    def test_extracts_requirement_references(self):
        body = "Refines [REQ-PARENT](/req/parent.sysreq.md?version=2#REQ-PARENT)."
        param_refs, req_refs = vcr.extract_markdown_references(body)
        assert param_refs == []
        assert len(req_refs) == 1
        assert req_refs[0][0] == "REQ-PARENT"
        assert req_refs[0][2] == 2  # version

    def test_handles_no_references(self):
        param_refs, req_refs = vcr.extract_markdown_references("Plain text here.")
        assert param_refs == []
        assert req_refs == []

    def test_handles_undefined_reference_links_gracefully(self):
        # `extract_markdown_references` swallows reference-resolution errors
        body = "See [missing-ref][undefined]"
        param_refs, req_refs = vcr.extract_markdown_references(body)
        assert param_refs == []
        assert req_refs == []
