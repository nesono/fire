"""Unit tests for parameter validator."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":validator.bzl", "validator")

def _test_valid_namespace(ctx):
    """Test valid namespace formats."""
    env = unittest.begin(ctx)

    # Simple namespace
    err = validator.validate({
        "namespace": "vehicle",
        "parameters": [],
        "schema_version": "1.0",
    })
    asserts.equals(env, None, err)

    # Nested namespace
    err = validator.validate({
        "namespace": "vehicle.dynamics.braking",
        "parameters": [],
        "schema_version": "1.0",
    })
    asserts.equals(env, None, err)

    # Namespace with underscores
    err = validator.validate({
        "namespace": "my_vehicle.my_dynamics",
        "parameters": [],
        "schema_version": "1.0",
    })
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_invalid_namespace(ctx):
    """Test invalid namespace formats."""
    env = unittest.begin(ctx)

    # Empty namespace
    err = validator.validate({
        "namespace": "",
        "parameters": [],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Empty namespace should fail")

    # Namespace with spaces
    err = validator.validate({
        "namespace": "my namespace",
        "parameters": [],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Namespace with spaces should fail")

    # Namespace with double dots
    err = validator.validate({
        "namespace": "vehicle..dynamics",
        "parameters": [],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Namespace with double dots should fail")

    # Namespace starting with number
    err = validator.validate({
        "namespace": "123vehicle",
        "parameters": [],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Namespace starting with number should fail")

    return unittest.end(env)

def _test_missing_required_fields(ctx):
    """Test missing required fields."""
    env = unittest.begin(ctx)

    # Missing namespace
    err = validator.validate({
        "parameters": [],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Missing namespace should fail")

    # Missing parameters
    err = validator.validate({
        "namespace": "test",
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Missing parameters should fail")

    # Missing schema_version
    err = validator.validate({
        "namespace": "test",
        "parameters": [],
    })
    asserts.true(env, err != None, "Missing schema_version should fail")

    return unittest.end(env)

def _test_valid_simple_parameters(ctx):
    """Test valid simple parameters."""
    env = unittest.begin(ctx)

    # Float parameter
    err = validator.validate({
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
    asserts.equals(env, None, err)

    # Integer parameter
    err = validator.validate({
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
    asserts.equals(env, None, err)

    # String parameter
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Vehicle model name",
                "name": "vehicle_model",
                "type": "string",
                "value": "Model X",
            },
        ],
        "schema_version": "1.0",
    })
    asserts.equals(env, None, err)

    # Boolean parameter
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Has ABS system",
                "name": "has_abs",
                "type": "boolean",
                "value": True,
            },
        ],
        "schema_version": "1.0",
    })
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_invalid_parameter_types(ctx):
    """Test invalid parameter types."""
    env = unittest.begin(ctx)

    # Invalid type name
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Test",
                "name": "value",
                "type": "double",
                "value": 1.0,
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Invalid type should fail")

    # Float value for integer type
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Test",
                "name": "count",
                "type": "integer",
                "value": 1.5,
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Float value for integer type should fail")

    # String value for float type
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Test",
                "name": "value",
                "type": "float",
                "value": "not a number",
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "String value for float type should fail")

    return unittest.end(env)

def _test_missing_parameter_fields(ctx):
    """Test missing required parameter fields."""
    env = unittest.begin(ctx)

    # Missing name
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Test",
                "type": "float",
                "value": 1.0,
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Missing name should fail")

    # Missing type
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Test",
                "name": "value",
                "value": 1.0,
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Missing type should fail")

    # Missing description
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "name": "value",
                "type": "float",
                "value": 1.0,
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Missing description should fail")

    # Missing value for non-table type
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Test",
                "name": "value",
                "type": "float",
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Missing value should fail")

    return unittest.end(env)

def _test_valid_table_parameters(ctx):
    """Test valid table parameters."""
    env = unittest.begin(ctx)

    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "columns": [
                    {"name": "gear", "type": "integer"},
                    {"name": "ratio", "type": "float"},
                ],
                "description": "Gear ratios",
                "name": "gear_ratios",
                "rows": [
                    [1, 3.5],
                    [2, 2.1],
                    [3, 1.4],
                ],
                "type": "table",
            },
        ],
        "schema_version": "1.0",
    })
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_invalid_table_parameters(ctx):
    """Test invalid table parameters."""
    env = unittest.begin(ctx)

    # Missing columns
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "Test",
                "name": "table",
                "rows": [[1, 2]],
                "type": "table",
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Missing columns should fail")

    # Missing rows
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "columns": [{"name": "col", "type": "integer"}],
                "description": "Test",
                "name": "table",
                "type": "table",
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Missing rows should fail")

    # Row with wrong column count
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "columns": [
                    {"name": "col1", "type": "integer"},
                    {"name": "col2", "type": "float"},
                ],
                "description": "Test",
                "name": "table",
                "rows": [
                    [1, 2.0],
                    [3],  # Wrong column count
                ],
                "type": "table",
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Row with wrong column count should fail")

    # Nested table
    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "columns": [
                    {"name": "col", "type": "table"},
                ],
                "description": "Test",
                "name": "table",
                "rows": [],
                "type": "table",
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Nested table should fail")

    return unittest.end(env)

def _test_duplicate_parameter_names(ctx):
    """Test duplicate parameter names."""
    env = unittest.begin(ctx)

    err = validator.validate({
        "namespace": "test",
        "parameters": [
            {
                "description": "First",
                "name": "value",
                "type": "float",
                "value": 1.0,
            },
            {
                "description": "Duplicate",
                "name": "value",
                "type": "float",
                "value": 2.0,
            },
        ],
        "schema_version": "1.0",
    })
    asserts.true(env, err != None, "Duplicate parameter names should fail")

    return unittest.end(env)

# Test suite
valid_namespace_test = unittest.make(_test_valid_namespace)
invalid_namespace_test = unittest.make(_test_invalid_namespace)
missing_required_fields_test = unittest.make(_test_missing_required_fields)
valid_simple_parameters_test = unittest.make(_test_valid_simple_parameters)
invalid_parameter_types_test = unittest.make(_test_invalid_parameter_types)
missing_parameter_fields_test = unittest.make(_test_missing_parameter_fields)
valid_table_parameters_test = unittest.make(_test_valid_table_parameters)
invalid_table_parameters_test = unittest.make(_test_invalid_table_parameters)
duplicate_parameter_names_test = unittest.make(_test_duplicate_parameter_names)

def validator_test_suite(name):
    """Create test suite for validator."""
    unittest.suite(
        name,
        valid_namespace_test,
        invalid_namespace_test,
        missing_required_fields_test,
        valid_simple_parameters_test,
        invalid_parameter_types_test,
        missing_parameter_fields_test,
        valid_table_parameters_test,
        invalid_table_parameters_test,
        duplicate_parameter_names_test,
    )
