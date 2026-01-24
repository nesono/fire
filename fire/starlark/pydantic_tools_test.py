"""Tests for pydantic_tools module."""

import pytest
from pydantic import BaseModel, Field, ValidationError, field_validator

from fire.starlark.pydantic_tools import format_validation_errors


class _SimpleModel(BaseModel):
    """Test model with basic fields."""

    model_config = {"extra": "forbid"}

    name: str = Field(min_length=1)
    version: int = Field(ge=1, strict=True)
    value: float = Field(strict=True)
    enabled: bool = Field(strict=True)


class _NestedModel(BaseModel):
    """Test model with nested structure."""

    items: list[_SimpleModel]


class _CustomValidatorModel(BaseModel):
    """Test model with a custom field_validator."""

    name: str

    @field_validator("name")
    @classmethod
    def name_must_be_upper(cls, v: str) -> str:
        if not v.isupper():
            raise ValueError("name must be uppercase")
        return v


def test_missing_field():
    with pytest.raises(ValidationError) as exc_info:
        _SimpleModel(name="x", version=1, value=1.0)  # type: ignore
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 1
    assert "'enabled' is a required property" in errors[0]


def test_string_too_short():
    with pytest.raises(ValidationError) as exc_info:
        _SimpleModel(name="", version=1, value=1.0, enabled=True)
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 1
    assert "at least" in errors[0]
    assert "character" in errors[0]


def test_int_type_error():
    with pytest.raises(ValidationError) as exc_info:
        _SimpleModel(name="x", version="not_int", value=1.0, enabled=True)  # type: ignore
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 1
    assert "not a valid integer" in errors[0]


def test_float_type_error():
    with pytest.raises(ValidationError) as exc_info:
        _SimpleModel(name="x", version=1, value="not_float", enabled=True)  # type: ignore
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 1
    assert "not a valid number" in errors[0]


def test_bool_type_error():
    with pytest.raises(ValidationError) as exc_info:
        _SimpleModel(name="x", version=1, value=1.0, enabled="yes")  # type: ignore
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 1
    assert "not a valid boolean" in errors[0]


def test_greater_than_equal():
    with pytest.raises(ValidationError) as exc_info:
        _SimpleModel(name="x", version=0, value=1.0, enabled=True)
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 1
    assert ">=" in errors[0]


def test_extra_forbidden():
    with pytest.raises(ValidationError) as exc_info:
        _SimpleModel(name="x", version=1, value=1.0, enabled=True, extra="bad")  # type: ignore
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 1
    assert "Additional properties are not allowed" in errors[0]
    assert "'extra' was unexpected" in errors[0]


def test_value_error_from_field_validator():
    with pytest.raises(ValidationError) as exc_info:
        _CustomValidatorModel(name="lower")
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 1
    assert "name must be uppercase" in errors[0]
    assert "Value error" not in errors[0]


def test_nested_path():
    with pytest.raises(ValidationError) as exc_info:
        _NestedModel(items=[{"name": "x", "version": "bad", "value": 1.0, "enabled": True}])  # type: ignore
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 1
    assert "items -> 0 -> version" in errors[0]


def test_skip_loc_tags():
    with pytest.raises(ValidationError) as exc_info:
        _NestedModel(items=[{"name": "x", "version": "bad", "value": 1.0, "enabled": True}])  # type: ignore
    errors = format_validation_errors(exc_info.value, skip_loc_tags=["0"])
    assert len(errors) == 1
    assert "items -> version" in errors[0]


def test_multiple_errors():
    with pytest.raises(ValidationError) as exc_info:
        _SimpleModel(name="", version="bad", value="bad", enabled="bad")  # type: ignore
    errors = format_validation_errors(exc_info.value)
    assert len(errors) == 4


def test_empty_validation_error_list():
    errors = format_validation_errors(None)
    assert errors == []
