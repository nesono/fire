"""Bazel rules for source-to-requirement traceability."""

def _extract_source_traceability_impl(ctx):
    """Implementation of source traceability extraction rule."""
    script = ctx.executable._script

    # Output trace JSON file
    output = ctx.outputs.out

    # Build arguments list
    args = ctx.actions.args()

    args.add("--output")
    args.add(output.path)

    # Add each requirement dep file
    for dep in ctx.files.deps:
        args.add("--dep")
        args.add(dep.short_path)

    # Add source files (positional)
    args.add("--")
    for src in ctx.files.srcs:
        args.add(src.short_path)

    # Get runfiles for the script
    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    # Run extraction script
    ctx.actions.run(
        inputs = ctx.files.srcs + ctx.files.deps + script_runfiles,
        outputs = [output],
        executable = script,
        arguments = [args],
        mnemonic = "ExtractSourceTraceability",
        progress_message = "Extracting source traceability for %s" % ctx.label.name,
        use_default_shell_env = True,
        execution_requirements = {
            "no-sandbox": "1",
        },
    )

    return [DefaultInfo(files = depset([output]))]

_extract_source_traceability = rule(
    implementation = _extract_source_traceability_impl,
    attrs = {
        "deps": attr.label_list(
            allow_files = [".md"],
            default = [],
            doc = "Requirement libraries that these source files implement or test",
        ),
        "out": attr.output(
            mandatory = True,
        ),
        "srcs": attr.label_list(
            allow_files = True,
            mandatory = True,
            doc = "Source files to link to requirements",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:extract_source_traceability_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Produces a JSON mapping from source files to requirement IDs declared via deps",
)

def source_traceability(name, srcs, deps = [], tags = [], visibility = None):
    """Declare traceability from source files to requirements.

    Links source files to requirement libraries purely via Bazel
    dependency declarations. Produces a <name>.trace.json mapping
    each source file to the requirement IDs found in deps.

    Args:
        name: Name of the target
        srcs: List of source files that implement or test the requirements
        deps: List of requirement libraries these sources trace to
        tags: Tags for this target
        visibility: Visibility of the target

    Example:
        source_traceability(
            name = "brake_controller_trace",
            srcs = ["brake_controller.cc", "brake_controller_test.cc"],
            deps = ["//vehicle/requirements:braking_requirements"],
        )
    """

    _extract_source_traceability(
        name = name,
        srcs = srcs,
        deps = deps,
        out = name + ".trace.json",
        tags = tags,
        visibility = visibility,
    )
