#!/usr/bin/env python3
"""Pydantic models for requirement metadata validation."""

import re
from typing import Literal, Optional, Union, Final, List

from pydantic import BaseModel, Field, field_validator

from fire.starlark import markdown_common
from fire.starlark.patterns import REQ_ID_PATTERN, TODO_PATTERN

_VALID_SIL_VALUES: Final = {
    "ASIL-A",
    "ASIL-B",
    "ASIL-C",
    "ASIL-D",
    "SIL-1",
    "SIL-2",
    "SIL-3",
    "SIL-4",
    "DAL-A",
    "DAL-B",
    "DAL-C",
    "DAL-D",
    "DAL-E",
    "QM",
}

SilValue = Literal[
    "ASIL-A",
    "ASIL-B",
    "ASIL-C",
    "ASIL-D",
    "SIL-1",
    "SIL-2",
    "SIL-3",
    "SIL-4",
    "DAL-A",
    "DAL-B",
    "DAL-C",
    "DAL-D",
    "DAL-E",
    "QM",
]


class RequirementMetadata(BaseModel):
    """Model for requirement inline metadata."""

    id: str = Field(pattern=REQ_ID_PATTERN.pattern)

    sil: Union[SilValue, str]

    sec: Union[bool, str]

    version: int = Field(ge=1, strict=True)

    parent: Optional[List[str]] = None

    model_config = {"extra": "forbid"}

    @field_validator("sil", mode="before")
    @classmethod
    def validate_sil(cls, v: object) -> object:
        """Accept valid SIL/ASIL/DAL literals or TODO(KEY-1234)."""
        if isinstance(v, str) and TODO_PATTERN.fullmatch(v):
            return v
        if v not in _VALID_SIL_VALUES:
            raise ValueError(
                "Input should be one of: "
                "ASIL-A/B/C/D (ISO 26262), "
                "SIL-1/2/3/4 (IEC 61508), "
                "DAL-A/B/C/D/E (DO-178C/DO-254), "
                "QM, or TODO(KEY-1234)"
            )
        return v

    @field_validator("sec", mode="before")
    @classmethod
    def validate_sec(cls, v: object) -> object:
        """Accept strict booleans or TODO(KEY-1234)."""
        if isinstance(v, str) and TODO_PATTERN.fullmatch(v):
            return v
        if not isinstance(v, bool):
            raise ValueError("value is not a valid boolean or TODO(KEY-1234)")
        return v

    @field_validator("parent")
    @classmethod
    def validate_parent_format(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate parent is a list of markdown links, TODO(KEY-1234), or None."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("parent must be a list")
        for parent_value in v:
            cls._validate_single_parent(parent_value)
        return v

    @classmethod
    def _validate_single_parent(cls, parent_value: str) -> None:
        """Validate a single parent entry."""
        if not isinstance(parent_value, str):
            raise ValueError("each parent entry must be a string")
        if TODO_PATTERN.fullmatch(parent_value):
            return
        cls._validate_parent_markdown_link(parent_value)

    @classmethod
    def _validate_parent_markdown_link(cls, parent_value: str) -> None:
        """Validate parent is a proper markdown link with repository-relative path."""
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
