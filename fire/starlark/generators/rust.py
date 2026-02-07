"""Rust code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_rust_files(items: list[dict]) -> list[tuple[str, str]]:
    """Generate per-parameter-version Rust files.

    Returns list of (relative_path, content) tuples.
    """
    files = []
    for item in items:
        filename = f"{item['base_name']}_v{item['version']}.rs"
        content = render_template("rust.rs.j2", item=item)
        files.append((filename, content))
    return files
