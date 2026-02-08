#!/usr/bin/env python3
"""Unit tests for parameter YAML validation using Pydantic models.

These tests validate the behavior of Pydantic-based parameter validation,
including automatic type inference from YAML values.
"""

import tempfile
import sys
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


def test_valid_simple_parameters_with_inference():
    """Test validation passes for valid simple parameters without explicit type."""
    data = {
        "parameters": {
            "test_i64_v1": {
                "value": 42,
                "description": "A 64-bit integer",
            },
            "test_f64_v1": {
                "value": 3.14,
                "unit": "m/s",
                "description": "A 64-bit float",
            },
            "test_string_v1": {
                "value": "hello",
                "description": "A string value",
            },
            "test_bool_v1": {
                "value": True,
                "description": "A boolean value",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_valid_parameters_with_explicit_type():
    """Test validation passes when type is explicitly provided."""
    data = {
        "parameters": {
            "test_i64_v1": {
                "type": "i64",
                "value": 42,
                "description": "Explicit i64",
            },
            "test_f64_v1": {
                "type": "f64",
                "value": 3.14,
                "description": "Explicit f64",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_infer_i64_from_int():
    """Test type inference for YAML integer -> i64."""
    data = {
        "parameters": {
            "count_v1": {
                "value": 42,
                "description": "Integer value",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_infer_f64_from_float():
    """Test type inference for YAML float -> f64."""
    data = {
        "parameters": {
            "speed_v1": {
                "value": 42.0,
                "description": "Float value",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_infer_bool_from_bool():
    """Test type inference for YAML bool -> bool."""
    data = {
        "parameters": {
            "enabled_v1": {
                "value": True,
                "description": "Boolean value",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_infer_string_from_string():
    """Test type inference for YAML string -> string."""
    data = {
        "parameters": {
            "name_v1": {
                "value": "test",
                "description": "String value",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_valid_table_parameter():
    """Test validation passes for valid table parameter."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "A table parameter",
                "columns": [
                    {"name": "col_a", "type": "i64"},
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
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_valid_single_version_param():
    """Test validation passes for a single-version parameter with _v1 suffix."""
    data = {
        "parameters": {
            "wheel_count_v1": {
                "value": 4,
                "description": "Number of wheels",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_valid_multi_version_param():
    """Test validation passes for multi-version parameters."""
    data = {
        "parameters": {
            "velocity_v1": {
                "value": 50.0,
                "unit": "m/s",
                "description": "Original velocity",
            },
            "velocity_v2": {
                "value": 55.0,
                "unit": "m/s",
                "description": "Updated velocity",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_valid_multi_version_with_type_change():
    """Test validation passes for multi-version params with different types."""
    data = {
        "parameters": {
            "velocity_v1": {
                "value": 50.0,
                "unit": "m/s",
                "description": "Original velocity as float",
            },
            "velocity_v2": {
                "value": 55,
                "unit": "m/s",
                "description": "Updated velocity as int",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_reject_key_without_version_suffix():
    """Test validation fails for key without _vN suffix."""
    data = {
        "parameters": {
            "wheel_count": {
                "value": 4,
                "description": "Missing version suffix",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["must match pattern", "_v"])


def test_reject_non_consecutive_versions():
    """Test validation fails for non-consecutive versions (_v1 + _v3)."""
    data = {
        "parameters": {
            "velocity_v1": {
                "value": 50.0,
                "description": "Version 1",
            },
            "velocity_v3": {
                "value": 60.0,
                "description": "Version 3 - gap!",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["consecutive"])


def test_reject_more_than_two_versions():
    """Test validation fails for more than two versions active (_v1, _v2 _v3)."""
    data = {
        "parameters": {
            "velocity_v1": {
                "value": 50.0,
                "description": "Version 1",
            },
            "velocity_v2": {
                "value": 50.0,
                "description": "Version 2",
            },
            "velocity_v3": {
                "value": 60.0,
                "description": "Version 3",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["two entries"])


def test_reject_versions_not_starting_from_1():
    """Test validation passes when versions don't start from 1."""
    data = {
        "parameters": {
            "velocity_v2": {
                "value": 55.0,
                "description": "Starting from v2",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_reject_version_zero():
    """Test validation fails for _v0 suffix."""
    data = {
        "parameters": {
            "velocity_v0": {
                "value": 50.0,
                "description": "Version 0 not allowed",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["must match pattern", "_v"])


def test_missing_parameters_field():
    """Test validation fails when 'parameters' field is missing."""
    data = {"not_parameters": {}}
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    assert len(errors) > 0


def test_empty_parameters_object():
    """Test validation fails for empty parameters object."""
    data = {"parameters": {}}
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(
        errors,
        [
            "should have at least 1 item",
            "does not have enough properties",
        ],
    )


def test_missing_value_field():
    """Test validation fails when 'value' field is missing."""
    data = {
        "parameters": {
            "test_param_v1": {
                "description": "Missing value",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["value"])


def test_missing_description_field():
    """Test validation fails when 'description' field is missing."""
    data = {
        "parameters": {
            "test_param_v1": {
                "value": 42,
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["description"])


def test_empty_description():
    """Test validation fails for empty description string."""
    data = {
        "parameters": {
            "test_param_v1": {
                "value": 42,
                "description": "",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
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
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["integer", "type"])


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
    data, errors = validate_parameters(yaml_path)
    assert errors
    assert any(
        "enum" in str(e).lower()
        or "not one of" in str(e).lower()
        or "not a valid" in str(e).lower()
        for e in errors
    )


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
    data, errors = validate_parameters(yaml_path)
    assert errors
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
    data, errors = validate_parameters(yaml_path)
    assert errors
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
    data, errors = validate_parameters(yaml_path)
    assert errors
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
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["columns"])


def test_table_missing_rows():
    """Test validation fails when table is missing 'rows' field."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Missing rows",
                "columns": [{"name": "col_a", "type": "i64"}],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
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
    data, errors = validate_parameters(yaml_path)
    assert errors
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
                "columns": [{"name": "col_a", "type": "i64"}],
                "rows": [],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
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
                "columns": [{"name": "col_a", "type": "i64"}],
                "rows": [[1]],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors


def test_column_missing_name():
    """Test validation fails when column is missing 'name' field."""
    data = {
        "parameters": {
            "test_table_v1": {
                "type": "table",
                "description": "Column missing name",
                "columns": [{"type": "i64"}],
                "rows": [[1]],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
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
    data, errors = validate_parameters(yaml_path)
    assert errors
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
                "columns": [{"name": invalid_name, "type": "i64"}],
                "rows": [[1]],
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    result, errors = validate_parameters(yaml_path)
    assert errors, f"Should fail for column name: {invalid_name}"
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
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["enum", "not one of"])


def test_additional_properties_not_allowed():
    """Test validation fails for additional properties not in schema."""
    data = {
        "parameters": {
            "test_param_v1": {
                "value": 42,
                "description": "Test",
                "extra_field": "not allowed",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["additional"])


def test_additional_top_level_properties_not_allowed():
    """Test validation fails for additional top-level properties."""
    data = {
        "parameters": {
            "test_param_v1": {
                "value": 42,
                "description": "Test",
            }
        },
        "extra_top_level": "not allowed",
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["additional"])


def test_integers_accepted_for_floats():
    """Test that integers are accepted for float types."""
    data = {
        "parameters": {
            "test_f64_v1": {
                "type": "f64",
                "value": 100,
                "description": "Integer for f64",
            },
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_obsolete_type_i32_rejected():
    """Test that obsolete type i32 is rejected."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "i32",
                "value": 42,
                "description": "Obsolete i32 type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["enum", "not one of", "not a valid"])


def test_obsolete_type_u32_rejected():
    """Test that obsolete type u32 is rejected."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "u32",
                "value": 42,
                "description": "Obsolete u32 type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["enum", "not one of", "not a valid"])


def test_obsolete_type_u64_rejected():
    """Test that obsolete type u64 is rejected."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "u64",
                "value": 42,
                "description": "Obsolete u64 type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["enum", "not one of", "not a valid"])


def test_obsolete_type_f32_rejected():
    """Test that obsolete type f32 is rejected."""
    data = {
        "parameters": {
            "test_param_v1": {
                "type": "f32",
                "value": 3.14,
                "description": "Obsolete f32 type",
            }
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["enum", "not one of", "not a valid"])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
