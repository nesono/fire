"""Bazel rules for parameter management in pure Starlark.

Parameters can be defined inline in BUILD files or loaded from separate .bzl files.
Validation happens at load time, and C++ code is generated at build time.
"""

load("@rules_cc//cc:defs.bzl", "cc_library")
load("//fire/starlark:cpp_generator.bzl", "cpp_generator")
load("//fire/starlark:validator.bzl", "validator")

def parameter_library(
        name,
        schema_version = "1.0",
        namespace = None,
        parameters = []):
    """Define a parameter library inline in Starlark.

    Args:
        name: Name of the library
        schema_version: Schema version (default "1.0")
        namespace: C++ namespace for parameters
        parameters: List of parameter dictionaries

    Example:
        parameter_library(
            name = "my_params",
            namespace = "my.namespace",
            parameters = [
                {
                    "name": "max_velocity",
                    "type": "float",
                    "unit": "m/s",
                    "value": 55.0,
                    "description": "Maximum velocity",
                },
            ],
        )
    """
    if not namespace:
        fail("namespace is required")

    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate C++ header
    cpp_code = cpp_generator.generate(param_data)

    # Create a generated header file
    native.genrule(
        name = name,
        outs = [name + ".h"],
        cmd = """cat > $@ <<'EOF'
{}
EOF""".format(cpp_code),
        visibility = ["//visibility:public"],
    )

def cc_parameter_library(name, parameter_library, **kwargs):
    """Create a cc_library from a parameter_library.

    Args:
        name: Name of the cc_library
        parameter_library: Label of the parameter_library (the generated .h file)
        **kwargs: Additional arguments for cc_library
    """
    cc_library(
        name = name,
        hdrs = [parameter_library],
        includes = ["."],
        **kwargs
    )
