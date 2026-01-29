"""Go code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_go(param_data: dict) -> str:
    """Generate Go package from parameter data."""
    namespace = param_data["namespace"]
    parameters = param_data["parameters"]

    # Get package name from last component of namespace
    package_name = namespace.split(".")[-1]

    return render_template(
        "go.go.j2",
        parameters=parameters,
        package_name=package_name,
    )
