#!/usr/bin/env python3
"""Build Pydantic requirement models dynamically from a FireConfig.

Given a FireConfig and a document type name, this module produces a Pydantic
BaseModel subclass whose fields, validators and ``extra = "forbid"`` behaviour
match the static RequirementMetadata / RegulatoryRequirementMetadata models
that FIRE shipped before the configuration system was introduced.
"""

from __future__ import annotations

import re
from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from fire.starlark import markdown_common
from fire.starlark.config_models import (
    DocumentTypeDefinition,
    FieldDefinition,
    FireConfig,
)
from fire.starlark.patterns import REQ_ID_PATTERN, TODO_PATTERN


def _build_enum_validator(field_name: str, field_def: FieldDefinition) -> classmethod:
    """Create a ``field_validator`` for an enum field."""
    valid_values = set(field_def.values)
    allow_todo = field_def.allow_todo

    def _validate(cls, v: object) -> object:  # noqa: N805
        if v is None:
            return v
        if allow_todo and isinstance(v, str) and TODO_PATTERN.fullmatch(v):
            return v
        if v not in valid_values:
            raise ValueError(
                f"Input should be one of: {', '.join(sorted(valid_values))}"
                + (", or TODO(KEY-1234)" if allow_todo else "")
            )
        return v

    return field_validator(field_name, mode="before")(classmethod(_validate))


def _build_bool_validator(field_name: str, field_def: FieldDefinition) -> classmethod:
    """Create a ``field_validator`` for a bool field."""
    allow_todo = field_def.allow_todo

    def _validate(cls, v: object) -> object:  # noqa: N805
        if v is None:
            return v
        if allow_todo and isinstance(v, str) and TODO_PATTERN.fullmatch(v):
            return v
        if not isinstance(v, bool):
            raise ValueError("value is not a valid boolean or TODO(KEY-1234)")
        return v

    return field_validator(field_name, mode="before")(classmethod(_validate))


def _validate_single_parent(parent_value: str) -> None:
    """Validate a single parent entry (shared by all parent_link fields)."""
    if not isinstance(parent_value, str):
        raise ValueError("each parent entry must be a string")
    if TODO_PATTERN.fullmatch(parent_value):
        return
    match = re.match(markdown_common.MARKDOWN_LINK_PATTERN, parent_value)
    if not match:
        raise ValueError(
            "parent must be a markdown link: [REQ-ID](/path.md?version=N#REQ-ID)"
        )
    path = match.group(2)
    base_path = path.split("#")[0].split("?")[0]
    if not base_path.startswith("/"):
        raise ValueError(
            f"parent path must be repository-relative (start with /): '{path}'"
        )


def _build_parent_link_validator(
    field_name: str, field_def: FieldDefinition
) -> classmethod:
    """Create a ``field_validator`` for a parent_link field."""

    def _validate(cls, v: object) -> object:  # noqa: N805
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError(f"{field_name} must be a list")
        for entry in v:
            _validate_single_parent(entry)
        return v

    return field_validator(field_name, mode="before")(classmethod(_validate))


def _annotation_for_field(field_def: FieldDefinition, *, required: bool) -> type:
    """Return the Python type annotation for a field definition."""
    if field_def.type == "enum":
        # Enum values are strings; allow_todo is enforced by the validator.
        base = str
    elif field_def.type == "bool":
        if field_def.allow_todo:
            base = Union[bool, str]
        else:
            base = bool
    elif field_def.type == "int":
        base = int
    elif field_def.type == "parent_link":
        # allow_multiple does not affect the annotation; the validator enforces shape.
        base = Optional[List[str]]
    else:
        base = str

    if not required and field_def.type != "parent_link":
        base = Optional[base]

    return base


def _field_kwargs(field_def: FieldDefinition, *, required: bool) -> dict:
    """Return kwargs for ``pydantic.Field(...)``."""
    kwargs: dict = {}
    if field_def.type == "int":
        if field_def.min_value is not None:
            kwargs["ge"] = field_def.min_value
        kwargs["strict"] = True
    if not required:
        kwargs["default"] = None
    if field_def.type == "parent_link":
        kwargs["default"] = None
    return kwargs


def build_requirement_model(
    config: FireConfig,
    doc_type_name: str,
) -> type[BaseModel]:
    """Build a Pydantic model class for the given document type.

    The returned class has:
    - An ``id`` field with the standard REQ_ID_PATTERN
    - One field per required + optional field listed in the document type
    - Appropriate validators for each field type
    - ``model_config = {"extra": "forbid"}``
    """
    doc_type: DocumentTypeDefinition = config.document_types[doc_type_name]

    required_set = set(doc_type.required_fields)
    all_fields = doc_type.required_fields + doc_type.optional_fields

    # Collect field annotations, Field() defaults, and validators
    annotations: dict[str, type] = {"id": str}
    namespace: dict = {
        "__annotations__": annotations,
        "id": Field(pattern=REQ_ID_PATTERN.pattern),
        "model_config": {"extra": "forbid"},
    }

    for fname in all_fields:
        fdef = config.field_definitions[fname]
        is_required = fname in required_set
        annotations[fname] = _annotation_for_field(fdef, required=is_required)
        field_kw = _field_kwargs(fdef, required=is_required)
        if field_kw:
            namespace[fname] = Field(**field_kw)

        # Attach validators
        if fdef.type == "enum":
            validator_name = f"validate_{fname}"
            namespace[validator_name] = _build_enum_validator(fname, fdef)
        elif fdef.type == "bool":
            validator_name = f"validate_{fname}"
            namespace[validator_name] = _build_bool_validator(fname, fdef)
        elif fdef.type == "parent_link":
            validator_name = f"validate_{fname}_format"
            namespace[validator_name] = _build_parent_link_validator(fname, fdef)

    model_cls = type(
        f"DynamicRequirement_{doc_type_name}",
        (BaseModel,),
        namespace,
    )
    return model_cls


def build_models_from_config(
    config: FireConfig,
) -> dict[str, type[BaseModel]]:
    """Build one model per document type defined in *config*.

    Returns a dict mapping document-type name to its Pydantic model class.
    """
    return {
        name: build_requirement_model(config, name) for name in config.document_types
    }


def model_for_suffix(
    config: FireConfig,
    models: dict[str, type[BaseModel]],
    file_path: str,
) -> type[BaseModel] | None:
    """Return the model matching *file_path*'s suffix, or ``None``."""
    for name, doc_type in config.document_types.items():
        if file_path.endswith(doc_type.suffix):
            return models[name]
    return None
