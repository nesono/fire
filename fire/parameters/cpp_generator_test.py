"""Tests for C++ parameter code generator."""

import unittest
from fire.parameters.cpp_generator import CppGenerator


class TestCppGenerator(unittest.TestCase):
    """Test cases for C++ code generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = CppGenerator()

    def test_generate_simple_float_parameter(self):
        """Test generating C++ code for a simple float parameter."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test.params",
            "parameters": [
                {
                    "name": "max_velocity",
                    "type": "float",
                    "unit": "m/s",
                    "value": 55.0,
                    "description": "Maximum velocity"
                }
            ]
        }

        result = self.generator.generate(param_data)

        # Check header guards
        self.assertIn("#ifndef", result)
        self.assertIn("#define", result)
        self.assertIn("#endif", result)

        # Check namespace
        self.assertIn("namespace test", result)
        self.assertIn("namespace params", result)

        # Check parameter declaration
        self.assertIn("constexpr double max_velocity", result)
        self.assertIn("55.0", result)

        # Check comment with description
        self.assertIn("Maximum velocity", result)

        # Check unit in comment
        self.assertIn("m/s", result)

    def test_generate_integer_parameter(self):
        """Test generating C++ code for an integer parameter."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "vehicle",
            "parameters": [
                {
                    "name": "wheel_count",
                    "type": "integer",
                    "value": 4,
                    "description": "Number of wheels"
                }
            ]
        }

        result = self.generator.generate(param_data)

        # Check integer type
        self.assertIn("constexpr int wheel_count", result)
        self.assertIn("= 4", result)

    def test_generate_string_parameter(self):
        """Test generating C++ code for a string parameter."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "vehicle",
            "parameters": [
                {
                    "name": "vehicle_name",
                    "type": "string",
                    "value": "TestVehicle",
                    "description": "Vehicle identifier"
                }
            ]
        }

        result = self.generator.generate(param_data)

        # Check string type
        self.assertIn("constexpr const char* vehicle_name", result)
        self.assertIn('"TestVehicle"', result)

    def test_generate_boolean_parameter(self):
        """Test generating C++ code for a boolean parameter."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "config",
            "parameters": [
                {
                    "name": "debug_mode",
                    "type": "boolean",
                    "value": True,
                    "description": "Enable debug output"
                }
            ]
        }

        result = self.generator.generate(param_data)

        # Check boolean type
        self.assertIn("constexpr bool debug_mode", result)
        self.assertIn("true", result)

    def test_generate_table_parameter(self):
        """Test generating C++ code for a table parameter."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "vehicle",
            "parameters": [
                {
                    "name": "braking_table",
                    "type": "table",
                    "description": "Braking distances by velocity",
                    "columns": [
                        {"name": "velocity", "type": "float", "unit": "m/s"},
                        {"name": "friction", "type": "float", "unit": "dimensionless"},
                        {"name": "distance", "type": "float", "unit": "m"}
                    ],
                    "rows": [
                        [10.0, 0.7, 7.1],
                        [20.0, 0.7, 28.6],
                        [30.0, 0.3, 150.0]
                    ]
                }
            ]
        }

        result = self.generator.generate(param_data)

        # Check struct definition
        self.assertIn("struct BrakingTableRow", result)
        self.assertIn("double velocity", result)
        self.assertIn("double friction", result)
        self.assertIn("double distance", result)

        # Check array declaration
        self.assertIn("constexpr BrakingTableRow braking_table[]", result)

        # Check data values
        self.assertIn("10.0", result)
        self.assertIn("0.7", result)
        self.assertIn("7.1", result)
        self.assertIn("28.6", result)

        # Check array size constant
        self.assertIn("constexpr size_t braking_table_size", result)
        self.assertIn("= 3", result)

    def test_generate_multiple_parameters(self):
        """Test generating C++ code with multiple parameters."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test",
            "parameters": [
                {
                    "name": "param1",
                    "type": "float",
                    "value": 1.0,
                    "description": "First parameter"
                },
                {
                    "name": "param2",
                    "type": "integer",
                    "value": 42,
                    "description": "Second parameter"
                }
            ]
        }

        result = self.generator.generate(param_data)

        # Check both parameters are present
        self.assertIn("param1", result)
        self.assertIn("param2", result)
        self.assertIn("1.0", result)
        self.assertIn("42", result)

    def test_header_guard_generation(self):
        """Test that header guards are unique based on namespace."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "vehicle.dynamics",
            "parameters": []
        }

        result = self.generator.generate(param_data)

        # Header guard should be based on namespace
        self.assertIn("VEHICLE_DYNAMICS_PARAMS_H", result)

    def test_nested_namespace_generation(self):
        """Test that nested namespaces are generated correctly."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "vehicle.dynamics.braking",
            "parameters": [
                {
                    "name": "test_param",
                    "type": "float",
                    "value": 1.0,
                    "description": "Test"
                }
            ]
        }

        result = self.generator.generate(param_data)

        # Check nested namespace structure
        self.assertIn("namespace vehicle", result)
        self.assertIn("namespace dynamics", result)
        self.assertIn("namespace braking", result)

        # Check closing braces with comments
        self.assertIn("} // namespace braking", result)
        self.assertIn("} // namespace dynamics", result)
        self.assertIn("} // namespace vehicle", result)

    def test_special_characters_in_names(self):
        """Test that parameter names are valid C++ identifiers."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test",
            "parameters": [
                {
                    "name": "max_velocity_m_s",
                    "type": "float",
                    "value": 55.0,
                    "description": "Maximum velocity in m/s"
                }
            ]
        }

        result = self.generator.generate(param_data)

        # Underscores should be preserved
        self.assertIn("max_velocity_m_s", result)

    def test_table_with_mixed_types(self):
        """Test generating table with mixed column types."""
        param_data = {
            "schema_version": "1.0",
            "namespace": "test",
            "parameters": [
                {
                    "name": "mixed_table",
                    "type": "table",
                    "description": "Table with mixed types",
                    "columns": [
                        {"name": "id", "type": "integer"},
                        {"name": "name", "type": "string"},
                        {"name": "value", "type": "float"},
                        {"name": "enabled", "type": "boolean"}
                    ],
                    "rows": [
                        [1, "first", 1.5, True],
                        [2, "second", 2.5, False]
                    ]
                }
            ]
        }

        result = self.generator.generate(param_data)

        # Check struct with mixed types
        self.assertIn("int id", result)
        self.assertIn("const char* name", result)
        self.assertIn("double value", result)
        self.assertIn("bool enabled", result)

        # Check values
        self.assertIn('"first"', result)
        self.assertIn('"second"', result)
        self.assertIn("true", result)
        self.assertIn("false", result)


if __name__ == "__main__":
    unittest.main()
