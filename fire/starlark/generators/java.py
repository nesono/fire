"""Java code generator for Fire parameters."""

from fire.starlark.generators.generator_common import generate_file_aggregate


def generate_java_files(
    items: list[dict],
    namespace: str = "",
    class_name: str = "Params",
) -> list[tuple[str, str]]:
    """Generate a single Java file containing all parameter versions.

    Returns list of (relative_path, content) tuples with one aggregated file.
    """
    return generate_file_aggregate(
        items,
        "java_all.java.j2",
        f"{class_name}.java",
        {"namespace": namespace, "class_name": class_name},
    )
