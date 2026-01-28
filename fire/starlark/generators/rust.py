"""Rust code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_rust(param_data: dict) -> str:
    """Generate Rust module from parameter data."""
    return render_template("rust.rs.j2", parameters=param_data["parameters"])
