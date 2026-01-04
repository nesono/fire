#!/usr/bin/env python3
"""Unit tests for parameter YAML validation against JSON schema.

These tests capture the current jsonschema-based validation behavior
to ensure feature parity when migrating to a different validation library.
"""

import tempfile
import unittest
from pathlib import Path

import yaml

from validate_parameters import validate_parameters  # type: ignore


class TestParameterValidation(unittest.TestCase):
    """Test parameter YAML validation."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Path to the schema file
        cls.schema_path = Path(__file__).parent / "parameter_schema.json"

    def _create_temp_yaml(self, data):
        """Create a temporary YAML file with the given data."""
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        yaml.dump(data, tmp)
        tmp.close()
        return tmp.name

    def _assert_words_in_string_list(self, errors, words):
        try:
            self.assertTrue(
                any(
                    any(word.lower() in str(e).lower() for word in words)
                    for e in errors
                )
            )
        except Exception:
            print("errors:", errors)
            raise

    def test_valid_simple_parameters(self):
        """Test validation passes for valid simple parameters."""
        data = {
            "parameters": {
                "test_i32": {
                    "type": "i32",
                    "value": 42,
                    "description": "A 32-bit integer",
                    "version": 1,
                },
                "test_f64": {
                    "type": "f64",
                    "value": 3.14,
                    "unit": "m/s",
                    "description": "A 64-bit float",
                    "version": 1,
                },
                "test_string": {
                    "type": "string",
                    "value": "hello",
                    "description": "A string value",
                    "version": 1,
                },
                "test_bool": {
                    "type": "bool",
                    "value": True,
                    "description": "A boolean value",
                    "version": 1,
                },
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertTrue(success, f"Validation failed: {errors}")

    def test_valid_table_parameter(self):
        """Test validation passes for valid table parameter."""
        data = {
            "parameters": {
                "test_table": {
                    "type": "table",
                    "description": "A table parameter",
                    "version": 1,
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
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertTrue(success, f"Validation failed: {errors}")

    def test_missing_parameters_field(self):
        """Test validation fails when 'parameters' field is missing."""
        data = {"not_parameters": {}}
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self.assertTrue(len(errors) > 0)

    def test_empty_parameters_object(self):
        """Test validation fails for empty parameters object."""
        data = {"parameters": {}}
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(
            errors,
            [
                "should have at least 1 item",
                "does not have enough properties",
            ],
        )

    def test_missing_type_field(self):
        """Test validation fails when 'type' field is missing."""
        data = {
            "parameters": {
                "test_param": {
                    "value": 42,
                    "description": "Missing type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        # Error message varies depending on which allOf branch is evaluated
        self.assertTrue(len(errors) > 0)

    def test_missing_description_field(self):
        """Test validation fails when 'description' field is missing."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": 42,
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["description"])

    def test_empty_description(self):
        """Test validation fails for empty description string."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": 42,
                    "description": "",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(
            errors, ["should have at least 1 character", "minLength", "too short"]
        )

    def test_missing_version_field(self):
        """Test validation fails when 'version' field is missing."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": 42,
                    "description": "Missing version",
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["version"])

    def test_invalid_version_zero(self):
        """Test validation fails for version = 0."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": 42,
                    "description": "Invalid version",
                    "version": 0,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self.assertTrue(
            any(
                "greater than or equal to 1" in str(e)
                or "minimum" in str(e).lower()
                or ">= 1" in str(e)
                for e in errors
            )
        )

    def test_invalid_version_negative(self):
        """Test validation fails for negative version."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": 42,
                    "description": "Invalid version",
                    "version": -1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self.assertTrue(
            any(
                "greater than or equal to 1" in str(e)
                or "minimum" in str(e).lower()
                or ">= 1" in str(e)
                for e in errors
            )
        )

    def test_wrong_value_type_for_i64_do_not_allow_coercing(self):
        """Test validation fails when value is a string instead of an i64."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i64",
                    "value": "42",
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["integer", "type"])

    def test_too_high_value_for_i64(self):
        """Test validation fails when value is too high for i64."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i64",
                    "value": 9223372036854775807,
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["less"])

    def test_too_low_value_for_i64(self):
        """Test validation fails when value is too low for i64."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i64",
                    "value": -9223372036854775809,
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["greater"])

    def test_invalid_type_enum(self):
        """Test validation fails for invalid type enum value."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "double",  # Invalid, should be f64
                    "value": 3.14,
                    "description": "Invalid type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self.assertTrue(
            any(
                "enum" in str(e).lower()
                or "not one of" in str(e).lower()
                or "not a valid" in str(e).lower()
                for e in errors
            )
        )

    def test_missing_value_for_i32(self):
        """Test validation fails when 'value' is missing for i32 type."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "description": "Missing value",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self.assertTrue(any("value" in str(e).lower() for e in errors))

    def test_wrong_value_type_for_i32(self):
        """Test validation fails when value is not an integer for i32."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": "not an integer",
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["integer", "type"])

    def test_wrong_value_type_for_i32_do_not_allow_coercing(self):
        """Test validation fails when value is a string instead of an i32."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": "42",
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["integer", "type"])

    def test_too_high_value_for_i32(self):
        """Test validation fails when value is too high for i32."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": 2147483647,
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["less"])

    def test_too_low_value_for_i32(self):
        """Test validation fails when value is too low for i32."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": -2147483649,
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["greater"])

    def test_negative_value_for_u32(self):
        """Test validation fails for negative value with u32 type."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "u32",
                    "value": -5,
                    "description": "Negative unsigned int",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["minimum", "0"])

    def test_wrong_value_type_for_u32_do_not_allow_coercing(self):
        """Test validation fails when value is a string instead of an u32."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "u32",
                    "value": "42",
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["integer", "type"])

    def test_too_high_value_for_u32(self):
        """Test validation fails when value is too high for u32."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "u32",
                    "value": 4294967296,
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["less"])

    def test_negative_value_for_u64(self):
        """Test validation fails for negative value with u64 type."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "u64",
                    "value": -100,
                    "description": "Negative unsigned int",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["minimum", "0"])

    def test_wrong_value_type_for_f32(self):
        """Test validation fails when value is not a number for f32."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "f32",
                    "value": "not a number",
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["number", "type"])

    def test_wrong_value_type_for_string(self):
        """Test validation fails when value is not a string for string type."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "string",
                    "value": 123,
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["string", "type"])

    def test_wrong_value_type_for_bool(self):
        """Test validation fails when value is not a boolean for bool type."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "bool",
                    "value": "true",  # String instead of boolean
                    "description": "Wrong value type",
                    "version": 1,
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["boolean", "type"])

    def test_table_missing_columns(self):
        """Test validation fails when table is missing 'columns' field."""
        data = {
            "parameters": {
                "test_table": {
                    "type": "table",
                    "description": "Missing columns",
                    "version": 1,
                    "rows": [[1, 2]],
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["columns"])

    def test_table_missing_rows(self):
        """Test validation fails when table is missing 'rows' field."""
        data = {
            "parameters": {
                "test_table": {
                    "type": "table",
                    "description": "Missing rows",
                    "version": 1,
                    "columns": [{"name": "col_a", "type": "i32"}],
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["rows"])

    def test_table_empty_columns(self):
        """Test validation fails for table with empty columns array."""
        data = {
            "parameters": {
                "test_table": {
                    "type": "table",
                    "description": "Empty columns",
                    "version": 1,
                    "columns": [],
                    "rows": [],
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(
            errors,
            [
                "should have at least 1 item",
                "minItems",
                "too short",
            ],
        )

    def test_table_empty_rows(self):
        """Test validation fails for table with empty rows array."""
        data = {
            "parameters": {
                "test_table": {
                    "type": "table",
                    "description": "Empty rows",
                    "version": 1,
                    "columns": [{"name": "col_a", "type": "i32"}],
                    "rows": [],
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(
            errors,
            [
                "should have at least 1 item",
                "minItems",
                "too short",
            ],
        )

    def test_table_with_value_field(self):
        """Test validation fails when table has 'value' field."""
        data = {
            "parameters": {
                "test_table": {
                    "type": "table",
                    "description": "Table with value field",
                    "version": 1,
                    "value": "should not be here",
                    "columns": [{"name": "col_a", "type": "i32"}],
                    "rows": [[1]],
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        # The schema sets "value": false for table type, which means value field is not allowed

    def test_column_missing_name(self):
        """Test validation fails when column is missing 'name' field."""
        data = {
            "parameters": {
                "test_table": {
                    "type": "table",
                    "description": "Column missing name",
                    "version": 1,
                    "columns": [{"type": "i32"}],
                    "rows": [[1]],
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["name"])

    def test_column_missing_type(self):
        """Test validation fails when column is missing 'type' field."""
        data = {
            "parameters": {
                "test_table": {
                    "type": "table",
                    "description": "Column missing type",
                    "version": 1,
                    "columns": [{"name": "col_a"}],
                    "rows": [[1]],
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["type"])

    def test_column_invalid_name_pattern(self):
        """Test validation fails for column name that doesn't match pattern."""
        # Column names must match ^[a-z][a-z0-9_]*$
        invalid_names = [
            "Column",  # Capital letter
            "123col",  # Starts with number
            "col-name",  # Contains hyphen
            "col name",  # Contains space
        ]

        for invalid_name in invalid_names:
            with self.subTest(name=invalid_name):
                data = {
                    "parameters": {
                        "test_table": {
                            "type": "table",
                            "description": "Invalid column name",
                            "version": 1,
                            "columns": [{"name": invalid_name, "type": "i32"}],
                            "rows": [[1]],
                        }
                    }
                }
                yaml_path = self._create_temp_yaml(data)
                success, errors = validate_parameters(yaml_path, str(self.schema_path))
                self.assertFalse(
                    success, f"Should fail for column name: {invalid_name}"
                )
                self._assert_words_in_string_list(errors, ["does not match"])

    def test_column_invalid_type_enum(self):
        """Test validation fails for invalid column type."""
        data = {
            "parameters": {
                "test_table": {
                    "type": "table",
                    "description": "Invalid column type",
                    "version": 1,
                    "columns": [
                        {"name": "col_a", "type": "table"}
                    ],  # table type not allowed in columns
                    "rows": [[1]],
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["enum", "not one of"])

    def test_additional_properties_not_allowed(self):
        """Test validation fails for additional properties not in schema."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": 42,
                    "description": "Test",
                    "version": 1,
                    "extra_field": "not allowed",
                }
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["additional"])

    def test_additional_top_level_properties_not_allowed(self):
        """Test validation fails for additional top-level properties."""
        data = {
            "parameters": {
                "test_param": {
                    "type": "i32",
                    "value": 42,
                    "description": "Test",
                    "version": 1,
                }
            },
            "extra_top_level": "not allowed",
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertFalse(success)
        self._assert_words_in_string_list(errors, ["additional"])

    def test_all_integer_types(self):
        """Test all integer types with valid values."""
        data = {
            "parameters": {
                "test_i32": {
                    "type": "i32",
                    "value": -42,
                    "description": "i32",
                    "version": 1,
                },
                "test_i64": {
                    "type": "i64",
                    "value": -9223372036854775807,
                    "description": "i64",
                    "version": 1,
                },
                "test_u32": {
                    "type": "u32",
                    "value": 42,
                    "description": "u32",
                    "version": 1,
                },
                "test_u64": {
                    "type": "u64",
                    "value": 18446744073709551615,
                    "description": "u64",
                    "version": 1,
                },
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertTrue(success, f"Validation failed: {errors}")

    def test_all_float_types(self):
        """Test all float types with valid values."""
        data = {
            "parameters": {
                "test_f32": {
                    "type": "f32",
                    "value": 3.14,
                    "description": "f32",
                    "version": 1,
                },
                "test_f64": {
                    "type": "f64",
                    "value": 2.718281828,
                    "description": "f64",
                    "version": 1,
                },
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertTrue(success, f"Validation failed: {errors}")

    def test_integers_accepted_for_floats(self):
        """Test that integers are accepted for float types (JSON schema allows this)."""
        data = {
            "parameters": {
                "test_f32": {
                    "type": "f32",
                    "value": 42,
                    "description": "Integer for f32",
                    "version": 1,
                },
                "test_f64": {
                    "type": "f64",
                    "value": 100,
                    "description": "Integer for f64",
                    "version": 1,
                },
            }
        }
        yaml_path = self._create_temp_yaml(data)
        success, errors = validate_parameters(yaml_path, str(self.schema_path))
        self.assertTrue(success, f"Validation failed: {errors}")


if __name__ == "__main__":
    unittest.main()
