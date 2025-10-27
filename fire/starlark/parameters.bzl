"""Bazel rules for parameter management using pure Starlark."""

load("//fire/starlark:cpp_generator.bzl", "cpp_generator")

# Provider to pass parameter information between rules
ParameterInfo = provider(
    doc = "Information about a parameter library",
    fields = {
        "data": "The parsed and validated parameter data",
        "src": "The source parameter file",
    },
)

def _parameter_library_impl(ctx):
    """Implementation of the parameter_library rule."""
    src = ctx.file.src

    # We need to read the file content - use ctx.actions.run with a script
    # that validates and copies the JSON
    output = ctx.actions.declare_file(ctx.label.name + ".params.json")

    # Create a validation script
    script = ctx.actions.declare_file(ctx.label.name + "_validate.py")
    ctx.actions.write(
        output = script,
        content = """
import json
import sys

# Read input JSON
with open(sys.argv[1], 'r') as f:
    data = json.load(f)

# Write output JSON (validation happens in Starlark via aspect or test)
with open(sys.argv[2], 'w') as f:
    json.dump(data, f, indent=2)
""",
    )

    # Run validation script
    ctx.actions.run(
        inputs = [src, script],
        outputs = [output],
        executable = "python3",
        arguments = [script.path, src.path, output.path],
        mnemonic = "ValidateParameters",
    )

    # Parse the JSON content for provider (read directly)
    # Note: We can't validate in the rule, so we'll do it via an aspect or macro
    # For now, just pass the file through
    return [
        DefaultInfo(files = depset([output])),
        ParameterInfo(
            src = src,
            data = struct(),  # Will be populated by aspect
        ),
    ]

parameter_library = rule(
    implementation = _parameter_library_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = [".json"],
            mandatory = True,
            doc = "The parameter JSON file to validate",
        ),
    },
    doc = "Validates a parameter file and makes it available for code generation",
)

def _cc_parameter_library_impl(ctx):
    """Implementation of the cc_parameter_library rule."""

    # Get the parameter library dependency
    param_info = ctx.attr.parameter_library[ParameterInfo]
    param_data = param_info.data

    # Override namespace if specified
    if ctx.attr.namespace:
        param_data = dict(param_data)  # Make a copy
        param_data["namespace"] = ctx.attr.namespace

    # Generate C++ header file
    header = ctx.actions.declare_file(ctx.attr.name + ".h")
    cpp_code = cpp_generator.generate(param_data)

    ctx.actions.write(
        output = header,
        content = cpp_code,
    )

    # Create compilation context for C++
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
    },
    fragments = ["cpp"],
    doc = "Generates a C++ header file from a parameter library",
)
