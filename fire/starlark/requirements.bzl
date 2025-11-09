"""Bazel rules for requirement management."""

def _validate_requirements_impl(ctx):
    """Implementation of requirement validation rule."""
    script = ctx.file._script

    # Output validation marker file
    output = ctx.outputs.out

    # Use "." as workspace root - the sandbox will have the right structure
    workspace_root = "."

    # Build command
    cmd = "python3 {script} {workspace}".format(
        script = script.path,
        workspace = workspace_root,
    )

    # Add requirement files (using short_path which is relative to workspace)
    for src in ctx.files.srcs:
        cmd += " " + src.short_path
    cmd += " && touch " + output.path

    # Run validation script
    # Note: We need to disable sandbox or make all potential reference targets available
    ctx.actions.run_shell(
        inputs = ctx.files.srcs + [script],
        outputs = [output],
        command = cmd,
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
        "out": attr.output(
            mandatory = True,
        ),
        "srcs": attr.label_list(
            allow_files = [".md"],
            mandatory = True,
            doc = "List of requirement markdown files to validate",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:validate_cross_references.py"),
            allow_single_file = True,
        ),
    },
    doc = "Validates cross-references in requirement documents",
)

def requirement_library(name, srcs, visibility = None):
    """Validates requirement documents and creates a filegroup.

    This validates that all cross-references (parameters, requirements, tests)
    actually exist, then creates a filegroup containing the requirement files.

    Args:
        name: Name of the target
        srcs: List of requirement markdown files
        visibility: Visibility of the target

    Example:
        requirement_library(
            name = "safety_requirements",
            srcs = glob(["requirements/safety/*.md"]),
        )
    """

    # Create validation target
    validation_name = name + "_validation"
    _validate_requirements(
        name = validation_name,
        srcs = srcs,
        out = validation_name + ".marker",
    )

    # Create filegroup that depends on validation
    native.filegroup(
        name = name,
        srcs = srcs + [":" + validation_name],
        visibility = visibility,
    )
