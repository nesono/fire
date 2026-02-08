"""Rust code generator for Fire parameters."""

from fire.starlark.generators.generator_common import generate_file_aggregate


def generate_rust_files(items: list[dict]) -> list[tuple[str, str]]:
    """Generate a single Rust file containing all parameter versions.

    Returns list of (relative_path, content) tuples.
    """
    return generate_file_aggregate(items, "rust_all.rs.j2", "lib.rs")
