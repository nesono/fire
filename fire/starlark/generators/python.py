"""Python code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_python(param_data: dict) -> str:
    """Generate Python module from parameter data."""
    return render_template("python.py.j2", parameters=param_data["parameters"])
