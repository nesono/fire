"""C++ code generator for Fire parameters."""

from fire.starlark.generators.generator_common import generate_files_per_item


def generate_cpp_files(
    items: list[dict],
    cpp_namespace: str = "",
    package_path: str = "",
) -> list[tuple[str, str]]:
    """Generate per-parameter-version C++ header files.

    Returns list of (relative_path, content) tuples.
    """

    def context_builder(item: dict) -> dict:
        """Build context for C++ header."""
        return {"namespace": cpp_namespace or ""}

    return generate_files_per_item(
        items,
        "cpp.hpp.j2",
        lambda item: f"{item['base_name']}_v{item['version']}.h",
        context_builder,
    )
