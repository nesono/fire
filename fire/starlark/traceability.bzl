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

    # Serialize implements and verifies mappings as JSON
    if ctx.attr.implements:
        args.add("--implements-json")
        args.add(json.encode(ctx.attr.implements))

    if ctx.attr.verifies:
        args.add("--verifies-json")
        args.add(json.encode(ctx.attr.verifies))

    # Get runfiles for the script
    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    # Run extraction script
    ctx.actions.run(
        inputs = ctx.files.deps + script_runfiles,
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
            doc = "Requirement libraries containing the referenced requirement IDs",
        ),
        "implements": attr.string_list_dict(
            default = {},
            doc = "Dict mapping source files to versioned requirement refs they implement",
        ),
        "out": attr.output(
            mandatory = True,
        ),
        "verifies": attr.string_list_dict(
            default = {},
            doc = "Dict mapping test files to versioned requirement refs they verify",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:extract_source_traceability_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Validates and produces a JSON mapping from source files to specific requirement IDs",
)

def source_traceability(name, deps, implements = {}, verifies = {}, tags = [], visibility = None):
    """Declare traceability from source files to specific requirements.

    Maps source files to the specific requirement IDs they implement or
    verify, with version tracking. Produces a <name>.trace.json and
    validates that all referenced requirement IDs exist in deps.

    Args:
        name: Name of the target
        deps: List of requirement libraries containing the referenced requirements
        implements: Dict mapping source files to lists of "REQ_ID?version=N" strings
        verifies: Dict mapping test files to lists of "REQ_ID?version=N" strings
        tags: Tags for this target
        visibility: Visibility of the target

    Example:
        source_traceability(
            name = "brake_controller_trace",
            implements = {
                "brake_controller.cc": [
                    "REQ_BC_CALCULATE_FORCE?version=1",
                    "REQ_BC_EMERGENCY_BRAKE?version=1",
                ],
            },
            verifies = {
                "brake_controller_test.cc": [
                    "REQ_BC_CALCULATE_FORCE?version=1",
                    "REQ_BC_EMERGENCY_BRAKE?version=1",
                ],
            },
            deps = [":brake_controller_requirements"],
        )
    """

    _extract_source_traceability(
        name = name,
        deps = deps,
        implements = implements,
        verifies = verifies,
        out = name + ".trace.json",
        tags = tags,
        visibility = visibility,
    )
