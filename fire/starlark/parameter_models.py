#!/usr/bin/env python3
"""Pydantic models for parameter YAML validation.

This module defines the Pydantic models that replace the JSON schema
for validating parameter YAML files.
"""

import re
from collections import defaultdict
from typing import Any, Dict, List, Literal, Union

from pydantic import (
    BaseModel,
    Field,
    RootModel,
    field_validator,
    model_validator,
)

_VERSION_SUFFIX_RE = re.compile(r"^([a-z][a-z0-9_]*)_v([1-9][0-9]*)$")


def infer_parameter_type(data: Dict[str, Any]) -> str:
    """Infer parameter type from the value field.

    Args:
        data: Parameter dictionary with at least a 'value' field

    Returns:
        Inferred type string: 'i64', 'f64', 'bool', 'string', or 'table'

    Raises:
        ValueError: If type cannot be inferred or value is None
    """
    # Table type must be explicit (has columns/rows)
    if "type" in data:
        return data["type"]

    if "value" not in data:
        raise ValueError("Parameter must have 'value' field")

    value = data["value"]

    if value is None:
        raise ValueError("Cannot infer type from NoneType")

    # Check bool BEFORE int (bool is subclass of int in Python)
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "i64"
    elif isinstance(value, float):
        return "f64"
    elif isinstance(value, str):
        return "string"
    else:
        raise ValueError(f"Cannot infer type from {type(value).__name__}")


class AllParamBase(BaseModel):
    """Parameter with description."""

    description: str = Field(min_length=1)


class UnitParamBase(AllParamBase):
    """Versioned parameter with description and unit."""

    unit: str | None = None


class Column(BaseModel):
    """Column definition for table parameters."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    type: Literal["i64", "f64", "string", "bool"]
    unit: str | None = None

    model_config = {"extra": "forbid"}


class I64Parameter(UnitParamBase):
    """64-bit signed integer parameter."""

    type: Literal["i64"]
    value: int = Field(strict=True)

    model_config = {"extra": "forbid"}


class F64Parameter(UnitParamBase):
    """64-bit float parameter."""

    type: Literal["f64"]
    value: float = Field(strict=True)

    model_config = {"extra": "forbid"}


class StringParameter(UnitParamBase):
    """String parameter."""

    type: Literal["string"]
    value: str

    model_config = {"extra": "forbid"}


class BoolParameter(UnitParamBase):
    """Boolean parameter."""

    type: Literal["bool"]
    value: bool = Field(strict=True)

    model_config = {"extra": "forbid"}

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


# Union of all parameter types (type field injected by ParameterFile validator)
Parameter = Union[
    I64Parameter,
    F64Parameter,
    StringParameter,
    BoolParameter,
    TableParameter,
]


class ParameterFile(RootModel[Dict[str, Parameter]]):
    """Root model for parameter YAML files.

    Parameters are defined at the root level without a 'parameters' wrapper.
    """

    root: Dict[str, Parameter] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def inject_inferred_types(cls, data: Any) -> Any:
        """Inject inferred types into parameter definitions before validation.

        For scalar parameters without an explicit 'type' field, infer the type
        from the Python type of the 'value' field (which comes from YAML parsing).
        """
        if not isinstance(data, dict):
            return data

        # Inject type field for each parameter if not present
        for param_name, param_data in data.items():
            if isinstance(param_data, dict) and "type" not in param_data:
                try:
                    param_data["type"] = infer_parameter_type(param_data)
                except ValueError as e:
                    # Re-raise with parameter name context
                    raise ValueError(f"Parameter '{param_name}': {e}") from e

        return data

    @model_validator(mode="after")
    def validate_version_suffixes(self):
        """Validate that all parameter keys use _vN suffix and versions are consecutive."""
        groups: Dict[str, Dict[int, str]] = defaultdict(dict)

        for key in self.root:
            m = _VERSION_SUFFIX_RE.match(key)
            if not m:
                raise ValueError(
                    f"Parameter key '{key}' must match pattern '<name>_v<N>' "
                    f"where name is lowercase snake_case and N >= 1 "
                    f"(e.g., 'wheel_count_v1')"
                )
            base_name = m.group(1)
            version = int(m.group(2))
            groups[base_name][version] = key

        for base_name, versions in groups.items():
            sorted_versions = sorted(versions.keys())
            min_version = min(versions.keys())
            max_version = max(versions.keys())
            expected = list(range(min_version, max_version + 1))

            actual = ", ".join(f"_v{v}" for v in sorted_versions)
            if len(sorted_versions) > 2:
                raise ValueError(
                    f"Versions for '{base_name}' must not exceed two entries."
                    f" Found {actual}"
                )
            if sorted_versions != expected:
                raise ValueError(
                    f"Versions for '{base_name}' must be consecutive."
                    f" Found: {actual}"
                )

        return self
