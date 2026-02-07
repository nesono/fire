"""Go code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_go_files(
    items: list[dict],
    package_name: str = "",
) -> list[tuple[str, str]]:
    """Generate per-parameter-version Go files in a single package.

    All files share the same Go package name (derived from the output directory).
    Variable names include version suffixes to avoid conflicts.
    Returns list of (relative_path, content) tuples.
    """
    files = []
    for item in items:
        filename = f"{item['base_name']}_v{item['version']}.go"
        content = render_template(
            "go.go.j2",
            item=item,
            package_name=package_name,
        )
        files.append((filename, content))
    return files
