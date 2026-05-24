#!/usr/bin/env python3
"""Pydantic models for FIRE configuration schema.

The configuration defines reusable field definitions and document types.
Consumers supply a fire_config.yaml; when absent, the built-in default
(default_fire_config.yaml) is used.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from fire.starlark import file_io_common


class FieldDefinition(BaseModel):
    """A reusable metadata field that can appear in document types."""

    display_name: str
    type: Literal["enum", "bool", "int", "parent_link"]
    description: str = ""

    # enum-specific
    values: Optional[List[str]] = None

    # int-specific
    min_value: Optional[int] = None

    # todo support
    allow_todo: bool = False

    # parent_link-specific
    allow_multiple: bool = False

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "FieldDefinition":
        if self.type == "enum" and not self.values:
            raise ValueError("enum field must specify 'values'")
        if self.type != "enum" and self.values is not None:
            raise ValueError("'values' is only valid for enum fields")
        if self.type != "int" and self.min_value is not None:
            raise ValueError("'min_value' is only valid for int fields")
        if self.type != "parent_link" and self.allow_multiple:
            raise ValueError("'allow_multiple' is only valid for parent_link fields")
        return self


class DocumentTypeDefinition(BaseModel):
    """A document type with its file suffix and field requirements."""

    suffix: str
    display_name: str
    description: str = ""
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)

    @field_validator("suffix")
    @classmethod
    def validate_suffix(cls, v: str) -> str:
        if not v.endswith(".md"):
            raise ValueError("suffix must end with '.md'")
        return v


class FireConfig(BaseModel):
    """Top-level FIRE configuration."""

    fire_config_version: int = Field(ge=1)
    field_definitions: dict[str, FieldDefinition]
    document_types: dict[str, DocumentTypeDefinition]

    @model_validator(mode="after")
    def validate_field_references(self) -> "FireConfig":
        """Ensure every field referenced by a document type is defined."""
        for doc_name, doc_type in self.document_types.items():
            for field_name in doc_type.required_fields + doc_type.optional_fields:
                if field_name not in self.field_definitions:
                    raise ValueError(
                        f"document type '{doc_name}' references undefined "
                        f"field '{field_name}'"
                    )
        return self

    def suffix_to_document_type(self) -> dict[str, DocumentTypeDefinition]:
        """Return a mapping from file suffix to document type definition."""
        return {dt.suffix: dt for dt in self.document_types.values()}

    def known_fields(self) -> list[str]:
        """Return all known field display names (lowercased) for metadata parsing."""
        return [fd.display_name.lower() for fd in self.field_definitions.values()]


def _default_config_path() -> Path:
    """Return the path to the built-in default_fire_config.yaml."""
    return Path(__file__).parent / "default_fire_config.yaml"


def load_config(config_path: str | Path | None = None) -> FireConfig:
    """Load and validate a FIRE configuration file.

    When *config_path* is ``None``, the built-in default is used.
    """
    if config_path is None:
        config_path = _default_config_path()
    else:
        config_path = Path(config_path)

    raw, error = file_io_common.load_yaml_safe(str(config_path))
    if error:
        raise OSError(error)

    return FireConfig.model_validate(raw)
