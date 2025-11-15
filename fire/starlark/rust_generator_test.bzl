"""Unit tests for Rust code generator."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":rust_generator.bzl", "rust_generator")

def _test_simple_float_parameter(ctx):
    """Test Rust generation for simple float parameter."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "test",
        [
            {
                "description": "Maximum velocity",
                "name": "max_velocity",
                "type": "float",
                "unit": "m/s",
                "value": 55.0,
            },
        ],
    )

    asserts.true(env, "// This file is auto-generated" in result, "Should have auto-gen comment")
    asserts.true(env, "/// Maximum velocity" in result, "Should have doc comment")
    asserts.true(env, "/// Unit: m/s" in result, "Should have unit comment")
    asserts.true(env, "pub const MAX_VELOCITY: f64 = 55.0;" in result, "Should have float declaration with SCREAMING_SNAKE_CASE")

    return unittest.end(env)

def _test_simple_integer_parameter(ctx):
    """Test Rust generation for simple integer parameter."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "test",
        [
            {
                "description": "Number of wheels",
                "name": "wheel_count",
                "type": "integer",
                "value": 4,
            },
        ],
    )

    asserts.true(env, "pub const WHEEL_COUNT: i32 = 4;" in result, "Should have integer declaration with SCREAMING_SNAKE_CASE")

    return unittest.end(env)

def _test_simple_string_parameter(ctx):
    """Test Rust generation for simple string parameter."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "test",
        [
            {
                "description": "Vehicle model",
                "name": "vehicle_model",
                "type": "string",
                "value": "Model X",
            },
        ],
    )

    asserts.true(env, 'pub const VEHICLE_MODEL: &\'static str = "Model X";' in result, "Should have string declaration with SCREAMING_SNAKE_CASE")

    return unittest.end(env)

def _test_simple_boolean_parameter(ctx):
    """Test Rust generation for simple boolean parameter."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "test",
        [
            {
                "description": "Enable turbo mode",
                "name": "turbo_enabled",
                "type": "boolean",
                "value": True,
            },
        ],
    )

    asserts.true(env, "pub const TURBO_ENABLED: bool = true;" in result, "Should have boolean declaration")

    result_false = rust_generator.generate(
        "test",
        [
            {
                "description": "Debug mode",
                "name": "debug_mode",
                "type": "boolean",
                "value": False,
            },
        ],
    )

    asserts.true(env, "pub const DEBUG_MODE: bool = false;" in result_false, "Should have false boolean")

    return unittest.end(env)

def _test_table_parameter(ctx):
    """Test Rust generation for table parameter."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "test",
        [
            {
                "columns": [
                    {"name": "velocity", "type": "float", "unit": "m/s"},
                    {"name": "friction", "type": "float", "unit": "dimensionless"},
                    {"name": "distance", "type": "float", "unit": "m"},
                ],
                "description": "Braking distance table",
                "name": "braking_table",
                "rows": [
                    [10.0, 0.7, 7.1],
                    [20.0, 0.7, 28.6],
                ],
                "type": "table",
            },
        ],
    )

    asserts.true(env, "/// Braking distance table" in result, "Should have table description")
    asserts.true(env, "#[derive(Debug, Clone, Copy)]" in result, "Should have derives")
    asserts.true(env, "pub struct BrakingTableRow {" in result, "Should have struct definition")
    asserts.true(env, "pub velocity: f64," in result, "Should have velocity field")
    asserts.true(env, "pub friction: f64," in result, "Should have friction field")
    asserts.true(env, "pub distance: f64," in result, "Should have distance field")
    asserts.true(env, "pub const BRAKING_TABLE: &[BrakingTableRow] = &[" in result, "Should have table constant")
    asserts.true(env, "BrakingTableRow { velocity: 10.0, friction: 0.7, distance: 7.1 }," in result, "Should have first row")
    asserts.true(env, "BrakingTableRow { velocity: 20.0, friction: 0.7, distance: 28.6 }," in result, "Should have second row")
    asserts.true(env, "pub const BRAKING_TABLE_SIZE: usize = 2;" in result, "Should have size constant")

    return unittest.end(env)

