"""Python code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_python_files(items: list[dict]) -> list[tuple[str, str]]:
    """Generate per-parameter-version Python files.

    Returns list of (relative_path, content) tuples.
    Includes an __init__.py so the directory is a proper Python package.
    """
    files = [("__init__.py", "")]
    for item in items:
        filename = f"{item['base_name']}_v{item['version']}.py"
        content = render_template("python_single.py.j2", item=item)
        files.append((filename, content))
    return files
