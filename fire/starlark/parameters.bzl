"""Bazel rules for parameter management.

Parameters can be defined inline in BUILD files or loaded from separate .bzl files.
Validation happens at load time, and code is generated at build time for multiple languages.
"""

load("@rules_cc//cc:defs.bzl", "cc_library")
load("@rules_go//go:def.bzl", "go_library")
load("@rules_java//java:defs.bzl", "java_library")
load("@rules_python//python:defs.bzl", "py_library")
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
        namespace = None,
        **kwargs):
    """Generate C++ header and create cc_library from parameter_library.

    Args:
        name: Name of the cc_library
        parameter_library: Label of the parameter_library target (the .json file)
        base_name: Base name for output file (optional, defaults to name with _cc suffix removed)
        namespace: Optional C++ namespace (use :: for nested namespaces, e.g., "outer::inner")
        **kwargs: Additional arguments for cc_library

    Example:
        parameter_library(
            name = "vehicle_params",
            parameters = VEHICLE_PARAMS,
        )

        cc_parameter_library(
            name = "vehicle_params_cc",
            parameter_library = ":vehicle_params",
            namespace = "my_project::params",  # Optional
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

    # Build command with optional namespace
    if namespace == None:
        # No namespace parameter provided - use default from JSON
        cmd = "$(location @fire//fire/starlark:generate_code_script) $< cpp $@"
    else:
        # Namespace explicitly provided (could be empty string for no namespace)
        cmd = "$(location @fire//fire/starlark:generate_code_script) $< cpp $@ --namespace='{}'".format(namespace)

    # Create a generated header file using the Python script
    header_target = name + "_header"
    native.genrule(
        name = header_target,
        srcs = [parameter_library],
        outs = [base_name + ".h"],
        cmd = cmd,
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
        parameter_library,
        class_name = None,
        package_prefix = None):
    """Generate Java class from parameter_library.

    Args:
        name: Name of the Bazel target
        parameter_library: Label of the parameter_library target (the .json file)
        class_name: Name of the generated class (optional, derived from target name if not provided)
        package_prefix: Optional package prefix (e.g., "com.example")

    Example:
        parameter_library(
            name = "vehicle_params",
            parameters = VEHICLE_PARAMS,
        )

        java_parameter_library(
            name = "vehicle_params_java",
            parameter_library = ":vehicle_params",
            class_name = "VehicleParams",  # Optional
            package_prefix = "com.example",  # Optional
        )
        # Generates: VehicleParams.java (or derived from target name)
    """

    # Derive class_name if not provided
    if not class_name:
        # Strip common suffixes and convert to PascalCase
        base_name = name.removesuffix("_java")
        parts = base_name.split("_")
        class_name = "".join([word.capitalize() for word in parts])

    # Create a generated Java file using the Python script
    # Note: The namespace with package_prefix will be handled in parameter_library
    # We need to create a custom JSON that includes the package_prefix
    # For now, we'll use a wrapper script or pass it as an environment variable

    # Actually, we need to handle package_prefix differently since parameter_library
    # already set the namespace. Let me use a different approach:
    # Generate with script, but we need to modify the namespace in the JSON

    # For simplicity, let's generate using the script and handle package_prefix
    # by modifying the parameter_library's namespace at this level

    java_file_target = name + "_file"

    if package_prefix:
        # Need to create a modified JSON with package prefix
        # Use a genrule to modify the JSON
        modified_json = name + "_json"
        native.genrule(
            name = modified_json,
            srcs = [parameter_library],
            outs = [name + "_modified.json"],
            cmd = """python3 -c '
import json, sys
with open("$<", "r") as f:
    data = json.load(f)
base_ns = data["namespace"]
data["namespace"] = "{}.{{}}".format(base_ns)
with open("$@", "w") as f:
    json.dump(data, f)
' """.format(package_prefix),
        )
        json_input = ":" + modified_json
    else:
        json_input = parameter_library

    native.genrule(
        name = java_file_target,
        srcs = [json_input],
        outs = [class_name + ".java"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) $< java $@",
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = ["//visibility:public"],
    )

    # Wrap in java_library
    java_library(
        name = name,
        srcs = [":" + java_file_target],
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
