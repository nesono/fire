#!/usr/bin/env python3
"""Tests for FIRE configuration models."""

import pytest
import yaml

from fire.starlark.config_models import (
    FieldDefinition,
    DocumentTypeDefinition,
    FireConfig,
    load_config,
)


class TestFieldDefinition:
    def test_enum_field(self):
        fd = FieldDefinition(
            display_name="SIL",
            type="enum",
            values=["ASIL-A", "ASIL-B"],
            allow_todo=True,
        )
        assert fd.type == "enum"
        assert fd.values == ["ASIL-A", "ASIL-B"]

    def test_enum_field_requires_values(self):
        with pytest.raises(ValueError, match="enum field must specify 'values'"):
            FieldDefinition(display_name="SIL", type="enum")

    def test_values_only_for_enum(self):
        with pytest.raises(ValueError, match="only valid for enum"):
            FieldDefinition(display_name="Sec", type="bool", values=["true", "false"])

    def test_bool_field(self):
        fd = FieldDefinition(display_name="Sec", type="bool", allow_todo=True)
        assert fd.type == "bool"

    def test_int_field(self):
        fd = FieldDefinition(display_name="Version", type="int", min_value=1)
        assert fd.min_value == 1

    def test_min_value_only_for_int(self):
        with pytest.raises(ValueError, match="only valid for int"):
            FieldDefinition(display_name="Sec", type="bool", min_value=1)

    def test_parent_link_field(self):
        fd = FieldDefinition(
            display_name="Parent", type="parent_link", allow_multiple=True
        )
        assert fd.allow_multiple is True

    def test_allow_multiple_only_for_parent_link(self):
        with pytest.raises(ValueError, match="only valid for parent_link"):
            FieldDefinition(
                display_name="SIL", type="enum", values=["A"], allow_multiple=True
            )


class TestDocumentTypeDefinition:
    def test_valid_suffix(self):
        dt = DocumentTypeDefinition(
            suffix=".sysreq.md",
            display_name="System Requirement",
            required_fields=["sil", "sec", "version"],
        )
        assert dt.suffix == ".sysreq.md"

    def test_suffix_must_end_with_md(self):
        with pytest.raises(ValueError, match="must end with '.md'"):
            DocumentTypeDefinition(suffix=".sysreq.yaml", display_name="Bad")


class TestFireConfig:
    def _minimal_config(self, **overrides):
        base = {
            "fire_config_version": 1,
            "field_definitions": {
                "version": {
                    "display_name": "Version",
                    "type": "int",
                    "min_value": 1,
                }
            },
            "document_types": {
                "sysreq": {
                    "suffix": ".sysreq.md",
                    "display_name": "System Requirement",
                    "required_fields": ["version"],
                }
            },
        }
        base.update(overrides)
        return base

    def test_valid_config(self):
        cfg = FireConfig.model_validate(self._minimal_config())
        assert cfg.fire_config_version == 1
        assert "sysreq" in cfg.document_types
        assert "version" in cfg.field_definitions

    def test_undefined_field_reference(self):
        data = self._minimal_config()
        data["document_types"]["sysreq"]["required_fields"] = ["nonexistent"]
        with pytest.raises(ValueError, match="undefined field 'nonexistent'"):
            FireConfig.model_validate(data)

    def test_suffix_to_document_type(self):
        cfg = FireConfig.model_validate(self._minimal_config())
        mapping = cfg.suffix_to_document_type()
        assert ".sysreq.md" in mapping
        assert mapping[".sysreq.md"].display_name == "System Requirement"

    def test_known_fields(self):
        cfg = FireConfig.model_validate(self._minimal_config())
        assert "version" in cfg.known_fields()


class TestLoadConfig:
    def test_load_default_config(self):
        cfg = load_config()
        assert cfg.fire_config_version == 1
        assert "sysreq" in cfg.document_types
        assert "swreq" in cfg.document_types
        assert "regreq" in cfg.document_types
        assert "sil" in cfg.field_definitions
        assert "sec" in cfg.field_definitions
        assert "version" in cfg.field_definitions
        assert "parent" in cfg.field_definitions

    def test_default_sysreq_fields(self):
        cfg = load_config()
        sysreq = cfg.document_types["sysreq"]
        assert set(sysreq.required_fields) == {"sil", "sec", "version"}
        assert sysreq.optional_fields == ["parent"]

    def test_default_regreq_fields(self):
        cfg = load_config()
        regreq = cfg.document_types["regreq"]
        assert regreq.required_fields == ["version"]
        assert set(regreq.optional_fields) == {"sil", "sec", "parent"}

    def test_default_sil_values(self):
        cfg = load_config()
        sil = cfg.field_definitions["sil"]
        assert "ASIL-A" in sil.values
        assert "SIL-1" in sil.values
        assert "DAL-A" in sil.values
        assert "PL-a" in sil.values
        assert "QM" in sil.values

    def test_load_custom_config(self, tmp_path):
        config_data = {
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
        config_file = tmp_path / "fire_config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")
        cfg = load_config(config_file)
        assert "handbook" in cfg.document_types
        assert cfg.document_types["handbook"].suffix == ".handbook.md"

    def test_load_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")
