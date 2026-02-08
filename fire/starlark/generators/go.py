"""Go code generator for Fire parameters."""

from fire.starlark.generators.generator_common import generate_files_per_item


def generate_go_files(
    items: list[dict],
    package_name: str = "",
) -> list[tuple[str, str]]:
    """Generate per-parameter-version Go files in a single package.

    All files share the same Go package name (derived from the output directory).
    Variable names include version suffixes to avoid conflicts.
    Returns list of (relative_path, content) tuples.
    """
    return generate_files_per_item(
        items,
        "go.go.j2",
        lambda item: f"{item['base_name']}_v{item['version']}.go",
        lambda item: {"package_name": package_name},
    )
