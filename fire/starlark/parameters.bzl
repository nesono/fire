"""Bazel rules for parameter management.

Parameters can be defined inline in BUILD files or loaded from separate .bzl files.
Validation happens at load time, and code is generated at build time for multiple languages.
"""

load("@rules_cc//cc:defs.bzl", "cc_library")
load("//fire/starlark:cpp_generator.bzl", "cpp_generator")
load("//fire/starlark:go_generator.bzl", "go_generator")
load("//fire/starlark:java_generator.bzl", "java_generator")
load("//fire/starlark:python_generator.bzl", "python_generator")
load("//fire/starlark:validator.bzl", "validator")

def parameter_library(
        name,
        schema_version = "1.0",
        namespace = None,
        parameters = []):
    """Define a parameter library inline in Starlark.

    Args:
        name: Name of the library
        schema_version: Schema version (default "1.0")
        namespace: C++ namespace for parameters
        parameters: List of parameter dictionaries

    Example:
        parameter_library(
            name = "my_params",
            namespace = "my.namespace",
            parameters = [
                {
                    "name": "max_velocity",
                    "type": "float",
                    "unit": "m/s",
                    "value": 55.0,
                    "description": "Maximum velocity",
                },
            ],
        )
    """
    if not namespace:
        fail("namespace is required")

    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate C++ header
    cpp_code = cpp_generator.generate(param_data)

    # Create a generated header file
    native.genrule(
        name = name,
        outs = [name + ".h"],
        cmd = """cat > $@ <<'EOF'
{}
EOF""".format(cpp_code),
        visibility = ["//visibility:public"],
    )

def cc_parameter_library(name, parameter_library, **kwargs):
    """Create a cc_library from a parameter_library.

    Args:
        name: Name of the cc_library
        parameter_library: Label of the parameter_library (the generated .h file)
        **kwargs: Additional arguments for cc_library
    """
    cc_library(
        name = name,
        hdrs = [parameter_library],
        includes = ["."],
        **kwargs
    )

def python_parameter_library(
        name,
        namespace,
        parameters,
        schema_version = "1.0"):
    """Generate Python module with parameters.

    Args:
        name: Name of the generated module (will create name.py)
        namespace: Python module namespace
        parameters: List of parameter dictionaries
        schema_version: Schema version (default "1.0")

    Example:
        python_parameter_library(
            name = "vehicle_params",
            namespace = "vehicle.dynamics",
            parameters = VEHICLE_PARAMS,
        )
    """
    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate Python code
    python_code = python_generator.generate(namespace, parameters)

    # Create a generated Python file
    native.genrule(
        name = name,
        outs = [name + ".py"],
        cmd = """cat > $@ <<'EOF'
{}
EOF""".format(python_code),
        visibility = ["//visibility:public"],
    )

def java_parameter_library(
        name,
        namespace,
        parameters,
        class_name = "Parameters",
        schema_version = "1.0"):
    """Generate Java class with parameters.

    Args:
        name: Name of the generated class file
        namespace: Java package namespace (e.g., "com.example.vehicle")
        parameters: List of parameter dictionaries
        class_name: Name of the generated class (default "Parameters")
        schema_version: Schema version (default "1.0")

    Example:
        java_parameter_library(
            name = "VehicleParams",
            namespace = "com.example.vehicle.dynamics",
            class_name = "VehicleParams",
            parameters = VEHICLE_PARAMS,
        )
    """
    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate Java code
    java_code = java_generator.generate(namespace, parameters, class_name)

    # Create a generated Java file
    native.genrule(
        name = name,
        outs = [class_name + ".java"],
        cmd = """cat > $@ <<'EOF'
{}
EOF""".format(java_code),
        visibility = ["//visibility:public"],
    )

def go_parameter_library(
        name,
        namespace,
        parameters,
        package_name = "parameters",
        schema_version = "1.0"):
    """Generate Go package with parameters.

    Args:
        name: Name of the generated Go file (will create name.go)
        namespace: Go package path (e.g., "vehicle/dynamics")
        parameters: List of parameter dictionaries
        package_name: Go package name (default "parameters")
        schema_version: Schema version (default "1.0")

    Example:
        go_parameter_library(
            name = "vehicle_params",
            namespace = "vehicle/dynamics",
            package_name = "dynamics",
            parameters = VEHICLE_PARAMS,
        )
    """
    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate Go code
    go_code = go_generator.generate(namespace, parameters, package_name)

    # Create a generated Go file
    native.genrule(
        name = name,
        outs = [name + ".go"],
        cmd = """cat > $@ <<'EOF'
{}
EOF""".format(go_code),
        visibility = ["//visibility:public"],
    )
