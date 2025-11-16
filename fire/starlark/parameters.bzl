"""Bazel rules for parameter management.

Parameters can be defined inline in BUILD files or loaded from separate .bzl files.
Validation happens at load time, and code is generated at build time for multiple languages.
"""

load("@rules_cc//cc:defs.bzl", "cc_library")
load("@rules_go//go:def.bzl", "go_library")
load("@rules_python//python:defs.bzl", "py_library")
load("//fire/starlark:java_generator.bzl", "java_generator")
load("//fire/starlark:validator.bzl", "validator")

def _derive_namespace_from_package():
    """Derive namespace from Bazel package path.

    Converts package path to namespace format:
    - "vehicle/dynamics" -> "vehicle.dynamics"
    - "" (root) -> "root"
    - "foo/bar/baz" -> "foo.bar.baz"

    Returns:
        Namespace string with dots
    """
    pkg = native.package_name()
    if not pkg:
        return "root"
    return pkg.replace("/", ".")

def _get_java_namespace(namespace, package_prefix = None):
    """Convert namespace to Java format.

    Args:
        namespace: Dot-separated namespace (e.g., "vehicle.dynamics")
        package_prefix: Optional prefix (e.g., "com.example")

    Returns:
        Java package format (e.g., "com.example.vehicle.dynamics")
    """
    if package_prefix:
        return package_prefix + "." + namespace
    return namespace

def _get_source_label(name):
    """Get the source Bazel label for traceability.

    Args:
        name: Target name

    Returns:
        Bazel label string (e.g., "//vehicle/dynamics:vehicle_params")
    """
    pkg = native.package_name()
    if pkg:
        return "//{pkg}:{name}".format(pkg = pkg, name = name)
    return "//:{name}".format(name = name)

def parameter_library(
        name,
        schema_version = "1.0",
        namespace = None,
        parameters = []):
    """Define and validate a parameter library, creating a JSON data file.

    This macro validates parameters at load time and creates a JSON file
    containing the parameter data. Language-specific libraries consume
    this target to generate code.

    Args:
        name: Name of the library (creates a .json file)
        schema_version: Schema version (default "1.0")
        namespace: Namespace for parameters (optional, derived from package path if not provided)
        parameters: List of parameter dictionaries

    Example:
        # Define parameters in a .bzl file
        VEHICLE_PARAMS = [
            {
                "name": "max_velocity",
                "type": "float",
                "unit": "m/s",
                "value": 55.0,
                "description": "Maximum velocity",
            },
        ]

        # Create parameter library (generates JSON)
        parameter_library(
            name = "vehicle_params",
            parameters = VEHICLE_PARAMS,
        )

        # Generate code for different languages (consume the JSON)
        cc_parameter_library(
            name = "vehicle_params_cc",
            parameter_library = ":vehicle_params",
        )
    """

    # Derive namespace from package path if not provided
    if not namespace:
        namespace = _derive_namespace_from_package()

    # Get source label for traceability
    source_label = _get_source_label(name)

    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
        "source_label": source_label,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Create a genrule that uses Python to output JSON
    # We pass the parameter data as a Python literal and use json.dumps
    param_data_repr = str(param_data)

    native.genrule(
        name = name,
        outs = [name + ".json"],
        cmd = """python3 -c 'import json; print(json.dumps({}))' > $@""".format(param_data_repr),
        visibility = ["//visibility:public"],
    )

def cc_parameter_library(
        name,
        parameter_library,
        base_name = None,
        **kwargs):
    """Generate C++ header and create cc_library from parameter_library.

    Args:
        name: Name of the cc_library
        parameter_library: Label of the parameter_library target (the .json file)
        base_name: Base name for output file (optional, defaults to name with _cc suffix removed)
        **kwargs: Additional arguments for cc_library

    Example:
        parameter_library(
            name = "vehicle_params",
            parameters = VEHICLE_PARAMS,
        )

        cc_parameter_library(
            name = "vehicle_params_cc",
            parameter_library = ":vehicle_params",
        )
        # Generates: vehicle_params.h
        # Include as: #include "examples/vehicle_params.h"

    Note:
        Headers should be included using repository-relative paths.
        For example, if the header is in package "examples", use:
            #include "examples/header_name.h"
    """

    # Derive base_name if not provided
    if not base_name:
        # Strip common suffixes
        base_name = name.removesuffix("_cc").removesuffix("_cpp")

    # Create a generated header file using the Python script
    header_target = name + "_header"
    native.genrule(
        name = header_target,
        srcs = [parameter_library],
        outs = [base_name + ".h"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) $< cpp $@",
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = ["//visibility:public"],
    )

    # Wrap in cc_library
    cc_library(
        name = name,
        hdrs = [":" + header_target],
        **kwargs
    )

