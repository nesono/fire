"""Bazel rules for parameter management.

Parameters are defined in YAML files and validated at build time.
"""

def _validate_parameters_impl(ctx):
    """Implementation of parameter validation rule."""
    script = ctx.executable._script
    input_file = ctx.file.src
    output = ctx.outputs.out

    # Get runfiles for the script
    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    args = [input_file.path, output.path]

    # Run validation
    ctx.actions.run(
        inputs = [input_file] + script_runfiles,
        outputs = [output],
        arguments = args,
        executable = script,
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
        "_script": attr.label(
            default = Label("@fire//fire/starlark:validate_parameters_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Validates a parameter YAML file",
)

def parameter_library(name, src, tags = [], visibility = None):
    """Define and validate a parameter library from a YAML file.

    This macro validates the YAML file at build time
    and makes it available for code generation.

    Args:
        name: Name of the library
        src: Path to the parameter YAML file (e.g., "vehicle_params.yaml")
        tags: Tags for this target (e.g., ["manual", "failure_test"])
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

    # Create validation target using custom rule
    validation_name = name + "_validation"
    _validate_parameters(
        name = validation_name,
        src = src,
        out = name + "_validated.yaml",
        tags = tags,
    )

    # Main target is a filegroup containing the validated YAML
    native.filegroup(
        name = name,
        srcs = [":" + validation_name],
        tags = tags,
        visibility = visibility,
    )
