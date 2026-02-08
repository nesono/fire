#!/usr/bin/env python3
"""Pydantic models for requirement metadata validation."""

import re
from typing import Literal, Optional, Union, Final

from pydantic import BaseModel, Field, field_validator

from fire.starlark import markdown_common

_TODO_PATTERN: Final = re.compile(r"^TODO\([A-Z]+-[0-9]+\)$")

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

    id: str = Field(pattern=r"^[A-Z][A-Z0-9_-]+$")

    sil: Union[SilValue, str]

    sec: Union[bool, str]

    version: int = Field(ge=1, strict=True)

    parent: Optional[str] = None

    model_config = {"extra": "forbid"}

    @field_validator("sil", mode="before")
    @classmethod
    def validate_sil(cls, v: object) -> object:
        """Accept valid SIL/ASIL/DAL literals or TODO(KEY-1234)."""
        if isinstance(v, str) and _TODO_PATTERN.match(v):
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
        if isinstance(v, str) and _TODO_PATTERN.match(v):
            return v
        if not isinstance(v, bool):
            raise ValueError("value is not a valid boolean or TODO(KEY-1234)")
        return v

    @field_validator("parent")
    @classmethod
    def validate_parent_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate parent is a markdown link, TODO(KEY-1234), or None."""
        if v is None:
            return v

        if _TODO_PATTERN.match(v):
            return v

        # Check markdown link format: [TEXT](URL)
        match = re.match(markdown_common.MARKDOWN_LINK_PATTERN, v)
        if not match:
            raise ValueError(
                "parent must be a markdown link: [REQ-ID](/path.md?version=N#REQ-ID)"
            )

        path = match.group(2)

        # Extract base path (before # and ?)
        base_path = path.split("#")[0] if "#" in path else path
        base_path = base_path.split("?")[0] if "?" in base_path else base_path

        # Verify repository-relative
        if not base_path.startswith("/"):
            raise ValueError(
                f"parent path must be repository-relative (start with /): '{path}'"
            )

        return v
