"""Code generation functions for parameter libraries.

This file provides functions that generate source code from parameter libraries.
Consumers are responsible for wrapping the generated files in their language-specific
library rules (cc_library, rust_library, go_library, etc.).

This design keeps Fire's dependencies minimal - Fire only needs rules_python for
validation. Consumers control which language rules they use and which versions.
"""

def generate_cc_parameters(
        name,
        parameter_library,
        base_name = None,
        namespace = None,
        visibility = None):
    """Generate C++ header file from parameter library.

    This rule generates a .h file. Consumers should wrap it in cc_library.

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        base_name: Base name for output file (optional, defaults to name)
        namespace: Optional C++ namespace (use :: for nested, e.g., "outer::inner")
        visibility: Visibility of the generated header

    Example:
        load("@fire//fire/starlark:parameters.bzl", "parameter_library")
        load("@fire//fire/starlark:codegen.bzl", "generate_cc_parameters")
        load("@rules_cc//cc:defs.bzl", "cc_library")

        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
        )

        generate_cc_parameters(
            name = "vehicle_params_h",
            parameter_library = ":vehicle_params",
            namespace = "vehicle",
        )

        cc_library(
            name = "vehicle_params_cc",
            hdrs = [":vehicle_params_h"],
        )
    """
    if not base_name:
        base_name = name

    # Build command with optional namespace
    cmd = "$(location @fire//fire/starlark:generate_code_script) cpp $< $@"
    if namespace:
        cmd += " --namespace='{}'".format(namespace)

    native.genrule(
        name = name,
        srcs = [parameter_library],
        outs = [base_name + ".h"],
        cmd = cmd,
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = visibility if visibility else ["//visibility:public"],
    )

def generate_python_parameters(
        name,
        parameter_library,
        base_name = None,
        visibility = None):
    """Generate Python module from parameter library.

    This rule generates a .py file. Consumers should wrap it in py_library.

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        base_name: Base name for output file (optional, defaults to name)
        visibility: Visibility of the generated module

    Example:
        load("@fire//fire/starlark:parameters.bzl", "parameter_library")
        load("@fire//fire/starlark:codegen.bzl", "generate_python_parameters")
        load("@rules_python//python:defs.bzl", "py_library")

        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
        )

        generate_python_parameters(
            name = "vehicle_params_py_src",
            parameter_library = ":vehicle_params",
        )

        py_library(
            name = "vehicle_params_py",
            srcs = [":vehicle_params_py_src"],
        )
    """
    if not base_name:
        base_name = name

    native.genrule(
        name = name,
        srcs = [parameter_library],
        outs = [base_name + ".py"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) python $< $@",
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = visibility if visibility else ["//visibility:public"],
    )

def generate_java_parameters(
        name,
        parameter_library,
        class_name = None,
        package_prefix = None,
        visibility = None):
    """Generate Java class from parameter library.

    This rule generates a .java file. Consumers should wrap it in java_library.

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        class_name: Name of the generated class (optional, derived from name if not provided)
        package_prefix: Optional package prefix (e.g., "com.example")
        visibility: Visibility of the generated class

    Example:
        load("@fire//fire/starlark:parameters.bzl", "parameter_library")
        load("@fire//fire/starlark:codegen.bzl", "generate_java_parameters")
        load("@rules_java//java:defs.bzl", "java_library")

        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
        )

        generate_java_parameters(
            name = "vehicle_params_java_src",
            parameter_library = ":vehicle_params",
            class_name = "VehicleParams",
            package_prefix = "com.example",
        )

        java_library(
            name = "vehicle_params_java",
            srcs = [":vehicle_params_java_src"],
        )
    """

    # Derive class_name if not provided
    if not class_name:
        base_name = name
        parts = base_name.split("_")
        class_name = "".join([word.capitalize() for word in parts])

    # Build command with optional package prefix
    cmd = "$(location @fire//fire/starlark:generate_code_script) java $< $@ --class-name='{}'".format(class_name)
    if package_prefix:
        cmd += " --namespace='{}'".format(package_prefix)

    native.genrule(
        name = name,
        srcs = [parameter_library],
        outs = [class_name + ".java"],
        cmd = cmd,
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = visibility if visibility else ["//visibility:public"],
    )

def generate_go_parameters(
        name,
        parameter_library,
        base_name = None,
        package_name = None,
        visibility = None):
    """Generate Go source file from parameter library.

    This rule generates a .go file. Consumers should wrap it in go_library.

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        base_name: Base name for output file (optional, defaults to name)
        package_name: Go package name (optional, derived from base_name if not provided)
        visibility: Visibility of the generated source

    Example:
        load("@fire//fire/starlark:parameters.bzl", "parameter_library")
        load("@fire//fire/starlark:codegen.bzl", "generate_go_parameters")
        load("@rules_go//go:def.bzl", "go_library")

        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
        )

        generate_go_parameters(
            name = "vehicle_params_go_src",
            parameter_library = ":vehicle_params",
        )

        go_library(
            name = "vehicle_params_go",
            srcs = [":vehicle_params_go_src"],
            importpath = "github.com/example/vehicle_params",
        )
    """
    if not base_name:
        base_name = name

    # Derive package name if not provided
    if not package_name:
        package_name = base_name.replace("_", "")

    native.genrule(
        name = name,
        srcs = [parameter_library],
        outs = [base_name + ".go"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) go $< $@ --namespace='{}'".format(package_name),
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = visibility if visibility else ["//visibility:public"],
    )

def generate_rust_parameters(
        name,
        parameter_library,
        base_name = None,
        visibility = None):
    """Generate Rust module from parameter library.

    This rule generates a .rs file. Consumers can include it directly in
    rust_library/rust_binary/rust_test srcs.

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        base_name: Base name for output file (optional, defaults to name)
        visibility: Visibility of the generated module

    Example:
        load("@fire//fire/starlark:parameters.bzl", "parameter_library")
        load("@fire//fire/starlark:codegen.bzl", "generate_rust_parameters")
        load("@rules_rust//rust:defs.bzl", "rust_library")

        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
        )

        generate_rust_parameters(
            name = "vehicle_params_rs",
            parameter_library = ":vehicle_params",
        )

        # Can use directly in srcs (Rust doesn't need a separate library wrapper)
        rust_test(
            name = "test",
            srcs = ["test.rs", ":vehicle_params_rs"],
        )
    """
    if not base_name:
        base_name = name

    native.genrule(
        name = name,
        srcs = [parameter_library],
        outs = [base_name + ".rs"],
        cmd = "$(location @fire//fire/starlark:generate_code_script) rust $< $@",
        tools = ["@fire//fire/starlark:generate_code_script"],
        visibility = visibility if visibility else ["//visibility:public"],
    )
