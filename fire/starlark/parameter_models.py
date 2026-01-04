#!/usr/bin/env python3
"""Pydantic models for parameter YAML validation.

This module defines the Pydantic models that replace the JSON schema
for validating parameter YAML files.
"""

from typing import Annotated, Any, Dict, List, Literal, Union

from pydantic import BaseModel, Discriminator, Field, Tag, field_validator


class AllParamBase(BaseModel):
    """Versioned parameter with description."""

    description: str = Field(min_length=1)
    version: int = Field(ge=1)


class UnitParamBase(AllParamBase):
    """Versioned parameter with description and unit."""

    unit: str | None = None


class Column(BaseModel):
    """Column definition for table parameters."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    type: Literal["i32", "i64", "u32", "u64", "f32", "f64", "string", "bool"]
    unit: str | None = None

    model_config = {"extra": "forbid"}


class I32Parameter(UnitParamBase):
    """32-bit signed integer parameter."""

    type: Literal["i32"]
    value: int = Field(strict=True, ge=-2147483648, lt=2147483647)

    model_config = {"extra": "forbid"}


class I64Parameter(UnitParamBase):
    """64-bit signed integer parameter."""

    type: Literal["i64"]
    value: int = Field(strict=True, ge=-9223372036854775808, lt=9223372036854775807)

    model_config = {"extra": "forbid"}


class U32Parameter(UnitParamBase):
    """32-bit unsigned integer parameter."""

    type: Literal["u32"]
    value: int = Field(strict=True, ge=0, le=4294967295)

    model_config = {"extra": "forbid"}


class U64Parameter(UnitParamBase):
    """64-bit unsigned integer parameter."""

    type: Literal["u64"]
    value: int = Field(ge=0)

    model_config = {"extra": "forbid"}


class F32Parameter(UnitParamBase):
    """32-bit float parameter."""

    type: Literal["f32"]
    value: float | int  # Allow int for float types

    model_config = {"extra": "forbid"}


class F64Parameter(UnitParamBase):
    """64-bit float parameter."""

    type: Literal["f64"]
    value: float | int  # Allow int for float types

    model_config = {"extra": "forbid"}


class StringParameter(UnitParamBase):
    """String parameter."""

    type: Literal["string"]
    value: str

    model_config = {"extra": "forbid"}


class BoolParameter(UnitParamBase):
    """Boolean parameter."""

    type: Literal["bool"]
    value: bool

    model_config = {"extra": "forbid", "strict": True}

    @field_validator("value", mode="before")
    @classmethod
    def validate_bool_strict(cls, v):
        """Strictly validate boolean values - no string coercion."""
        if not isinstance(v, bool):
            raise ValueError("value is not a valid boolean")
        return v


class TableParameter(AllParamBase):
    """Table parameter with columns and rows."""

    type: Literal["table"]
    columns: List[Column] = Field(min_length=1)
    rows: List[List[Any]] = Field(min_length=1)

    model_config = {"extra": "forbid"}


# Discriminated union of all parameter types based on 'type' field
Parameter = Annotated[
    Union[
        Annotated[I32Parameter, Tag("i32")],
        Annotated[I64Parameter, Tag("i64")],
        Annotated[U32Parameter, Tag("u32")],
        Annotated[U64Parameter, Tag("u64")],
        Annotated[F32Parameter, Tag("f32")],
        Annotated[F64Parameter, Tag("f64")],
        Annotated[StringParameter, Tag("string")],
        Annotated[BoolParameter, Tag("bool")],
        Annotated[TableParameter, Tag("table")],
    ],
    Discriminator("type"),
]


class ParameterFile(BaseModel):
    """Root model for parameter YAML files."""

    parameters: Dict[str, Parameter] = Field(min_length=1)

    model_config = {"extra": "forbid"}
