"""C++ code generator for Fire parameters."""

import os

from fire.starlark.generators.template_loader import render_template


def generate_cpp(
    param_data: dict,
    cpp_namespace: str = "",
    output_file: str = "",
    package_path: str = "",
) -> str:
    """Generate C++ header from parameter data."""
    parameters = param_data["parameters"]

    # Determine namespace
    if cpp_namespace is None:
        namespace = param_data["namespace"].replace(".", "::")
    else:
        namespace = cpp_namespace

    # Create include guard
    if namespace:
        guard_name = namespace.upper().replace("::", "_") + "_PARAMS_H"
    else:
        if output_file and package_path:
            base_name = os.path.basename(output_file)
            if base_name.endswith(".h"):
                base_name = base_name[:-2]
            repo_path = package_path + "/" + base_name if package_path else base_name
            guard_name = (
                repo_path.upper().replace("/", "_").replace(".", "_").replace("-", "_")
                + "_H"
            )
        else:
            guard_name = "GENERATED_PARAMS_H"

    return render_template(
        "cpp.hpp.j2",
        parameters=parameters,
        namespace=namespace,
        guard_name=guard_name,
    )
