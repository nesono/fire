"""Rust code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_rust_files(items: list[dict]) -> list[tuple[str, str]]:
    """Generate a single Rust file containing all parameter versions.

    Returns list of (relative_path, content) tuples.
    """
    files = []

    # Generate single lib.rs file with all parameters
    lib_content = render_template("rust_all.rs.j2", items=items)
    files.append(("lib.rs", lib_content))

    return files
