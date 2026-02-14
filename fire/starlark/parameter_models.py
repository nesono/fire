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
    model_validator,
)

_VERSION_SUFFIX_RE = re.compile(r"^([a-z][a-z0-9_]*)_v([1-9][0-9]*)$")


def infer_type_from_value(value: Any) -> str:
    """Infer type from a single value.

    Args:
        value: A Python value from YAML parsing

    Returns:
        Inferred type string: 'i64', 'f64', 'bool', or 'string'

    Raises:
        ValueError: If type cannot be inferred or value is None
    """
    if value is None:
        raise ValueError("Cannot infer type from None")

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


def infer_parameter_type(data: Dict[str, Any]) -> str:
    """Infer parameter type for a parameter.

    Args:
        data: Parameter dictionary

    Returns:
        Inferred type string: 'i64', 'f64', 'bool', 'string', or 'table'

    Raises:
        ValueError: If type cannot be inferred or value is None
    """
    # Table type must be explicit (has columns/rows)
    if "type" in data and data["type"] == "table":
        return "table"

    # Reject explicit type for scalar parameters
    if "type" in data:
        raise ValueError(
            "Explicit 'type' field not allowed for scalar parameters. "
            "Types are automatically inferred from values "
            "(int→i64, float→f64, bool→bool, string→string)."
        )

    if "value" not in data:
        raise ValueError("Parameter must have 'value' field")

    return infer_type_from_value(data["value"])


class AllParamBase(BaseModel):
    """Parameter with description."""

    description: str = Field(min_length=1)


class UnitParamBase(AllParamBase):
    """Versioned parameter with description and unit."""

    unit: str = Field(min_length=1)


class Column(BaseModel):
    """Column definition for table parameters."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    type: Literal["i64", "f64", "string", "bool"]
    unit: str = Field(min_length=1)

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


class TableParameter(AllParamBase):
    """Table parameter with columns and rows."""

    type: Literal["table"]
    columns: List[Column] = Field(min_length=1)
    rows: List[List[Any]] = Field(min_length=1)

    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    @classmethod
    def inject_column_types(cls, data: Any) -> Any:
        """Infer column types from first row values.

        Explicit 'type' fields in columns are not allowed - types are always
        inferred from the first row's values.
        """
        if not isinstance(data, dict):
            return data

        rows = data.get("rows", [])
        columns = data.get("columns", [])

        if not rows or not columns:
            return data

        first_row = rows[0]

        if len(first_row) != len(columns):
            raise ValueError(
                f"First row has {len(first_row)} values but "
                f"{len(columns)} columns are defined"
            )

        # Inject inferred types from first row
        # (Validation already done in ParameterFile.inject_inferred_types)
        for i, col in enumerate(columns):
            if isinstance(col, dict):
                col["type"] = infer_type_from_value(first_row[i])

        return data


# Union of all parameter types (type field injected by ParameterFile validator)
Parameter = Union[
    I64Parameter,
    F64Parameter,
    StringParameter,
    BoolParameter,
    TableParameter,
]


class ParameterFile(RootModel[Dict[str, Parameter]]):
    """Root model for parameter YAML files."""

    root: Dict[str, Parameter] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def inject_inferred_types(cls, data: Any) -> Any:
        """Inject inferred types into parameter definitions before validation.

        Types are always inferred from values. Explicit 'type' fields for
        scalar parameters are rejected.
        """
        if not isinstance(data, dict):
            return data

        # Infer and inject type for each parameter
        for param_name, param_data in data.items():
            if isinstance(param_data, dict):
                # For tables, check columns early to give clear error before union discrimination
                if param_data.get("type") == "table" or (
                    "columns" in param_data and "rows" in param_data
                ):
                    columns = param_data.get("columns", [])
                    rows = param_data.get("rows", [])

                    # Check for explicit type fields in columns
                    for i, col in enumerate(columns):
                        if isinstance(col, dict) and "type" in col:
                            col_name = col.get("name", f"column {i}")
                            raise ValueError(
                                f"Parameter '{param_name}': Column '{col_name}': "
                                f"Explicit 'type' field not allowed. "
                                f"Types are inferred from row values."
                            )

                    # Check type consistency across rows
                    if rows and columns:
                        first_row = rows[0]
                        if len(first_row) != len(columns):
                            raise ValueError(
                                f"Parameter '{param_name}': First row has {len(first_row)} values "
                                f"but {len(columns)} columns are defined"
                            )

                        # Infer types from first row
                        inferred_types = []
                        for i, value in enumerate(first_row):
                            try:
                                inferred_types.append(infer_type_from_value(value))
                            except ValueError as e:
                                col_name = (
                                    columns[i].get("name", f"column {i}")
                                    if i < len(columns) and isinstance(columns[i], dict)
                                    else f"column {i}"
                                )
                                raise ValueError(
                                    f"Parameter '{param_name}': Row 0, column '{col_name}': {e}"
                                ) from e

                        # Validate all rows for type consistency
                        for row_idx, row in enumerate(rows):
                            if len(row) != len(columns):
                                raise ValueError(
                                    f"Parameter '{param_name}': Row {row_idx} has {len(row)} values "
                                    f"but {len(columns)} columns are defined"
                                )

                            for col_idx, value in enumerate(row):
                                col_name = (
                                    columns[col_idx].get("name", f"column {col_idx}")
                                    if col_idx < len(columns)
                                    and isinstance(columns[col_idx], dict)
                                    else f"column {col_idx}"
                                )
                                expected_type = inferred_types[col_idx]

                                try:
                                    actual_type = infer_type_from_value(value)
                                except ValueError as e:
                                    raise ValueError(
                                        f"Parameter '{param_name}': Row {row_idx}, column '{col_name}': {e}"
                                    ) from e

                                if actual_type != expected_type:
                                    raise ValueError(
                                        f"Parameter '{param_name}': Row {row_idx}, column '{col_name}': "
                                        f"Inconsistent type. Expected {expected_type} (inferred from first row), "
                                        f"but got {actual_type}."
                                    )

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
