"""Unit tests for C++ code generator."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":cpp_generator.bzl", "cpp_generator")

def _test_simple_float_parameter(ctx):
    """Test C++ generation for simple float parameter."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Maximum velocity",
                "name": "max_velocity",
                "type": "float",
                "unit": "m/s",
                "value": 55.0,
            },
        ],
        "schema_version": "1.0",
    })

    asserts.true(env, "#ifndef TEST_PARAMS_H" in result, "Should have header guard")
    asserts.true(env, "namespace test {" in result, "Should have namespace")
    asserts.true(env, "/// Maximum velocity - Unit: m/s" in result, "Should have comment")
    asserts.true(env, "constexpr double max_velocity = 55.0;" in result, "Should have float declaration")

    return unittest.end(env)

def _test_simple_integer_parameter(ctx):
    """Test C++ generation for simple integer parameter."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Number of wheels",
                "name": "wheel_count",
                "type": "integer",
                "value": 4,
            },
        ],
        "schema_version": "1.0",
    })

    asserts.true(env, "constexpr int wheel_count = 4;" in result, "Should have integer declaration")

    return unittest.end(env)

def _test_simple_string_parameter(ctx):
    """Test C++ generation for simple string parameter."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Vehicle model",
                "name": "vehicle_model",
                "type": "string",
                "value": "Model X",
            },
        ],
        "schema_version": "1.0",
    })

    asserts.true(env, 'constexpr const char* vehicle_model = "Model X";' in result, "Should have string declaration")

    return unittest.end(env)

def _test_simple_boolean_parameter(ctx):
    """Test C++ generation for simple boolean parameter."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Has ABS",
                "name": "has_abs",
                "type": "boolean",
                "value": True,
            },
        ],
        "schema_version": "1.0",
    })

    asserts.true(env, "constexpr bool has_abs = true;" in result, "Should have boolean declaration")

    return unittest.end(env)

def _test_nested_namespace(ctx):
    """Test C++ generation for nested namespace."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "vehicle.dynamics.braking",
        "parameters": [
            {
                "description": "Test",
                "name": "value",
                "type": "float",
                "value": 1.0,
            },
        ],
        "schema_version": "1.0",
    })

    asserts.true(env, "namespace vehicle {" in result, "Should have first namespace")
    asserts.true(env, "namespace dynamics {" in result, "Should have second namespace")
    asserts.true(env, "namespace braking {" in result, "Should have third namespace")
    asserts.true(env, "} // namespace braking" in result, "Should close third namespace")
    asserts.true(env, "} // namespace dynamics" in result, "Should close second namespace")
    asserts.true(env, "} // namespace vehicle" in result, "Should close first namespace")

    return unittest.end(env)

def _test_table_parameter(ctx):
    """Test C++ generation for table parameter."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "test",
        "parameters": [
            {
                "columns": [
                    {"name": "gear", "type": "integer"},
                    {"name": "ratio", "type": "float"},
                    {"name": "max_speed", "type": "float", "unit": "km/h"},
                ],
                "description": "Gear ratios",
                "name": "gear_ratios",
                "rows": [
                    [1, 3.5, 40.0],
                    [2, 2.1, 70.0],
                ],
                "type": "table",
            },
        ],
        "schema_version": "1.0",
    })

    # Check struct definition
    asserts.true(env, "struct GearRatiosRow {" in result, "Should have struct")
    asserts.true(env, "int gear;" in result, "Should have gear field")
    asserts.true(env, "double ratio;" in result, "Should have ratio field")
    asserts.true(env, "/// Unit: km/h" in result, "Should have unit comment")
    asserts.true(env, "double max_speed;" in result, "Should have max_speed field")

    # Check array declaration
    asserts.true(env, "/// Gear ratios" in result, "Should have description comment")
    asserts.true(env, "constexpr GearRatiosRow gear_ratios[] = {" in result, "Should have array declaration")
    asserts.true(env, "{1, 3.5, 40.0}," in result, "Should have first row")
    asserts.true(env, "{2, 2.1, 70.0}," in result, "Should have second row")

    # Check size constant
    asserts.true(env, "constexpr size_t gear_ratios_size = 2;" in result, "Should have size constant")

    return unittest.end(env)

def _test_string_escaping(ctx):
    """Test C++ generation escapes strings properly."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Test",
                "name": "message",
                "type": "string",
                "value": 'He said "hello"',
            },
        ],
        "schema_version": "1.0",
    })

    asserts.true(env, 'constexpr const char* message = "He said \\"hello\\""' in result, "Should escape quotes")

    return unittest.end(env)

def _test_header_guard_format(ctx):
    """Test header guard naming."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "vehicle.dynamics",
        "parameters": [],
        "schema_version": "1.0",
    })

    asserts.true(env, "#ifndef VEHICLE_DYNAMICS_PARAMS_H" in result, "Should have correct header guard")
    asserts.true(env, "#define VEHICLE_DYNAMICS_PARAMS_H" in result, "Should define header guard")
    asserts.true(env, "#endif // VEHICLE_DYNAMICS_PARAMS_H" in result, "Should close header guard")

    return unittest.end(env)

def _test_includes_size_t(ctx):
    """Test that cstddef is included for size_t."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "test",
        "parameters": [],
        "schema_version": "1.0",
    })

    asserts.true(env, "#include <cstddef>" in result, "Should include cstddef")

    return unittest.end(env)

def _test_multiple_parameters(ctx):
    """Test C++ generation for multiple parameters."""
    env = unittest.begin(ctx)

    result = cpp_generator.generate({
        "namespace": "test",
        "parameters": [
            {
                "description": "First value",
                "name": "value1",
                "type": "float",
                "value": 1.0,
            },
            {
                "description": "Second value",
                "name": "value2",
                "type": "integer",
                "value": 2,
            },
            {
                "description": "Third value",
                "name": "value3",
                "type": "boolean",
                "value": False,
            },
        ],
        "schema_version": "1.0",
    })

    asserts.true(env, "constexpr double value1 = 1.0;" in result, "Should have first parameter")
    asserts.true(env, "constexpr int value2 = 2;" in result, "Should have second parameter")
    asserts.true(env, "constexpr bool value3 = false;" in result, "Should have third parameter")

    return unittest.end(env)

# Test suite
simple_float_parameter_test = unittest.make(_test_simple_float_parameter)
simple_integer_parameter_test = unittest.make(_test_simple_integer_parameter)
simple_string_parameter_test = unittest.make(_test_simple_string_parameter)
simple_boolean_parameter_test = unittest.make(_test_simple_boolean_parameter)
nested_namespace_test = unittest.make(_test_nested_namespace)
table_parameter_test = unittest.make(_test_table_parameter)
string_escaping_test = unittest.make(_test_string_escaping)
header_guard_format_test = unittest.make(_test_header_guard_format)
includes_size_t_test = unittest.make(_test_includes_size_t)
multiple_parameters_test = unittest.make(_test_multiple_parameters)

def cpp_generator_test_suite(name):
    """Create test suite for cpp_generator."""
    unittest.suite(
        name,
        simple_float_parameter_test,
        simple_integer_parameter_test,
        simple_string_parameter_test,
        simple_boolean_parameter_test,
        nested_namespace_test,
        table_parameter_test,
        string_escaping_test,
        header_guard_format_test,
        includes_size_t_test,
        multiple_parameters_test,
    )
