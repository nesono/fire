"""Bazel rule for rendering a FIRE markdown document to a styled PDF.

The action runs the ``render_pdf`` binary with ``no_sandbox`` and the host
shell environment (the same escape hatch as the other FIRE rules) because
WeasyPrint loads native libraries (pango, cairo, harfbuzz) and fonts that must
be provisioned on the host; see the README PDF Export prerequisites.
"""

load("//fire/starlark:fire_rule_utils.bzl", "run_python_script")

def _document_pdf_impl(ctx):
    """Render a single FIRE markdown document to a PDF artifact."""
    srcs = ctx.files.srcs
    if len(srcs) != 1:
        fail(
            "document_pdf renders a single document (multi-file merge is " +
            "deferred); got %d sources" % len(srcs),
        )
    source = srcs[0]

    args = ctx.actions.args()
    args.add(source.short_path)
    args.add("--out", ctx.outputs.out.path)

    extra_inputs = list(srcs)
    if ctx.file.config:
        args.add("--config", ctx.file.config.short_path)
        extra_inputs.append(ctx.file.config)
    for sheet in ctx.files.stylesheets:
        args.add("--stylesheet", sheet.short_path)
    extra_inputs += ctx.files.stylesheets
    if ctx.file.template:
        args.add("--template", ctx.file.template.short_path)
        extra_inputs.append(ctx.file.template)

    run_python_script(
        ctx,
        script = ctx.executable._script,
        script_target = ctx.attr._script,
        args = args,
        extra_inputs = extra_inputs,
        outputs = [ctx.outputs.out],
        mnemonic = "DocumentPdf",
        progress_message = "Rendering PDF for %s" % ctx.label.name,
        use_default_shell_env = True,
        no_sandbox = True,
    )

    return [DefaultInfo(files = depset([ctx.outputs.out]))]

document_pdf = rule(
    implementation = _document_pdf_impl,
    attrs = {
        "config": attr.label(
            allow_single_file = [".yaml", ".yml"],
            doc = "Optional fire_config.yaml; defaults to the embedded config",
        ),
        "out": attr.output(
            mandatory = True,
            doc = "Generated PDF artifact",
        ),
        "srcs": attr.label_list(
            allow_files = [".md"],
            mandatory = True,
            doc = "Markdown document to render (a single document in v1)",
        ),
        "stylesheets": attr.label_list(
            allow_files = [".css"],
            default = [],
            doc = "CSS files cascaded after the FIRE base.css, in order",
        ),
        "template": attr.label(
            allow_single_file = [".j2", ".html"],
            doc = "Optional HTML template overriding the default",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:render_pdf_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = """Renders a FIRE markdown document to a styled PDF via WeasyPrint.

    Example:
        document_pdf(
            name = "braking_pdf",
            srcs = ["braking.sysreq.md"],
            stylesheets = ["//branding:corporate.css"],
            out = "braking.pdf",
        )
    """,
)
