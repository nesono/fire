#!/usr/bin/env python3
"""Pydantic models for requirement metadata validation."""

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RequirementMetadata(BaseModel):
    """Model for requirement inline metadata."""

    id: str = Field(pattern=r"^[A-Z][A-Z0-9_-]+$")

    sil: Literal[
        "ASIL-A",
        "ASIL-B",
        "ASIL-C",
        "ASIL-D",
        "SIL-1",
        "SIL-2",
        "SIL-3",
        "SIL-4",
        "QM",
    ]

    sec: bool = Field(strict=True)

    version: int = Field(ge=1, strict=True)

    parent: Optional[str] = None

    model_config = {"extra": "forbid"}

    @field_validator("sec", mode="before")
    @classmethod
    def validate_sec_bool(cls, v):
        """Validate sec field strictly as boolean."""
        if not isinstance(v, bool):
            raise ValueError("sec must be a boolean (true or false)")
        return v

    @field_validator("parent")
    @classmethod
    def validate_parent_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate parent is a markdown link with repository-relative path."""
        if v is None:
            return v

        # Check markdown link format: [TEXT](URL)
        match = re.match(r"\[([^\]]+)\]\(([^\)]+)\)", v)
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
