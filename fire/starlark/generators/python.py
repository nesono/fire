"""Python code generator for Fire parameters."""

from fire.starlark.generators.generator_common import generate_files_per_item


def generate_python_files(items: list[dict]) -> list[tuple[str, str]]:
    """Generate per-parameter-version Python files.

    Returns list of (relative_path, content) tuples.
    Includes an __init__.py so the directory is a proper Python package.
    """
    return generate_files_per_item(
        items,
        "python.py.j2",
        lambda item: f"{item['base_name']}_v{item['version']}.py",
    )
