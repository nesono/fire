"""Bazel rules for parameter management.

Parameters are defined in YAML files and validated at build time using JSON schema.
"""

def _validate_parameters_impl(ctx):
    """Implementation of parameter validation rule."""
    script = ctx.executable._script
    schema = ctx.file._schema
    input_file = ctx.file.src
    output = ctx.outputs.out

    # Create a wrapper script that runs validation and copies file on success
    wrapper_script = ctx.actions.declare_file(ctx.label.name + "_wrapper.sh")
    ctx.actions.write(
        output = wrapper_script,
        content = """#!/bin/bash
"{script}" "{input}" --schema="{schema}" && cp "{input}" "{output}"
""".format(
            script = script.path,
            input = input_file.path,
            schema = schema.path,
            output = output.path,
        ),
        is_executable = True,
    )

    # Get runfiles for the script
    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    # Run validation
    ctx.actions.run(
        inputs = [input_file, schema] + script_runfiles,
        outputs = [output],
        executable = wrapper_script,
        tools = [script],
        mnemonic = "ValidateParameters",
        progress_message = "Validating parameters in %s" % input_file.basename,
    )

    return [DefaultInfo(files = depset([output]))]

_validate_parameters = rule(
    implementation = _validate_parameters_impl,
    attrs = {
        "out": attr.output(
            mandatory = True,
        ),
        "src": attr.label(
            allow_single_file = [".yaml", ".yml"],
            mandatory = True,
            doc = "Parameter YAML file to validate",
        ),
        "_schema": attr.label(
            default = Label("@fire//fire/starlark:parameter_schema.json"),
            allow_single_file = [".json"],
        ),
        "_script": attr.label(
            default = Label("@fire//fire/starlark:validate_parameters_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Validates a parameter YAML file against the parameter schema",
)

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

        # Validate parameters
        parameter_library(
            name = "vehicle_params",
            src = "vehicle_params.yaml",
        )
    """

    # Use empty namespace if not provided
    if not namespace:
        namespace = ""

    # Create validation target using custom rule
    validation_name = name + "_validation"
    _validate_parameters(
        name = validation_name,
        src = src,
        out = name + "_validated.yaml",
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
