"""Java code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_java_files(
    items: list[dict],
    namespace: str = "",
    class_name: str = "Params",
) -> list[tuple[str, str]]:
    """Generate a single Java file containing all parameter versions.

    Returns list of (relative_path, content) tuples with one aggregated file.
    """
    files = []

    # Generate single aggregated class containing all parameters
    filename = f"{class_name}.java"
    content = render_template(
        "java_all.java.j2",
        items=items,
        namespace=namespace,
        class_name=class_name,
    )
    files.append((filename, content))

    return files
