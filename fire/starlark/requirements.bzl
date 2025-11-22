"""Bazel rules for requirement management."""

def _validate_requirements_impl(ctx):
    """Implementation of requirement validation rule."""
    script = ctx.executable._script

    # Output validation marker file
    output = ctx.outputs.out

    # Use "." as workspace root - the sandbox will have the right structure
    workspace_root = "."

    # Build arguments list
    args = ctx.actions.args()
    args.add(workspace_root)
    args.add("--allowed-deps")

    # Add allowed dependency paths (short_path format)
    # Include srcs in allowed deps (requirements in same target can reference each other)
    for src in ctx.files.srcs:
        args.add(src.short_path)
    for dep in ctx.files.deps:
        args.add(dep.short_path)

    # Add requirement files (using short_path which is relative to workspace)
    args.add("--")
    for src in ctx.files.srcs:
        args.add(src.short_path)

    # Create a wrapper script that runs the validator and touches the output
    wrapper_script = ctx.actions.declare_file(ctx.label.name + "_wrapper.sh")
    ctx.actions.write(
        output = wrapper_script,
        content = """#!/bin/bash
"$@" && touch {output}
""".format(output = output.path),
        is_executable = True,
    )

    # Get runfiles for the script
    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    # Run validation script
    # Note: We need to disable sandbox or make all potential reference targets available
    ctx.actions.run(
        inputs = ctx.files.srcs + ctx.files.deps + script_runfiles,
        outputs = [output],
        executable = wrapper_script,
        arguments = [script.path, args],
        tools = [script],
        mnemonic = "ValidateRequirements",
        progress_message = "Validating cross-references in %s" % ctx.label.name,
        use_default_shell_env = True,
        execution_requirements = {
            "no-sandbox": "1",  # Disable sandbox so we can access workspace files
        },
    )

    return [DefaultInfo(files = depset([output]))]

_validate_requirements = rule(
    implementation = _validate_requirements_impl,
    attrs = {
        "deps": attr.label_list(
            allow_files = [".md", ".yaml", ".yml"],
            default = [],
            doc = "Dependencies: other requirement files and parameter files referenced by srcs",
        ),
        "out": attr.output(
            mandatory = True,
        ),
        "srcs": attr.label_list(
            allow_files = [".md"],
            mandatory = True,
            doc = "List of requirement markdown files to validate",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:validate_cross_references_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Validates cross-references in requirement documents",
)

def requirement_library(name, srcs, deps = [], tags = [], visibility = None):
    """Validates requirement documents and creates a filegroup.

    This validates that all cross-references (parameters, requirements, tests)
    actually exist, then creates a filegroup containing the requirement files.

    Args:
        name: Name of the target
        srcs: List of requirement markdown files
        deps: List of dependencies that srcs references (requirement files and parameter files)
        tags: Tags for this target (e.g., ["manual", "failure_test"])
        visibility: Visibility of the target

    Example:
        requirement_library(
            name = "safety_requirements",
            srcs = glob(["requirements/safety/*.md"]),
            deps = [":vehicle_params"],  # References parameter files
        )

        requirement_library(
            name = "component_requirements",
            srcs = glob(["components/**/*.swreq.md"]),
            deps = [
                ":safety_requirements",  # References system requirements
                ":vehicle_params",       # References parameter files
            ],
        )
    """

    # Create validation target
    validation_name = name + "_validation"
    _validate_requirements(
        name = validation_name,
        srcs = srcs,
        deps = deps,
        out = validation_name + ".marker",
        tags = tags,  # tags is a built-in attribute available on all rules
    )

    # Create filegroup that depends on validation
    native.filegroup(
        name = name,
        srcs = srcs + [":" + validation_name],
        visibility = visibility,
        tags = tags,  # tags is a built-in attribute
    )