def _test_string_escaping(ctx):
    """Test Rust string escaping."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "test",
        [
            {
                "description": "Test string with quotes",
                "name": "test_string",
                "type": "string",
                "value": 'She said "Hello"',
            },
        ],
    )

    asserts.true(env, 'pub const TEST_STRING: &\'static str = "She said \\"Hello\\"";' in result, "Should escape quotes")

    return unittest.end(env)

def _test_multiple_parameters(ctx):
    """Test Rust generation with multiple parameters."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "vehicle",
        [
            {
                "description": "Max velocity",
                "name": "max_velocity",
                "type": "float",
                "value": 55.0,
            },
            {
                "description": "Wheel count",
                "name": "wheel_count",
                "type": "integer",
                "value": 4,
            },
        ],
    )

    asserts.true(env, "pub const MAX_VELOCITY: f64 = 55.0;" in result, "Should have first parameter")
    asserts.true(env, "pub const WHEEL_COUNT: i32 = 4;" in result, "Should have second parameter")

    return unittest.end(env)

def _test_source_label_traceability(ctx):
    """Test that source label is included in generated code."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "test",
        [
            {
                "description": "Test param",
                "name": "test_param",
                "type": "float",
                "value": 1.0,
            },
        ],
        source_label = "//examples:vehicle_params",
    )

    asserts.true(env, "// Generated from: //examples:vehicle_params" in result, "Should have source label")

    return unittest.end(env)

def _test_float_formatting(ctx):
    """Test that floats always have decimal point."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "test",
        [
            {
                "description": "Integer-valued float",
                "name": "test_float",
                "type": "float",
                "value": 10,
            },
        ],
    )

    asserts.true(env, "pub const TEST_FLOAT: f64 = 10.0;" in result, "Should add .0 to integer-valued floats")

    return unittest.end(env)

def _test_table_with_strings(ctx):
    """Test table parameter with string columns."""
    env = unittest.begin(ctx)

    result = rust_generator.generate(
        "test",
        [
            {
                "columns": [
                    {"name": "name", "type": "string"},
                    {"name": "value", "type": "integer"},
                ],
                "description": "Config table",
                "name": "config",
                "rows": [
                    ["option1", 10],
                    ["option2", 20],
                ],
                "type": "table",
            },
        ],
    )

    asserts.true(env, "pub name: &'static str," in result, "Should have string field")
    asserts.true(env, "pub value: i32," in result, "Should have integer field")
    asserts.true(env, 'ConfigRow { name: "option1", value: 10 },' in result, "Should have string data")

    return unittest.end(env)

# Test suite
simple_float_parameter_test = unittest.make(_test_simple_float_parameter)
simple_integer_parameter_test = unittest.make(_test_simple_integer_parameter)
simple_string_parameter_test = unittest.make(_test_simple_string_parameter)
simple_boolean_parameter_test = unittest.make(_test_simple_boolean_parameter)
table_parameter_test = unittest.make(_test_table_parameter)
string_escaping_test = unittest.make(_test_string_escaping)
multiple_parameters_test = unittest.make(_test_multiple_parameters)
source_label_traceability_test = unittest.make(_test_source_label_traceability)
float_formatting_test = unittest.make(_test_float_formatting)
table_with_strings_test = unittest.make(_test_table_with_strings)

def rust_generator_test_suite(name):
    """Create test suite for rust_generator."""
    unittest.suite(
        name,
        simple_float_parameter_test,
        simple_integer_parameter_test,
        simple_string_parameter_test,
        simple_boolean_parameter_test,
        table_parameter_test,
        string_escaping_test,
        multiple_parameters_test,
        source_label_traceability_test,
        float_formatting_test,
        table_with_strings_test,
    )