def python_parameter_library(
        name,
        parameter_library,
        base_name = None,
        **kwargs):
    """Generate Python module and create py_library from parameter_library.

    Args:
        name: Name of the py_library
        parameter_library: Label of the parameter_library target (the .json file)
        base_name: Base name for output file (optional, defaults to name with _py suffix removed)
        **kwargs: Additional arguments for py_library

    Example:
        parameter_library(
            name = "vehicle_params",
            parameters = VEHICLE_PARAMS,
        )

        python_parameter_library(
            name = "vehicle_params_py",
            parameter_library = ":vehicle_params",
        )
        # Generates: vehicle_params.py
        # Import as: from examples.vehicle_params import ...
    """

    # Derive base_name if not provided
    if not base_name:
        # Strip common suffixes
        base_name = name.removesuffix("_py").removesuffix("_python")

    # Create a generated Python file using the Python script
    py_file_target = name + "_file"
    native.genrule(
        name = py_file_target,
        srcs = [parameter_library],
        outs = [base_name + ".py"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) $< python $@",
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = ["//visibility:public"],
    )

    # Wrap in py_library
    py_library(
        name = name,
        srcs = [":" + py_file_target],
        imports = [".."],
        **kwargs
    )

def java_parameter_library(
        name,
        parameters = None,
        parameter_library = None,
        namespace = None,
        package_prefix = None,
        class_name = "Parameters",
        schema_version = "1.0"):
    """Generate Java class with parameters.

    NOTE: Java generation still uses the legacy Starlark-based generator.
    The parameter_library attribute is not yet supported.

    Args:
        name: Name of the generated class file
        parameters: List of parameter dictionaries (legacy, still required)
        parameter_library: DEPRECATED - not yet implemented for Java
        namespace: Java package namespace (optional, derived from package path if not provided)
        package_prefix: Optional package prefix (e.g., "com.example")
        class_name: Name of the generated class (default "Parameters")
        schema_version: Schema version (default "1.0")

    Example:
        # Namespace auto-derived from package path
        java_parameter_library(
            name = "VehicleParams",
            class_name = "VehicleParams",
            package_prefix = "com.example",  # Optional
            parameters = VEHICLE_PARAMS,
        )

        # Or explicitly specify namespace
        java_parameter_library(
            name = "VehicleParams",
            namespace = "com.example.vehicle.dynamics",
            class_name = "VehicleParams",
            parameters = VEHICLE_PARAMS,
        )
    """

    if parameter_library:
        fail("java_parameter_library does not yet support parameter_library attribute. " +
             "Java generation still uses the legacy Starlark generator. " +
             "Please pass parameters directly for now.")

    if not parameters:
        fail("java_parameter_library requires 'parameters' attribute")

    # Derive namespace from package path if not provided
    if not namespace:
        base_namespace = _derive_namespace_from_package()
        namespace = _get_java_namespace(base_namespace, package_prefix)

    # Get source label for traceability
    source_label = _get_source_label(name)

    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
        "source_label": source_label,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate Java code using legacy Starlark generator
    java_code = java_generator.generate(namespace, parameters, class_name, source_label)

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
        parameter_library,
        base_name = None,
        importpath = None,
        **kwargs):
    """Generate Go package and create go_library from parameter_library.

    Args:
        name: Name of the go_library
        parameter_library: Label of the parameter_library target (the .json file)
        base_name: Base name for output file (optional, defaults to name with _go suffix removed)
        importpath: Go import path (optional, defaults to package path + "/" + base_name)
        **kwargs: Additional arguments for go_library

    Example:
        parameter_library(
            name = "vehicle_params",
            parameters = VEHICLE_PARAMS,
        )

        go_parameter_library(
            name = "vehicle_params_go",
            parameter_library = ":vehicle_params",
        )
        # Generates: vehicle_params.go
        # Import as: import vehicle_params "examples/vehicle_params"
    """

    # Derive base_name if not provided
    if not base_name:
        # Strip common suffixes
        base_name = name.removesuffix("_go").removesuffix("_golang")

    # Derive importpath if not provided
    if not importpath:
        pkg = native.package_name()
        if pkg:
            importpath = pkg + "/" + base_name
        else:
            importpath = base_name

    # Create a generated Go file using the Python script
    go_file_target = name + "_file"
    native.genrule(
        name = go_file_target,
        srcs = [parameter_library],
        outs = [base_name + ".go"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) $< go $@",
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = ["//visibility:public"],
    )

    # Wrap in go_library
    go_library(
        name = name,
        srcs = [":" + go_file_target],
        importpath = importpath,
        **kwargs
    )

def rust_parameter_library(
        name,
        parameter_library,
        base_name = None):
    """Generate Rust module from parameter_library.

    Args:
        name: Name of the Bazel target (use directly in rust_test srcs)
        parameter_library: Label of the parameter_library target (the .json file)
        base_name: Base name for output file (optional, defaults to name with _rs suffix removed)

    Example:
        parameter_library(
            name = "vehicle_params",
            parameters = VEHICLE_PARAMS,
        )

        rust_parameter_library(
            name = "vehicle_params_rs",
            parameter_library = ":vehicle_params",
        )
        # Generates: vehicle_params.rs
        # Include as: #[path = "vehicle_params.rs"] mod vehicle_params;
    """

    # Derive base_name if not provided
    if not base_name:
        # Strip common suffixes
        base_name = name.removesuffix("_rs").removesuffix("_rust")

    # Create a generated Rust file using the Python script
    native.genrule(
        name = name,
        srcs = [parameter_library],
        outs = [base_name + ".rs"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) $< rust $@",
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = ["//visibility:public"],
    )
