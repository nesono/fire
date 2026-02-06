"""Code generation functions for parameter libraries.

This file provides functions that generate source code from parameter libraries.
Consumers are responsible for wrapping the generated files in their language-specific
library rules (cc_library, rust_library, go_library, etc.).

This design keeps Fire's dependencies minimal - Fire only needs rules_python for
validation. Consumers control which language rules they use and which versions.
"""

def _generate_parameters_impl(ctx):
    """Implementation of parameter code generation rule."""
    script = ctx.executable._script
    input_file = ctx.file.src
    language = ctx.attr.language

    # Java needs a .srcjar (zip of .java files) since java_library
    # doesn't support TreeArtifact directories in srcs
    if language == "java":
        output = ctx.actions.declare_file(ctx.attr.base_name + ".srcjar")
    else:
        output = ctx.actions.declare_directory(ctx.attr.base_name)

    # Build arguments
    args = ctx.actions.args()

    # Add package path first (before subcommand)
    args.add("--package-path=" + ctx.label.package)

    args.add(language)
    args.add(input_file.path)
    args.add(output.path)

    # Add language-specific flags
    if ctx.attr.namespace:
        args.add("--namespace=" + ctx.attr.namespace)
    if ctx.attr.package_prefix:
        args.add("--namespace=" + ctx.attr.package_prefix)
    if ctx.attr.package_name:
        args.add("--namespace=" + ctx.attr.package_name)
    if ctx.attr.class_name:
        args.add("--class-name=" + ctx.attr.class_name)

    # Get runfiles for the script
    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    # Language name for messages (capitalize first letter)
    lang_display = language.capitalize() if language != "cpp" else "C++"

    # Run code generation
    ctx.actions.run(
        inputs = [input_file] + script_runfiles,
        outputs = [output],
        executable = script,
        arguments = [args],
        mnemonic = "Generate" + lang_display.replace("+", "").replace(" ", "") + "Parameters",
        progress_message = "Generating %s parameters from %s" % (lang_display, input_file.basename),
    )

    return [DefaultInfo(files = depset([output]))]

_generate_parameters = rule(
    implementation = _generate_parameters_impl,
    attrs = {
        "base_name": attr.string(
            mandatory = True,
            doc = "Base name for the output directory (TreeArtifact)",
        ),
        "class_name": attr.string(
            doc = "Java class name (defaults to PascalCase of base_name)",
        ),
        "language": attr.string(
            mandatory = True,
            values = ["cpp", "python", "java", "go", "rust"],
            doc = "Target programming language",
        ),
        "namespace": attr.string(
            doc = "C++ namespace (use :: for nested, e.g., 'outer::inner')",
        ),
        "package_name": attr.string(
            doc = "Go package name",
        ),
        "package_prefix": attr.string(
            doc = "Java package prefix (e.g., 'com.example')",
        ),
        "src": attr.label(
            allow_single_file = [".yaml", ".yml"],
            mandatory = True,
            doc = "Parameter YAML file (validated)",
        ),
        "_script": attr.label(
            default = Label("@fire//fire/starlark:generate_code_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Generates source code from parameter library for a specific language",
)

def generate_cc_parameters(
        name,
        parameter_library,
        base_name = None,
        namespace = None,
        visibility = None):
    """Generate C++ header files from parameter library.

    This rule generates a directory of .h files (one per parameter-version).
    Consumers should wrap it in cc_library.

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        base_name: Base name for output directory (optional, defaults to name)
        namespace: Optional C++ namespace (use :: for nested, e.g., "outer::inner")
        visibility: Visibility of the generated headers

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

    # Use custom rule for code generation
    _generate_parameters(
        name = name,
        src = parameter_library,
        base_name = base_name,
        language = "cpp",
        namespace = namespace if namespace else "",
        visibility = visibility if visibility else ["//visibility:public"],
    )

def generate_python_parameters(
        name,
        parameter_library,
        base_name = None,
        visibility = None):
    """Generate Python module files from parameter library.

    This rule generates a directory of .py files (one per parameter-version).
    Consumers should wrap it in py_library.

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        base_name: Base name for output directory (optional, defaults to name)
        visibility: Visibility of the generated modules

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

    # Use custom rule for code generation
    _generate_parameters(
        name = name,
        src = parameter_library,
        base_name = base_name,
        language = "python",
        visibility = visibility if visibility else ["//visibility:public"],
    )

def generate_java_parameters(
        name,
        parameter_library,
        package_prefix = None,
        class_name = None,
        visibility = None):
    """Generate Java class files from parameter library.

    This rule generates a single Java file containing all parameters.
    Consumers should wrap it in java_library.

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        package_prefix: Optional package prefix (e.g., "com.example")
        class_name: Optional class name (defaults to PascalCase of name, e.g., "VehicleParams")
        visibility: Visibility of the generated classes

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
            package_prefix = "com.example",
        )

        java_library(
            name = "vehicle_params_java",
            srcs = [":vehicle_params_java_src"],
        )
    """

    # Use custom rule for code generation
    _generate_parameters(
        name = name,
        src = parameter_library,
        base_name = name,
        language = "java",
        package_prefix = package_prefix if package_prefix else "",
        class_name = class_name if class_name else "",
        visibility = visibility if visibility else ["//visibility:public"],
    )

def generate_go_parameters(
        name,
        parameter_library,
        base_name = None,
        visibility = None):
    """Generate Go source files from parameter library.

    This rule generates a directory with sub-packages (one per parameter-version).
    Go consumers need per-sub-package go_library targets.

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        base_name: Base name for output directory (optional, defaults to name)
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
            name = "wheel_count_v1_go",
            srcs = [":vehicle_params_go_src"],
            importpath = "examples/vehicle_params/wheel_count_v1",
        )
    """
    if not base_name:
        base_name = name

    # Use custom rule for code generation
    _generate_parameters(
        name = name,
        src = parameter_library,
        base_name = base_name,
        language = "go",
        visibility = visibility if visibility else ["//visibility:public"],
    )

def generate_rust_parameters(
        name,
        parameter_library,
        base_name = None,
        visibility = None):
    """Generate Rust module files from parameter library.

    This rule generates a directory of .rs files (one per parameter-version).
    Consumers can include files directly via include!() or #[path].

    Args:
        name: Name of the generation target
        parameter_library: Label of the parameter_library target (the validated YAML)
        base_name: Base name for output directory (optional, defaults to name)
        visibility: Visibility of the generated modules

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

        rust_test(
            name = "test",
            srcs = ["test.rs", ":vehicle_params_rs"],
        )
    """
    if not base_name:
        base_name = name

    # Use custom rule for code generation
    _generate_parameters(
        name = name,
        src = parameter_library,
        base_name = base_name,
        language = "rust",
        visibility = visibility if visibility else ["//visibility:public"],
    )
