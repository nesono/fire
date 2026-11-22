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

    def test_matches_heading_with_trailing_text(self):
        # Headings may have a trailing space and additional text;
        # they should still match.
        lines = ["## REQ-1 Some description"]
        assert vcr._find_requirement_heading_index(lines, "REQ-1") == 0

    def test_matches_heading_with_trailing_whitespace(self):
        lines = ["## REQ-1   "]
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


# ---------------------------------------------------------------------------
# validate_requirement_headings
# ---------------------------------------------------------------------------


class TestValidateRequirementHeadings:
    def test_conformant_headings_accepted(self):
        content = "## REQ-1\nbody\n## REQ_SW_2\nbody\n"
        assert vcr.validate_requirement_headings(content, "f.md") == []

    def test_lowercase_heading_rejected(self):
        errors = vcr.validate_requirement_headings("## req-lower-002\n", "f.md")
        assert len(errors) == 1
        assert "f.md:1" in errors[0]
        assert "req-lower-002" in errors[0]

    def test_heading_with_trailing_title_rejected(self):
        content = "## REQ-OK-001\n## REQ-TITLE-003 Braking distance\n"
        errors = vcr.validate_requirement_headings(content, "f.md")
        assert len(errors) == 1
        assert "f.md:2" in errors[0]

    def test_trailing_whitespace_accepted(self):
        assert vcr.validate_requirement_headings("## REQ-1   \n", "f.md") == []

    def test_other_heading_levels_ignored(self):
        content = "# Title\n### Details\n#### More\n"
        assert vcr.validate_requirement_headings(content, "f.md") == []

    def test_headings_in_fenced_code_blocks_ignored(self):
        content = "## REQ-1\n```markdown\n## not a requirement\n```\n"
        assert vcr.validate_requirement_headings(content, "f.md") == []

    def test_heading_after_fenced_code_block_checked(self):
        content = "```\n## ignored\n```\n## bad heading\n"
        errors = vcr.validate_requirement_headings(content, "f.md")
        assert len(errors) == 1
        assert "f.md:4" in errors[0]


class TestValidateRequirementFileHeadings:
    def test_non_conformant_heading_fails_validation(self, tmp_path):
        path = tmp_path / "bad.sysreq.md"
        path.write_text(
            textwrap.dedent(
                """\
                ## REQ-OK-001

                SIL: QM | Sec: false | Version: 1

                Conformant.

                ## req-lower-002

                SIL: BOGUS | Sec: maybe | Version: 0

                Invalid metadata that must not be silently skipped.
                """
            )
        )
        errors = vcr.validate_requirement_file(str(path), str(tmp_path))
        assert any("req-lower-002" in error for error in errors)


# ---------------------------------------------------------------------------
# validate_parameter_reference
# ---------------------------------------------------------------------------


class TestValidateParameterReference:
    def _write_params(self, tmp_path, content, name="params.yaml"):
        (tmp_path / name).write_text(textwrap.dedent(content))

    def _validate(self, tmp_path, name, version, path="/params.yaml"):
        return vcr.validate_parameter_reference(
            name, f"{path}#{name}", str(tmp_path), version, "req.md"
        )

    def test_exact_key_and_version_accepted(self, tmp_path):
        self._write_params(tmp_path, "max_speed_v1:\n  value: 1\n")
        assert self._validate(tmp_path, "max_speed", 1) == (True, None)

    def test_name_that_is_suffix_of_other_parameter_rejected(self, tmp_path):
        self._write_params(tmp_path, "max_speed_v1:\n  value: 1\n")
        valid, error = self._validate(tmp_path, "speed", 1)
        assert not valid
        assert "'speed' not found" in error

    def test_commented_out_key_rejected(self, tmp_path):
        self._write_params(tmp_path, "# speed_v1:\nmax_speed_v1:\n  value: 1\n")
        valid, error = self._validate(tmp_path, "speed", 1)
        assert not valid

    def test_key_in_nested_value_rejected(self, tmp_path):
        self._write_params(
            tmp_path, "max_speed_v1:\n  description: 'see speed_v1: here'\n"
        )
        valid, _ = self._validate(tmp_path, "speed", 1)
        assert not valid

    def test_future_version_rejected(self, tmp_path):
        self._write_params(tmp_path, "speed_v1:\n  value: 1\n")
        valid, error = self._validate(tmp_path, "speed", 2)
        assert not valid
        assert "future version (2)" in error

    def test_version_older_than_oldest_present_rejected(self, tmp_path):
        self._write_params(tmp_path, "speed_v2:\n  value: 1\nspeed_v3:\n  value: 2\n")
        valid, error = self._validate(tmp_path, "speed", 1)
        assert not valid
        assert "version 1" in error

    def test_older_present_version_warns_but_accepted(self, tmp_path, capsys):
        self._write_params(tmp_path, "speed_v1:\n  value: 1\nspeed_v2:\n  value: 2\n")
        assert self._validate(tmp_path, "speed", 1) == (True, None)
        assert "PARAMETER VERSION MISMATCH" in capsys.readouterr().out

    def test_missing_version_rejected(self, tmp_path):
        self._write_params(tmp_path, "speed_v1:\n  value: 1\n")
        valid, error = self._validate(tmp_path, "speed", None)
        assert not valid
        assert "misses version" in error

    def test_validated_yaml_fallback_used(self, tmp_path):
        self._write_params(
            tmp_path, "speed_v1:\n  value: 1\n", name="params_validated.yaml"
        )
        assert self._validate(tmp_path, "speed", 1) == (True, None)

    def test_missing_file_rejected(self, tmp_path):
        valid, error = self._validate(tmp_path, "speed", 1)
        assert not valid
        assert "does not exist" in error

    def test_malformed_yaml_rejected(self, tmp_path):
        self._write_params(tmp_path, "speed_v1: [unclosed\n")
        valid, _ = self._validate(tmp_path, "speed", 1)
        assert not valid


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
