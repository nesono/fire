#!/usr/bin/env python3
"""Tests for validate_cross_references helpers."""

import textwrap

import pytest

from fire.starlark import validate_cross_references as vcr
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

    def test_prefix_id_does_not_match_longer_id(self):
        # Regression test for #268: searching for REQ-1 must not match
        # a longer ID like REQ-12.
        lines = ["## REQ-12", "body"]
        assert vcr._find_requirement_heading_index(lines, "REQ-1") is None

    def test_skips_prefix_match_and_finds_exact(self):
        # Even when a longer-ID heading precedes the exact match, the
        # exact match is what gets returned.
        lines = ["## REQ-12", "body", "## REQ-1", "more"]
        assert vcr._find_requirement_heading_index(lines, "REQ-1") == 2

    def test_trailing_text_after_id_does_not_match(self):
        # Anchor resolution requires a bare-ID heading so `#<ID>` anchors stay
        # reliable; a trailing title changes the rendered slug and must not match.
        lines = ["## REQ-1 Some description"]
        assert vcr._find_requirement_heading_index(lines, "REQ-1") is None

    def test_matches_heading_with_trailing_whitespace(self):
        lines = ["## REQ-1   "]
        assert vcr._find_requirement_heading_index(lines, "REQ-1") == 0

    def test_matches_h3_heading(self):
        # Entries may be nested under informal section headers at H3 level.
        lines = ["## Hazards", "", "### HARA-H-001", "body"]
        assert vcr._find_requirement_heading_index(lines, "HARA-H-001") == 2

    def test_h3_heading_with_trailing_text_does_not_match(self):
        lines = ["### HARA-H-001 Some description"]
        assert vcr._find_requirement_heading_index(lines, "HARA-H-001") is None

    def test_h3_prefix_id_does_not_match_longer_id(self):
        lines = ["### HARA-H-0012", "body"]
        assert vcr._find_requirement_heading_index(lines, "HARA-H-001") is None

    def test_matches_arbitrary_heading_depth(self):
        # Any heading depth (# .. ######) is recognized.
        for depth in range(1, 7):
            lines = ["intro", f"{'#' * depth} REQ-9", "body"]
            assert vcr._find_requirement_heading_index(lines, "REQ-9") == 1

    def test_no_match_for_seven_hashes(self):
        lines = ["####### REQ-9"]
        assert vcr._find_requirement_heading_index(lines, "REQ-9") is None


# ---------------------------------------------------------------------------
# _entry_id_regex
# ---------------------------------------------------------------------------


class TestEntryIdRegex:
    def test_default_all_caps_id_shape(self):
        pat = vcr._entry_id_regex("foo.sysreq.md")
        assert pat.fullmatch("REQ-1")
        assert pat.fullmatch("HARA-H-001")
        assert not pat.fullmatch("Hazards")

    def test_uses_config_id_pattern(self, default_config):
        default_config.document_types["sysreq"].id_pattern = r"HARA-H-\d+"
        pat = vcr._entry_id_regex("foo.sysreq.md", config=default_config)
        assert pat.fullmatch("HARA-H-001")
        assert not pat.fullmatch("REQ-1")

    def test_matching_doc_type_without_id_pattern_uses_default(self, default_config):
        # Config provided and suffix matches, but the type has no id_pattern.
        pat = vcr._entry_id_regex("foo.sysreq.md", config=default_config)
        assert pat.pattern == vcr._DEFAULT_ID_RE.pattern

    def test_unknown_suffix_falls_back_to_default(self, default_config):
        pat = vcr._entry_id_regex("foo.unknown.md", config=default_config)
        assert pat.pattern == vcr._DEFAULT_ID_RE.pattern


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

    def test_valid_metadata_parses_h3_entry(self):
        content = textwrap.dedent(
            """
            ## Hazards

            ### REQ-1
            Sil: ASIL-D | Sec: false | Version: 1
            Body
            """
        )
        meta, err = vcr.parse_inline_metadata_for_requirement(content, "REQ-1")
        assert err is None
        assert meta is not None
        assert meta.version == 1


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


# ---------------------------------------------------------------------------
# validate_requirement_file — entry detection
# ---------------------------------------------------------------------------


class TestValidateRequirementFileEntryDetection:
    def test_h3_entry_under_informal_section_is_validated(self, tmp_path):
        req = tmp_path / "hazards.sysreq.md"
        req.write_text(
            textwrap.dedent(
                """
                # Hazard Analysis

                ## Hazards

                ### HARA-H-001
                SIL: ASIL-D | Sec: false | Version: 1

                Loss of braking on grade.
                """
            )
        )
        errors = vcr.validate_requirement_file(str(req), str(tmp_path))
        assert errors == []

    def test_all_caps_section_header_flagged_without_hardening(self, tmp_path):
        # With the default all-caps heuristic, an all-caps section header is
        # indistinguishable from an entry and gets flagged as missing metadata.
        req = tmp_path / "doc.sysreq.md"
        req.write_text("## HAZARDS\n\nSome prose without metadata.\n")
        errors = vcr.validate_requirement_file(str(req), str(tmp_path))
        assert any("HAZARDS" in e for e in errors)

    def test_id_pattern_hardening_ignores_section_header(
        self, tmp_path, default_config
    ):
        # Explicit id_pattern makes entry recognition unambiguous: the all-caps
        # section header no longer looks like an entry.
        default_config.document_types["sysreq"].id_pattern = r"HARA-H-\d+"
        models = build_models_from_config(default_config)
        req = tmp_path / "doc.sysreq.md"
        req.write_text(
            textwrap.dedent(
                """
                ## HAZARDS

                ### HARA-H-001
                SIL: ASIL-D | Sec: false | Version: 1

                Loss of braking.
                """
            )
        )
        errors = vcr.validate_requirement_file(
            str(req), str(tmp_path), config=default_config, models=models
        )
        assert errors == []

    def test_deep_heading_entry_is_validated(self, tmp_path):
        # Entry detection works at any depth, not just H2/H3.
        req = tmp_path / "deep.sysreq.md"
        req.write_text(
            textwrap.dedent(
                """
                # Doc

                ## Section

                #### REQ-DEEP
                SIL: ASIL-D | Sec: false | Version: 1

                Deeply nested entry.
                """
            )
        )
        errors = vcr.validate_requirement_file(str(req), str(tmp_path))
        assert errors == []

    def test_heading_with_trailing_text_is_not_an_entry(self, tmp_path):
        # The ID must be the whole heading token; a trailing title means the
        # heading is not treated as an entry (issue #292 explicitly excludes
        # `## REQ-ID Title`). Invalid metadata below must therefore be ignored.
        req = tmp_path / "doc.sysreq.md"
        req.write_text("## REQ-1 Some Title\nSIL: NOPE | Sec: false | Version: 1\n")
        errors = vcr.validate_requirement_file(str(req), str(tmp_path))
        assert errors == []

    def test_custom_id_pattern_ignores_default_shaped_id(
        self, tmp_path, default_config
    ):
        # With a custom id_pattern, an all-caps ID that does not match it is
        # treated as a section header, not an entry — even with bad metadata.
        default_config.document_types["sysreq"].id_pattern = r"HARA-H-\d+"
        models = build_models_from_config(default_config)
        req = tmp_path / "doc.sysreq.md"
        req.write_text("## REQ-1\nSIL: NOPE | Sec: false | Version: 1\n")
        errors = vcr.validate_requirement_file(
            str(req), str(tmp_path), config=default_config, models=models
        )
        assert errors == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
