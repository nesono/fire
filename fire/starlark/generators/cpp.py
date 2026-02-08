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
        """Build context with include guard for C++ header."""
        # Create include guard from package path + filename
        if package_path:
            repo_path = (
                package_path + "/" + item["base_name"] + "_v" + str(item["version"])
            )
        else:
            repo_path = item["base_name"] + "_v" + str(item["version"])
        guard_name = (
            repo_path.upper().replace("/", "_").replace(".", "_").replace("-", "_")
            + "_H"
        )
        return {"namespace": cpp_namespace or "", "guard_name": guard_name}

    return generate_files_per_item(
        items,
        "cpp.hpp.j2",
        lambda item: f"{item['base_name']}_v{item['version']}.h",
        context_builder,
    )
