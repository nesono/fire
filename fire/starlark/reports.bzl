"""Bazel rules for generating requirement reports."""

def _generate_report_impl(ctx):
    """Implementation of the generate_report rule."""

    # Get the Python script file
    script = ctx.file._script

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

    # Run the Python script
    ctx.actions.run(
        inputs = ctx.files.srcs + [script],
        outputs = [ctx.outputs.out],
        executable = "python3",
        arguments = [script.path] + [args],
        mnemonic = "GenerateReport",
        progress_message = "Generating %s report for %s" % (ctx.attr.report_type, ctx.label.name),
    )

    return [DefaultInfo(files = depset([ctx.outputs.out]))]

generate_report = rule(
    implementation = _generate_report_impl,
    attrs = {
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
            doc = "Standard name for compliance reports (e.g., 'ISO 26262', 'DO-178C')",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:generate_report.py"),
            allow_single_file = True,
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
