"""Bazel rules for parameter management.

Parameters are defined in YAML files and validated at build time using JSON schema.
Code is generated for multiple languages from the validated YAML.

This file provides only parameter validation (parameter_library).
For code generation, use @fire//fire/starlark:codegen.bzl which provides:
  - generate_cc_parameters()      - generates .h files
  - generate_python_parameters()  - generates .py files
  - generate_java_parameters()    - generates .java files
  - generate_go_parameters()      - generates .go files
  - generate_rust_parameters()    - generates .rs files

Consumers are responsible for wrapping generated files in their own language libraries.
This keeps Fire's dependencies minimal - Fire only needs rules_python for validation.
"""

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

        # In BUILD.bazel:
        load("@fire//fire/starlark:parameters.bzl", "parameter_library")
        load("@fire//fire/starlark:codegen.bzl", "generate_cc_parameters")
        load("@rules_cc//cc:defs.bzl", "cc_library")

        # Validate parameters
        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
        )

        # Generate C++ code
        generate_cc_parameters(
            name = "vehicle_params_h",
            parameter_library = ":vehicle_params",
        )

        # Wrap in cc_library
        cc_library(
            name = "vehicle_params_cc",
            hdrs = [":vehicle_params_h"],
        )
    """

    # Use empty namespace if not provided
    if not namespace:
        namespace = ""

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
