#!/usr/bin/env python3
"""Tests for the format specification generator."""

import pytest

from fire.starlark.config_models import FireConfig, load_config
from fire.starlark.generate_format_spec import generate_format_spec


@pytest.fixture()
def default_config():
    return load_config()


class TestGenerateFormatSpec:
    def test_contains_title(self, default_config):
        output = generate_format_spec(default_config)
        assert "# FIRE Format Specification" in output

    def test_contains_auto_generated_note(self, default_config):
        output = generate_format_spec(default_config)
        assert "auto-generated" in output

    def test_contains_all_document_types(self, default_config):
        output = generate_format_spec(default_config)
        for dt in default_config.document_types.values():
            assert dt.display_name in output
            assert dt.suffix in output

    def test_contains_sil_values(self, default_config):
        output = generate_format_spec(default_config)
        assert "ASIL-A" in output
        assert "SIL-1" in output
        assert "DAL-A" in output
        assert "PL-a" in output
        assert "QM" in output

    def test_contains_field_docs(self, default_config):
        output = generate_format_spec(default_config)
        # All field display names appear
        for fdef in default_config.field_definitions.values():
            assert fdef.display_name in output

    def test_contains_parameter_section(self, default_config):
        output = generate_format_spec(default_config)
        assert "## Parameter Files" in output

    def test_contains_cross_references_section(self, default_config):
        output = generate_format_spec(default_config)
        assert "## Cross-References" in output

    def test_contains_validation_rules(self, default_config):
        output = generate_format_spec(default_config)
        assert "## Validation Rules" in output

    def test_contains_table_of_contents(self, default_config):
        output = generate_format_spec(default_config)
        assert "## Table of Contents" in output

    def test_sysreq_shows_required_sil(self, default_config):
        output = generate_format_spec(default_config)
        # sysreq section should show SIL as required
        sysreq_start = output.index("System Requirement")
        # Find the next document type section to bound our search
        swreq_start = output.index("Software Requirement")
        sysreq_section = output[sysreq_start:swreq_start]
        assert "**Required:** Yes" in sysreq_section

    def test_regreq_shows_optional_sil(self, default_config):
        output = generate_format_spec(default_config)
        # regreq section should show SIL as optional
        regreq_start = output.index("Regulatory Requirement")
        regreq_section = output[regreq_start:]
        # Find the SIL field in the regreq section
        sil_pos = regreq_section.index("`SIL` Field")
        # Look for Required: No after SIL field
        after_sil = regreq_section[sil_pos : sil_pos + 200]
        assert "**Required:** No" in after_sil

    def test_custom_config(self):
        """Test with a minimal custom config."""
        custom = FireConfig.model_validate(
            {
                "fire_config_version": 1,
                "field_definitions": {
                    "version": {
                        "display_name": "Version",
                        "type": "int",
                        "min_value": 1,
                    }
                },
                "document_types": {
                    "handbook": {
                        "suffix": ".handbook.md",
                        "display_name": "Handbook Entry",
                        "description": "Product handbook entries",
                        "required_fields": ["version"],
                        "optional_fields": [],
                    }
                },
            }
        )
        output = generate_format_spec(custom)
        assert "Handbook Entry" in output
        assert ".handbook.md" in output
        assert "Product handbook entries" in output
