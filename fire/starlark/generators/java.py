"""Java code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template, pascal_case


def generate_java_files(
    items: list[dict],
    namespace: str = "",
) -> list[tuple[str, str]]:
    """Generate per-parameter-version Java files.

    Returns list of (relative_path, content) tuples.
    """
    files = []
    for item in items:
        class_name = pascal_case(item["base_name"]) + "V" + str(item["version"])
        filename = f"{class_name}.java"
        content = render_template(
            "java_single.java.j2",
            item=item,
            namespace=namespace,
            class_name=class_name,
        )
        files.append((filename, content))
    return files
