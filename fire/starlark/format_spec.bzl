"""Bazel rule for generating FORMAT_SPECIFICATION.md from FIRE config."""

def _generate_format_specification_impl(ctx):
    """Implementation of the format specification generator rule."""
    script = ctx.executable._script
    args = ctx.actions.args()
    args.add("--out", ctx.outputs.out.path)

    config_inputs = []
    if ctx.file.config:
        args.add("--config", ctx.file.config.path)
        config_inputs = [ctx.file.config]

    script_runfiles = ctx.attr._script[DefaultInfo].default_runfiles.files.to_list()

    ctx.actions.run(
        inputs = config_inputs + [script] + script_runfiles,
        outputs = [ctx.outputs.out],
        executable = script,
        arguments = [args],
        mnemonic = "GenerateFormatSpec",
        progress_message = "Generating format specification for %s" % ctx.label.name,
    )

    return [DefaultInfo(files = depset([ctx.outputs.out]))]

generate_format_specification = rule(
    implementation = _generate_format_specification_impl,
    attrs = {
        "config": attr.label(
            allow_single_file = [".yaml", ".yml"],
            doc = "Optional fire_config.yaml for custom document types",
        ),
        "out": attr.output(
            mandatory = True,
            doc = "Output markdown file (e.g., FORMAT_SPECIFICATION.md)",
        ),
        "_script": attr.label(
            default = Label("//fire/starlark:generate_format_spec_script"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = """Generates a FORMAT_SPECIFICATION.md from FIRE configuration.

    Example:
        generate_format_specification(
            name = "format_spec",
            config = ":fire_config.yaml",
            out = "FORMAT_SPECIFICATION.md",
        )
    """,
)
