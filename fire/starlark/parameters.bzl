"""Bazel rules for parameter management.

Parameters are defined in YAML files and validated at build time using JSON schema.
Code is generated for multiple languages from the validated YAML.
"""

load("@rules_cc//cc:defs.bzl", "cc_library")
load("@rules_go//go:def.bzl", "go_library")
load("@rules_java//java:defs.bzl", "java_library")
load("@rules_python//python:defs.bzl", "py_library")

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

def parameter_library(
        name,
        src,
        namespace = None,
        visibility = None):
    """Define and validate a parameter library from a YAML file.

    This macro validates the YAML file at build time against a JSON schema
    and makes it available for code generation.

    Args:
        name: Name of the library
        src: Path to the parameter YAML file (e.g., "vehicle_params.yaml")
        namespace: Namespace for parameters (optional, derived from package path if not provided)
        visibility: Visibility of the target

    Example:
        # Define parameters in a YAML file (vehicle_params.yaml):
        # parameters:
        #   max_velocity:
        #     type: float
        #     value: 55.0
        #     unit: m/s
        #     description: Maximum velocity

        # Create parameter library
        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
        )

        # Generate code for different languages
        cc_parameter_library(
            name = "vehicle_params_cc",
            parameter_library = ":vehicle_params",
        )
    """

    # Derive namespace from package path if not provided
    if not namespace:
        namespace = _derive_namespace_from_package()

    # Create validation target
    validation_name = name + "_validation"
    native.genrule(
        name = validation_name,
        srcs = [src],
        outs = [name + "_validated.yaml"],
        cmd = """
            $(location @fire//fire/starlark:validate_parameters_script) \
                $< \
                --schema=$(location @fire//fire/starlark:parameter_schema.json) && \
            cp $< $@
        """,
        tools = [
            "@fire//fire/starlark:validate_parameters_script",
            "@fire//fire/starlark:parameter_schema.json",
        ],
        visibility = visibility if visibility else ["//visibility:public"],
    )

    # Create a filegroup that exposes both the namespace and the validated YAML
    # We store namespace in a separate file for code generators to consume
    namespace_file = name + "_namespace"
    native.genrule(
        name = namespace_file,
        outs = [name + ".namespace"],
        cmd = "echo '{}' > $@".format(namespace),
        visibility = ["//visibility:private"],
    )

    # Main target is a filegroup containing the validated YAML
    native.filegroup(
        name = name,
        srcs = [":" + validation_name],
        visibility = visibility if visibility else ["//visibility:public"],
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
        parameter_library: Label of the parameter_library target (the YAML file)
        base_name: Base name for output file (optional, defaults to name with _cc suffix removed)
        namespace: Optional C++ namespace (use :: for nested namespaces, e.g., "outer::inner")
        **kwargs: Additional arguments for cc_library

    Example:
        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
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
        base_name = name

    # Get namespace from package if not provided
    if namespace == None:
        namespace = _derive_namespace_from_package()

    # Build command with namespace
    if namespace:
        cmd = "$(location @fire//fire/starlark:generate_code_script) cpp $< $@ --namespace='{}'".format(namespace)
    else:
        cmd = "$(location @fire//fire/starlark:generate_code_script) cpp $< $@"

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
        parameter_library: Label of the parameter_library target (the YAML file)
        base_name: Base name for output file (optional, defaults to name with _py suffix removed)
        **kwargs: Additional arguments for py_library

    Example:
        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
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
        base_name = name

    # Create a generated Python file using the Python script
    py_file_target = name + "_file"
    native.genrule(
        name = py_file_target,
        srcs = [parameter_library],
        outs = [base_name + ".py"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) python $< $@",
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
        parameter_library: Label of the parameter_library target (the YAML file)
        class_name: Name of the generated class (optional, derived from target name if not provided)
        package_prefix: Optional package prefix (e.g., "com.example")

    Example:
        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
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
        base_name = name
        parts = base_name.split("_")
        class_name = "".join([word.capitalize() for word in parts])

    # Determine namespace
    base_namespace = _derive_namespace_from_package()
    if package_prefix:
        namespace = "{}.{}".format(package_prefix, base_namespace)
    else:
        namespace = base_namespace

    java_file_target = name + "_file"

    native.genrule(
        name = java_file_target,
        srcs = [parameter_library],
        outs = [class_name + ".java"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) java $< $@ --class-name='{}' --namespace='{}'".format(class_name, namespace),
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
        parameter_library: Label of the parameter_library target (the YAML file)
        base_name: Base name for output file (optional, defaults to name with _go suffix removed)
        importpath: Go import path (optional, defaults to package path + "/" + base_name)
        **kwargs: Additional arguments for go_library

    Example:
        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
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
        base_name = name

    # Derive importpath if not provided
    if not importpath:
        pkg = native.package_name()
        if pkg:
            importpath = pkg + "/" + base_name
        else:
            importpath = base_name

    # Get namespace from package
    namespace = _derive_namespace_from_package()

    # Create a generated Go file using the Python script
    go_file_target = name + "_file"
    native.genrule(
        name = go_file_target,
        srcs = [parameter_library],
        outs = [base_name + ".go"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) go $< $@ --namespace='{}'".format(namespace),
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
        parameter_library: Label of the parameter_library target (the YAML file)
        base_name: Base name for output file (optional, defaults to name with _rs suffix removed)

    Example:
        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
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
        base_name = name

    # Create a generated Rust file using the Python script
    native.genrule(
        name = name,
        srcs = [parameter_library],
        outs = [base_name + ".rs"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) rust $< $@",
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = ["//visibility:public"],
    )
