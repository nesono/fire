"""Bazel rules for generating requirement reports."""

def _generate_report_impl(ctx):
    """Implementation of the generate_report rule."""

    # Get the Python script executable
    script = ctx.executable._script

    # Prepare arguments
    args = ctx.actions.args()
    args.add(ctx.attr.report_type)
    args.add(ctx.outputs.out.path)

    # Add all input files
    for src in ctx.files.srcs:
        args.add(src.path)

    # Add standard if specified
    if ctx.attr.standard:
        args.add("--standard=" + ctx.attr.standard)

    # Add critical_type if specified
    if ctx.attr.critical_type:
        args.add("--critical-type=" + ctx.attr.critical_type)

    # Get runfiles for the script
    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    # Run the Python script
    ctx.actions.run(
        inputs = ctx.files.srcs + [script] + script_runfiles,
        outputs = [ctx.outputs.out],
        executable = script,
        arguments = [args],
        mnemonic = "GenerateReport",
        progress_message = "Generating %s report for %s" % (ctx.attr.report_type, ctx.label.name),
    )

    return [DefaultInfo(files = depset([ctx.outputs.out]))]

def _release_report_impl(ctx):
    """Implementation of the release_report rule."""

    script = ctx.executable._script
    args = ctx.actions.args()
    args.add("--out")
    args.add(ctx.outputs.out.path)
    args.add("--product")
    args.add(ctx.attr.product)

    requirement_files = [f for f in ctx.files.requirements if f.path.endswith(".md")]
    param_files = [
        f
        for f in ctx.files.params
        if f.path.endswith(".yaml") or f.path.endswith(".yml")
    ]
    trace_files = [f for f in ctx.files.source_traces if f.path.endswith(".json")]

    args.add_all(requirement_files, before_each = "--requirements")
    args.add_all(param_files, before_each = "--params")
    args.add_all(trace_files, before_each = "--source-traces")

    if ctx.file.exemptions:
        args.add("--exemptions")
        args.add(ctx.file.exemptions.path)

    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    ctx.actions.run(
        inputs = requirement_files +
                 param_files +
                 trace_files +
                 ([ctx.file.exemptions] if ctx.file.exemptions else []) +
                 [script] +
                 script_runfiles,
        outputs = [ctx.outputs.out],
        executable = script,
        arguments = [args],
        mnemonic = "ReleaseReport",
        progress_message = "Generating release report for %s" % ctx.label.name,
    )

    return [DefaultInfo(files = depset([ctx.outputs.out]))]

generate_report = rule(
    implementation = _generate_report_impl,
    attrs = {
        "critical_type": attr.string(
            doc = "Requirement type to highlight in compliance reports (e.g., 'safety', 'security')",
        ),
        "out": attr.output(
            mandatory = True,
            doc = "Output markdown file",
        ),
        "report_type": attr.string(
            mandatory = True,
            values = ["traceability", "coverage", "change_impact", "compliance"],
            doc = "Type of report to generate",
        ),
        "srcs": attr.label_list(
            allow_files = [".md"],
            mandatory = True,
            doc = "List of requirement markdown files to include in the report",
        ),
        "standard": attr.string(
            doc = "Standard name for compliance reports (e.g., 'ISO 26262', 'IEC 61508')",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:generate_report_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = """Generates requirement reports in markdown format.

    This rule parses requirement files and generates various types of reports:
    - traceability: Full traceability matrix with version information
    - coverage: Coverage metrics showing parameter/test/standard coverage
    - change_impact: Identifies requirements with stale parent references
    - compliance: Compliance report for a specific standard (e.g., ISO 26262)

    Example:
        generate_report(
            name = "traceability_report",
            srcs = glob(["requirements/*.md"]),
            report_type = "traceability",
            out = "TRACEABILITY.md",
        )

        generate_report(
            name = "compliance_report",
            srcs = glob(["requirements/*.md"]),
            report_type = "compliance",
            standard = "ISO 26262",
            out = "COMPLIANCE.md",
        )
    """,
)

release_report = rule(
    implementation = _release_report_impl,
    attrs = {
        "exemptions": attr.label(
            allow_single_file = [".yaml", ".yml"],
            doc = "Optional exemptions YAML file",
        ),
        "out": attr.output(
            mandatory = True,
            doc = "Output markdown file",
        ),
        "params": attr.label_list(
            allow_files = [".yaml", ".yml"],
            doc = "Parameter YAML files to include in the report",
        ),
        "product": attr.string(
            default = "Product",
            doc = "Product name shown in the report",
        ),
        "requirements": attr.label_list(
            allow_files = [".md"],
            mandatory = True,
            doc = "Requirement markdown files to include in the report",
        ),
        "source_traces": attr.label_list(
            allow_files = [".json"],
            doc = "Source traceability JSON files",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:release_report_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = """Generates a release readiness report in markdown format.

    Example:
        release_report(
            name = "release_report",
            requirements = glob(["requirements/*.md"]),
            params = glob(["params/*.yaml"]),
            source_traces = [":brake_controller_trace"],
            exemptions = ":release_exemptions",
            product = "Brake Controller",
            out = "RELEASE_REPORT.md",
        )
    """,
)
