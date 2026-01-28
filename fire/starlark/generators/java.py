"""Java code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_java(param_data: dict) -> str:
    """Generate Java class from parameter data."""
    namespace = param_data["namespace"]
    parameters = param_data["parameters"]
    class_name = param_data.get("class_name", "Parameters")

    return render_template(
        "java.java.j2",
        parameters=parameters,
        namespace=namespace,
        class_name=class_name,
    )
