"""C++ code generator for Fire parameters."""

from fire.starlark.generators.template_loader import render_template


def generate_cpp_files(
    items: list[dict],
    cpp_namespace: str = "",
    package_path: str = "",
) -> list[tuple[str, str]]:
    """Generate per-parameter-version C++ header files.

    Returns list of (relative_path, content) tuples.
    """
    # Determine namespace
    namespace = cpp_namespace or ""

    files = []
    for item in items:
        filename = f"{item['base_name']}_v{item['version']}.h"
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
        content = render_template(
            "cpp_single.hpp.j2",
            item=item,
            namespace=namespace,
            guard_name=guard_name,
        )
        files.append((filename, content))
    return files
