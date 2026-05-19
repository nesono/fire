"""Bazel rules for release readiness reporting."""

load("//fire/starlark:fire_rule_utils.bzl", "run_python_script")

def _release_report_impl(ctx):
    """Implementation of the release_report rule."""

    args = ctx.actions.args()
    args.add("--out")
    args.add(ctx.outputs.out.path)
    args.add("--product")
    args.add(ctx.attr.product)

    # Pass config file if provided
    if ctx.file.config:
        args.add("--config", ctx.file.config.path)

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

    config_inputs = [ctx.file.config] if ctx.file.config else []

    run_python_script(
        ctx,
        script = ctx.executable._script,
        script_target = ctx.attr._script,
        args = args,
        extra_inputs = requirement_files + param_files + trace_files + config_inputs,
        outputs = [ctx.outputs.out],
        mnemonic = "ReleaseReport",
        progress_message = "Generating release report for %s" % ctx.label.name,
    )

    return [DefaultInfo(files = depset([ctx.outputs.out]))]

release_report = rule(
    implementation = _release_report_impl,
    attrs = {
        "config": attr.label(
            allow_single_file = [".yaml", ".yml"],
            doc = "Optional fire_config.yaml for custom document types",
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
            product = "Brake Controller",
            out = "RELEASE_REPORT.md",
        )
    """,
)

def _release_readiness_test_impl(ctx):
    """Implementation of the release_readiness_test rule."""

    script = ctx.executable._script
    report = ctx.file.report

    # Create a test script that runs the validation
    test_script = ctx.actions.declare_file(ctx.label.name + "_test.sh")
    ctx.actions.write(
        output = test_script,
        content = """#!/bin/bash
set -e
{script} {report}
""".format(
            script = script.short_path,
            report = report.short_path,
        ),
        is_executable = True,
    )

    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    runfiles = ctx.runfiles(files = [report, script] + script_runfiles)

    return [DefaultInfo(
        executable = test_script,
        runfiles = runfiles,
    )]

release_readiness_test = rule(
    implementation = _release_readiness_test_impl,
    test = True,
    attrs = {
        "report": attr.label(
            allow_single_file = [".md"],
            mandatory = True,
            doc = "The release_report target to validate",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:validate_release_readiness_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = """Tests that a release report indicates the product is ready for release.

    This test reads the generated release report and fails if it contains
    "NOT READY FOR RELEASE", printing the issues that need to be addressed.

    Example:
        release_report(
            name = "release_report",
            requirements = glob(["requirements/*.md"]),
            params = glob(["params/*.yaml"]),
            source_traces = [":brake_controller_trace"],
            product = "Brake Controller",
            out = "RELEASE_REPORT.md",
        )

        release_readiness_test(
            name = "release_readiness",
            report = ":release_report",
        )

    Then run:
        bazel build :release_report  # Generate the report
        bazel test :release_readiness  # Validate readiness
    """,
)
