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
        "test_i64_v1": {
            "value": 42,
            "unit": "1",
            "description": "A 64-bit integer",
        },
        "test_f64_v1": {
            "value": 3.14,
            "unit": "m/s",
            "description": "A 64-bit float",
        },
        "test_string_v1": {
            "value": "hello",
            "unit": "1",
            "description": "A string value",
        },
        "test_bool_v1": {
            "value": True,
            "unit": "1",
            "description": "A boolean value",
        },
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_explicit_type_rejected_for_scalars():
    """Test validation fails when type is explicitly provided for scalar parameters."""
    data = {
        "test_i64_v1": {
            "type": "i64",  # Not allowed - type inferred from value
            "value": 42,
            "unit": "1",
            "description": "Explicit i64",
        },
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(
        errors, ["Explicit 'type' field not allowed", "inferred"]
    )


def test_infer_i64_from_int():
    """Test type inference for YAML integer -> i64."""
    data = {
        "count_v1": {
            "value": 42,
            "unit": "1",
            "description": "Integer value",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_infer_f64_from_float():
    """Test type inference for YAML float -> f64."""
    data = {
        "speed_v1": {
            "value": 42.0,
            "unit": "1",
            "description": "Float value",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_infer_bool_from_bool():
    """Test type inference for YAML bool -> bool."""
    data = {
        "enabled_v1": {
            "value": True,
            "unit": "1",
            "description": "Boolean value",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_infer_string_from_string():
    """Test type inference for YAML string -> string."""
    data = {
        "name_v1": {
            "value": "test",
            "unit": "1",
            "description": "String value",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_valid_table_parameter():
    """Test validation passes for valid table parameter with type inference."""
    data = {
        "test_table_v1": {
            "type": "table",
            "description": "A table parameter",
            "columns": [
                {"name": "col_a", "unit": "1"},
                {"name": "col_b", "unit": "m"},
            ],
            "rows": [
                [1, 2.5],
                [2, 3.7],
            ],
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_scalar_explicit_type_rejected():
    """Test validation fails when scalar parameter has explicit 'type' field."""
    data = {
        "wheel_count_v1": {
            "type": "i64",  # Explicit type not allowed for scalar parameters
            "value": 4,
            "unit": "1",
            "description": "Test parameter",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(
        errors, ["Explicit 'type' field not allowed", "inferred", "scalar"]
    )


def test_valid_single_version_param():
    """Test validation passes for a single-version parameter with _v1 suffix."""
    data = {
        "wheel_count_v1": {
            "value": 4,
            "unit": "1",
            "description": "Number of wheels",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_valid_multi_version_param():
    """Test validation passes for multi-version parameters."""
    data = {
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
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_valid_multi_version_with_type_change():
    """Test validation passes for multi-version params with different types."""
    data = {
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
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_reject_key_without_version_suffix():
    """Test validation fails for key without _vN suffix."""
    data = {
        "wheel_count": {
            "value": 4,
            "unit": "1",
            "description": "Missing version suffix",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["must match pattern", "_v"])


def test_reject_non_consecutive_versions():
    """Test validation fails for non-consecutive versions (_v1 + _v3)."""
    data = {
        "velocity_v1": {
            "value": 50.0,
            "unit": "1",
            "description": "Version 1",
        },
        "velocity_v3": {
            "value": 60.0,
            "unit": "1",
            "description": "Version 3 - gap!",
        },
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["consecutive"])


def test_reject_more_than_two_versions():
    """Test validation fails for more than two versions active (_v1, _v2 _v3)."""
    data = {
        "velocity_v1": {
            "value": 50.0,
            "unit": "1",
            "description": "Version 1",
        },
        "velocity_v2": {
            "value": 50.0,
            "unit": "1",
            "description": "Version 2",
        },
        "velocity_v3": {
            "value": 60.0,
            "unit": "1",
            "description": "Version 3",
        },
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["two entries"])


def test_reject_versions_not_starting_from_1():
    """Test validation passes when versions don't start from 1."""
    data = {
        "velocity_v2": {
            "value": 55.0,
            "unit": "1",
            "description": "Starting from v2",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


def test_reject_version_zero():
    """Test validation fails for _v0 suffix."""
    data = {
        "velocity_v0": {
            "value": 50.0,
            "unit": "1",
            "description": "Version 0 not allowed",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["must match pattern", "_v"])


def test_invalid_parameter_structure():
    """Test validation fails when parameter structure is invalid."""
    data = {"not_valid_v1": "string instead of dict"}
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    assert len(errors) > 0


def test_empty_parameters_object():
    """Test validation fails for empty parameters object."""
    data = {}
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
        "test_param_v1": {
            "unit": "1",
            "description": "Missing value",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["value"])


def test_missing_description_field():
    """Test validation fails when 'description' field is missing."""
    data = {
        "test_param_v1": {
            "value": 42,
            "unit": "1",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["description"])


def test_empty_description():
    """Test validation fails for empty description string."""
    data = {
        "test_param_v1": {
            "value": 42,
            "unit": "1",
            "description": "",
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
        "test_param_v1": {
            "type": "i64",
            "value": "42",
            "unit": "1",
            "description": "Wrong value type",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["integer", "type"])


def test_no_coercing_for_f64():
    """Test validation fails when value is not a number for f64."""
    data = {
        "test_param_v1": {
            "type": "f64",
            "value": "3.14",
            "unit": "1",
            "description": "Wrong value type",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["number", "type"])


def test_wrong_value_type_for_string():
    """Test validation fails when value is not a string for string type."""
    data = {
        "test_param_v1": {
            "type": "string",
            "value": 123,
            "unit": "1",
            "description": "Wrong value type",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["string", "type"])


def test_wrong_value_type_for_bool():
    """Test validation fails when value is not a boolean for bool type."""
    data = {
        "test_param_v1": {
            "type": "bool",
            "value": "true",  # String instead of boolean
            "unit": "1",
            "description": "Wrong value type",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["boolean", "type"])


def test_table_missing_columns():
    """Test validation fails when table is missing 'columns' field."""
    data = {
        "test_table_v1": {
            "type": "table",
            "description": "Missing columns",
            "rows": [[1, 2]],
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["columns"])


def test_table_missing_rows():
    """Test validation fails when table is missing 'rows' field."""
    data = {
        "test_table_v1": {
            "type": "table",
            "description": "Missing rows",
            "columns": [{"name": "col_a", "unit": "1"}],
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["rows"])


def test_table_empty_columns():
    """Test validation fails for table with empty columns array."""
    data = {
        "test_table_v1": {
            "type": "table",
            "description": "Empty columns",
            "columns": [],
            "rows": [],
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
        "test_table_v1": {
            "type": "table",
            "description": "Empty rows",
            "columns": [{"name": "col_a", "unit": "1"}],
            "rows": [],
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
        "test_table_v1": {
            "type": "table",
            "description": "Table with value field",
            "value": "should not be here",
            "columns": [{"name": "col_a", "unit": "1"}],
            "rows": [[1]],
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors


def test_column_missing_name():
    """Test validation fails when column is missing 'name' field."""
    data = {
        "test_table_v1": {
            "type": "table",
            "description": "Column missing name",
            "columns": [{"unit": "1"}],
            "rows": [[1]],
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["name"])


def test_column_type_inference():
    """Test validation passes when column type is inferred from row values."""
    data = {
        "test_table_v1": {
            "type": "table",
            "description": "Column with type inference",
            "columns": [{"name": "col_a", "unit": "1"}],
            "rows": [[1], [2], [3]],
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert not errors, f"Validation failed: {errors}"


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
        "test_table_v1": {
            "type": "table",
            "description": "Invalid column name",
            "columns": [{"name": invalid_name, "unit": "1"}],
            "rows": [[1]],
        }
    }
    yaml_path = _create_temp_yaml(data)
    result, errors = validate_parameters(yaml_path)
    assert errors, f"Should fail for column name: {invalid_name}"
    _assert_words_in_string_list(errors, ["does not match"])


def test_column_explicit_type_rejected():
    """Test validation fails when column has explicit 'type' field."""
    data = {
        "test_table_v1": {
            "type": "table",
            "description": "Explicit type not allowed",
            "columns": [
                {"name": "col_a", "type": "f64", "unit": "1"}
            ],  # Explicit type field not allowed
            "rows": [[1.0]],
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(
        errors, ["Explicit 'type' field not allowed", "inferred"]
    )


def test_additional_properties_not_allowed():
    """Test validation fails for additional properties not in schema."""
    data = {
        "test_param_v1": {
            "value": 42,
            "unit": "1",
            "description": "Test",
            "extra_field": "not allowed",
        }
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["additional"])


def test_additional_top_level_properties_not_allowed():
    """Test validation fails for parameter without version suffix."""
    data = {
        "test_param_v1": {
            "value": 42,
            "unit": "1",
            "description": "Test",
        },
        "extra_param_without_version": {
            "value": 99,
            "unit": "1",
            "description": "Missing version suffix",
        },
    }
    yaml_path = _create_temp_yaml(data)
    data, errors = validate_parameters(yaml_path)
    assert errors
    _assert_words_in_string_list(errors, ["must match pattern", "_v"])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
