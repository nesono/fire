"""Tests for parameter file validation."""

import unittest

from fire.parameters.validator import ParameterValidator, ValidationError


class TestParameterValidator(unittest.TestCase):
    """Test cases for parameter validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = ParameterValidator()

    def test_valid_simple_parameter(self):
        """Test validation of a simple valid parameter file."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "max_velocity",
                    "type": "float",
                    "unit": "m/s",
                    "value": 55.0,
                    "description": "Maximum velocity",
                }
            ],
        }

        # Should not raise an exception
        self.validator.validate(param_data)

    def test_missing_required_fields(self):
        """Test that missing required fields raises ValidationError."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            # Missing 'parameters' field
        }

        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate(param_data)
        self.assertIn("parameters", str(ctx.exception))

    def test_invalid_parameter_type(self):
        """Test that invalid parameter type raises ValidationError."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "test_param",
                    "type": "invalid_type",  # Invalid type
                    "value": 42,
                    "description": "Test parameter",
                }
            ],
        }

        with self.assertRaises(ValidationError):
            self.validator.validate(param_data)

    def test_valid_table_parameter(self):
        """Test validation of a table parameter."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "braking_table",
                    "type": "table",
                    "description": "Braking distances",
                    "columns": [
                        {"name": "velocity", "type": "float", "unit": "m/s"},
                        {"name": "distance", "type": "float", "unit": "m"},
                    ],
                    "rows": [[10.0, 5.0], [20.0, 20.0]],
                }
            ],
        }

        # Should not raise an exception
        self.validator.validate(param_data)

    def test_table_with_mismatched_columns(self):
        """Test that table rows must match column count."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "braking_table",
                    "type": "table",
                    "description": "Braking distances",
                    "columns": [
                        {"name": "velocity", "type": "float", "unit": "m/s"},
                        {"name": "distance", "type": "float", "unit": "m"},
                    ],
                    "rows": [[10.0, 5.0, 999.0]],  # Too many columns
                }
            ],
        }

        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate(param_data)
        self.assertIn("column", str(ctx.exception).lower())

    def test_type_checking_float(self):
        """Test that float values are validated."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "test_param",
                    "type": "float",
                    "value": "not_a_float",  # Invalid value
                    "description": "Test",
                }
            ],
        }

        with self.assertRaises(ValidationError):
            self.validator.validate(param_data)

    def test_type_checking_integer(self):
        """Test that integer values are validated."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "count",
                    "type": "integer",
                    "value": 42,
                    "description": "Test count",
                }
            ],
        }

        # Should not raise an exception
        self.validator.validate(param_data)

    def test_type_checking_string(self):
        """Test that string values are validated."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "vehicle_name",
                    "type": "string",
                    "value": "TestVehicle",
                    "description": "Vehicle identifier",
                }
            ],
        }

        # Should not raise an exception
        self.validator.validate(param_data)

    def test_type_checking_boolean(self):
        """Test that boolean values are validated."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "debug_mode",
                    "type": "boolean",
                    "value": True,
                    "description": "Enable debug mode",
                }
            ],
        }

        # Should not raise an exception
        self.validator.validate(param_data)

    def test_duplicate_parameter_names(self):
        """Test that duplicate parameter names are rejected."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "duplicate",
                    "type": "float",
                    "value": 1.0,
                    "description": "First",
                },
                {
                    "name": "duplicate",
                    "type": "float",
                    "value": 2.0,
                    "description": "Second",
                },
            ],
        }

        with self.assertRaises(ValidationError):
            self.validator.validate(param_data)

    def test_invalid_namespace(self):
        """Test that invalid namespace format is rejected."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "invalid namespace!",  # Contains space and special char
            "parameters": [],
        }

        with self.assertRaises(ValidationError):
            self.validator.validate(param_data)


if __name__ == "__main__":
    unittest.main()
