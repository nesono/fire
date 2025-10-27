"""Bazel rules for parameter management."""

def _parameter_library_impl(ctx):
    """Implementation of the parameter_library rule."""

    # Get the input YAML file
    src = ctx.file.src

    # Create output file to store validated parameter data
    output = ctx.actions.declare_file(ctx.label.name + ".params")

    # Run validation on the parameter file
    ctx.actions.run(
        inputs = [src],
        outputs = [output],
        executable = ctx.executable._validator_tool,
        arguments = [
            src.path,
            output.path,
        ],
        mnemonic = "ValidateParameters",
        progress_message = "Validating parameters %s" % src.short_path,
    )

    return [
        DefaultInfo(files = depset([output])),
        ParameterInfo(
            src = src,
            validated_output = output,
        ),
    ]

# Define a provider to pass parameter information between rules
ParameterInfo = provider(
    doc = "Information about a parameter library",
    fields = {
        "src": "The source YAML file",
        "validated_output": "The validated parameter file",
    },
)

parameter_library = rule(
    implementation = _parameter_library_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = [".yaml", ".yml"],
            mandatory = True,
            doc = "The parameter YAML file to validate",
        ),
        "_validator_tool": attr.label(
            default = Label("//fire/tools:validate_parameters"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Validates a parameter file and makes it available for code generation",
)

def _cc_parameter_library_impl(ctx):
    """Implementation of the cc_parameter_library rule."""

    # Get the parameter library dependency
    param_info = ctx.attr.parameter_library[ParameterInfo]

    # Create output header file
    header = ctx.actions.declare_file(ctx.attr.name + ".h")

    # Build arguments for code generator
    args = [
        param_info.validated_output.path,
        header.path,
    ]

    # Only override namespace if explicitly specified
    if ctx.attr.namespace:
        args.extend(["--namespace", ctx.attr.namespace])

    # Run C++ code generator
    ctx.actions.run(
        inputs = [param_info.validated_output],
        outputs = [header],
        executable = ctx.executable._cpp_generator_tool,
        arguments = args,
        mnemonic = "GenerateCppParameters",
        progress_message = "Generating C++ header for %s" % param_info.src.short_path,
    )

    # Create a cc_library that can be used as a dependency
    compilation_context = cc_common.create_compilation_context(
        headers = depset([header]),
        includes = depset([header.dirname]),
    )

    cc_info = CcInfo(
        compilation_context = compilation_context,
    )

    return [
        DefaultInfo(files = depset([header])),
        cc_info,
    ]

cc_parameter_library = rule(
    implementation = _cc_parameter_library_impl,
    attrs = {
        "namespace": attr.string(
            doc = "C++ namespace for the generated code (overrides the namespace in the parameter file)",
        ),
        "parameter_library": attr.label(
            mandatory = True,
            providers = [ParameterInfo],
            doc = "The parameter_library target to generate C++ code from",
        ),
        "_cpp_generator_tool": attr.label(
            default = Label("//fire/tools:generate_cpp_parameters"),
            executable = True,
            cfg = "exec",
        ),
    },
    fragments = ["cpp"],
    doc = "Generates a C++ header file from a parameter library",
)
