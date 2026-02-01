#!/usr/bin/env python3
"""Unit tests for parameter YAML validation using Pydantic models.

These tests validate the behavior of Pydantic-based parameter validation.
"""

import tempfile

import pytest
import yaml

from validate_parameters import validate_parameters  # type: ignore


def _create_temp_yaml(data):
    """Create a temporary YAML file with the given data."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    yaml.dump(data, tmp)
    tmp.close()
    return tmp.name


def _assert_words_in_string_list(errors, words):
    try:
        assert any(
            any(word.lower() in str(e).lower() for word in words) for e in errors
        )
    except Exception:
        print("errors:", errors)
        raise


def test_valid_simple_parameters():
    """Test validation passes for valid simple parameters."""
    data = {
        "parameters": {
            "test_i32_v1": {
                "type": "i32",
                "value": 42,
                "description": "A 32-bit integer",
            },
            "test_f64_v1": {
                "type": "f64",
                "value": 3.14,
                "unit": "m/s",
                "description": "A 64-bit float",
            },
            "test_string_v1": {
                "type": "string",
                "value": "hello",
                "description": "A string value",
            },
            "test_bool_v1": {
                "type": "bool",
                "value": True,
                "description": "A boolean value",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert success, f"Validation failed: {errors}"


def test_valid_table_parameter():
    """Test validation passes for valid table parameter."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "A table parameter",
                "columns": [
                    {"name": "col_a", "type": "i32"},
                    {"name": "col_b", "type": "f64", "unit": "m"},
                ],
                "rows": [
                    [1, 2.5],
                    [2, 3.7],
                ],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert success, "Validation failed: {errors}"


def test_valid_single_version_param():
    """Test validation passes for a single-version parameter with _v1 suffix."""
    data = {
        "parameters": {
            "wheel_count_v1": {
                "type": "i32",
                "value": 4,
                "description": "Number of wheels",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert success, f"Validation failed: {errors}"


def test_valid_multi_version_param():
    """Test validation passes for multi-version parameters."""
    data = {
        "parameters": {
            "velocity_v1": {
                "type": "f64",
                "value": 50.0,
                "unit": "m/s",
                "description": "Original velocity",
            },
            "velocity_v2": {
                "type": "f64",
                "value": 55.0,
                "unit": "m/s",
                "description": "Updated velocity",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert success, f"Validation failed: {errors}"


def test_valid_multi_version_with_type_change():
    """Test validation passes for multi-version params with different types."""
    data = {
        "parameters": {
            "velocity_v1": {
                "type": "f64",
                "value": 50.0,
                "unit": "m/s",
                "description": "Original velocity as float",
            },
            "velocity_v2": {
                "type": "i32",
                "value": 55,
                "unit": "m/s",
                "description": "Updated velocity as int",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert success, f"Validation failed: {errors}"


def test_reject_key_without_version_suffix():
    """Test validation fails for key without _vN suffix."""
    data = {
        "parameters": {
            "wheel_count": {
                "type": "i32",
                "value": 4,
                "description": "Missing version suffix",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["must match pattern", "_v"])


def test_reject_non_consecutive_versions():
    """Test validation fails for non-consecutive versions (_v1 + _v3)."""
    data = {
        "parameters": {
            "velocity_v1": {
                "type": "f64",
                "value": 50.0,
                "description": "Version 1",
            },
            "velocity_v3": {
                "type": "f64",
                "value": 60.0,
                "description": "Version 3 - gap!",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["consecutive"])


def test_reject_versions_not_starting_from_1():
    """Test validation fails when versions don't start from 1."""
    data = {
        "parameters": {
            "velocity_v2": {
                "type": "f64",
                "value": 55.0,
                "description": "Starting from v2",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["consecutive"])


def test_reject_version_zero():
    """Test validation fails for _v0 suffix."""
    data = {
        "parameters": {
            "velocity_v0": {
                "type": "f64",
                "value": 50.0,
                "description": "Version 0 not allowed",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["must match pattern", "_v"])


def test_missing_parameters_field():
    """Test validation fails when 'parameters' field is missing."""
    data = {"not_parameters": {}}
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    assert len(errors) > 0


def test_empty_parameters_object():
    """Test validation fails for empty parameters object."""
    data = {"parameters": {}}
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(
        errors,
        [
            "should have at least 1 item",
            "does not have enough properties",
        ],
    )


def test_missing_type_field():
    """Test validation fails when 'type' field is missing."""
    data = {
        "parameters": {
            "test_param_v1": {
                "value": 42,
                "description": "Missing type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    # Error message varies depending on which allOf branch is evaluated
    assert len(errors) > 0


def test_missing_description_field():
    """Test validation fails when 'description' field is missing."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "value": 42,
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["description"])


def test_empty_description():
    """Test validation fails for empty description string."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "value": 42,
                "description": "",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(
        errors, ["should have at least 1 character", "minLength", "too short"]
    )


def test_wrong_value_type_for_i64_do_not_allow_coercing():
    """Test validation fails when value is a string instead of an i64."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i64",
                "value": "42",
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["integer", "type"])


def test_too_high_value_for_i64():
    """Test validation fails when value is too high for i64."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i64",
                "value": 9223372036854775807,
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["less"])


def test_too_low_value_for_i64():
    """Test validation fails when value is too low for i64."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i64",
                "value": -9223372036854775809,
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["greater"])


def test_invalid_type_enum():
    """Test validation fails for invalid type enum value."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "double",  # Invalid, should be f64
                "value": 3.14,
                "description": "Invalid type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    assert any(
        "enum" in str(e).lower()
        or "not one of" in str(e).lower()
        or "not a valid" in str(e).lower()
        for e in errors
    )


def test_missing_value_for_i32():
    """Test validation fails when 'value' is missing for i32 type."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "description": "Missing value",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    assert any("value" in str(e).lower() for e in errors)


def test_wrong_value_type_for_i32():
    """Test validation fails when value is not an integer for i32."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "value": "not an integer",
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["integer", "type"])


def test_wrong_value_type_for_i32_do_not_allow_coercing():
    """Test validation fails when value is a string instead of an i32."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "value": "42",
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["integer", "type"])


def test_too_high_value_for_i32():
    """Test validation fails when value is too high for i32."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "value": 2147483647,
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["less"])


def test_too_low_value_for_i32():
    """Test validation fails when value is too low for i32."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "value": -2147483649,
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["greater"])


def test_negative_value_for_u32():
    """Test validation fails for negative value with u32 type."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "u32",
                "value": -5,
                "description": "Negative unsigned int",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["minimum", "0"])


def test_wrong_value_type_for_u32_do_not_allow_coercing():
    """Test validation fails when value is a string instead of an u32."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "u32",
                "value": "42",
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["integer", "type"])


def test_too_high_value_for_u32():
    """Test validation fails when value is too high for u32."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "u32",
                "value": 4294967296,
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["less"])


def test_negative_value_for_u64():
    """Test validation fails for negative value with u64 type."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "u64",
                "value": -100,
                "description": "Negative unsigned int",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["minimum", "0"])


def test_wrong_value_type_for_u64_do_not_allow_coercing():
    """Test validation fails when value is a string instead of an u64."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "u64",
                "value": "42",
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["integer", "type"])


def test_too_high_value_for_u64():
    """Test validation fails when value is too high for u64."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "u64",
                "value": 18446744073709551616,
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["less"])


def test_wrong_value_type_for_f32():
    """Test validation fails when value is not a number for f32."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "f32",
                "value": "not a number",
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["number", "type"])


def test_no_coercing_for_f32():
    """Test validation fails when value is not a number for f32."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "f32",
                "value": "3.14",
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["number", "type"])


def test_no_coercing_for_f64():
    """Test validation fails when value is not a number for f64."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "f64",
                "value": "3.14",
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["number", "type"])


def test_wrong_value_type_for_string():
    """Test validation fails when value is not a string for string type."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "string",
                "value": 123,
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["string", "type"])


def test_wrong_value_type_for_bool():
    """Test validation fails when value is not a boolean for bool type."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "bool",
                "value": "true",  # String instead of boolean
                "description": "Wrong value type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["boolean", "type"])


def test_table_missing_columns():
    """Test validation fails when table is missing 'columns' field."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Missing columns",
                "rows": [[1, 2]],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["columns"])


def test_table_missing_rows():
    """Test validation fails when table is missing 'rows' field."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Missing rows",
                "columns": [{"name": "col_a", "type": "i32"}],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["rows"])


def test_table_empty_columns():
    """Test validation fails for table with empty columns array."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Empty columns",
                "columns": [],
                "rows": [],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(
        errors,
        [
            "should have at least 1 item",
            "minItems",
            "too short",
        ],
    )


def test_table_empty_rows():
    """Test validation fails for table with empty rows array."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Empty rows",
                "columns": [{"name": "col_a", "type": "i32"}],
                "rows": [],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(
        errors,
        [
            "should have at least 1 item",
            "minItems",
            "too short",
        ],
    )


def test_table_with_value_field():
    """Test validation fails when table has 'value' field."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Table with value field",
                "value": "should not be here",
                "columns": [{"name": "col_a", "type": "i32"}],
                "rows": [[1]],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    # The schema sets "value": false for table type, which means value field is not allowed


def test_column_missing_name():
    """Test validation fails when column is missing 'name' field."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Column missing name",
                "columns": [{"type": "i32"}],
                "rows": [[1]],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["name"])


def test_column_missing_type():
    """Test validation fails when column is missing 'type' field."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Column missing type",
                "columns": [{"name": "col_a"}],
                "rows": [[1]],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["type"])


@pytest.mark.parametrize(
    "invalid_name",
    [
        "Column",  # Capital letter
        "123col",  # Starts with number
        "col-name",  # Contains hyphen
        "col name",  # Contains space
    ],
)
def test_column_invalid_name_pattern(invalid_name):
    """Test validation fails for column name that doesn't match pattern."""
    # Column names must match ^[a-z][a-z0-9_]*$
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Invalid column name",
                "columns": [{"name": invalid_name, "type": "i32"}],
                "rows": [[1]],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success, f"Should fail for column name: {invalid_name}"
    _assert_words_in_string_list(errors, ["does not match"])


def test_column_invalid_type_enum():
    """Test validation fails for invalid column type."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Invalid column type",
                "columns": [
                    {"name": "col_a", "type": "table"}
                ],  # table type not allowed in columns
                "rows": [[1]],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["enum", "not one of"])


def test_additional_properties_not_allowed():
    """Test validation fails for additional properties not in schema."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "value": 42,
                "description": "Test",
                "extra_field": "not allowed",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["additional"])


def test_additional_top_level_properties_not_allowed():
    """Test validation fails for additional top-level properties."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "value": 42,
                "description": "Test",
            }
        },
        "extra_top_level": "not allowed",
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert not success
    _assert_words_in_string_list(errors, ["additional"])


def test_all_integer_types():
    """Test all integer types with valid values."""
    data = {
        "parameters": {
            "test_i32_v1": {
                "type": "i32",
                "value": -42,
                "description": "i32",
            },
            "test_i64_v1": {
                "type": "i64",
                "value": -9223372036854775807,
                "description": "i64",
            },
            "test_u32_v1": {
                "type": "u32",
                "value": 42,
                "description": "u32",
            },
            "test_u64_v1": {
                "type": "u64",
                "value": 18446744073709551615,
                "description": "u64",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert success, "Validation failed: {errors}"


def test_all_float_types():
    """Test all float types with valid values."""
    data = {
        "parameters": {
            "test_f32_v1": {
                "type": "f32",
                "value": 3.14,
                "description": "f32",
            },
            "test_f64_v1": {
                "type": "f64",
                "value": 2.718281828,
                "description": "f64",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert success, "Validation failed: {errors}"


def test_integers_accepted_for_floats():
    """Test that integers are accepted for float types (JSON schema allows this)."""
    data = {
        "parameters": {
            "test_f32_v1": {
                "type": "f32",
                "value": 42,
                "description": "Integer for f32",
            },
            "test_f64_v1": {
                "type": "f64",
                "value": 100,
                "description": "Integer for f64",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    success, errors = validate_parameters(yaml_path)
    assert success, "Validation failed: {errors}"
