"""C++ code generator for Fire parameters."""

from fire.starlark.generators.base import get_type, pascal_case, format_value

# Templates for C++ code generation
HEADER_TEMPLATE = """\
#ifndef ${guard_name}
#define ${guard_name}

#include <cstddef>  // for size_t
#include <cstdint>  // for int32_t, int64_t, uint32_t, uint64_t

"""

NAMESPACE_OPEN = "namespace ${namespace} {\n"
NAMESPACE_CLOSE = "}  // namespace ${namespace}\n"

TABLE_STRUCT_TEMPLATE = """\
struct ${struct_name} {
${fields}
};

"""

TABLE_DATA_TEMPLATE = """\
namespace detail {
constexpr ${struct_name} ${const_name}_DATA[] = {
${rows}
};
}  // namespace detail

constexpr size_t ${const_name}_SIZE = ${size};

"""

TABLE_ACCESSOR_TEMPLATE = """\
/// ${description}
/// Access ${param_name} with version check (current version: ${version})
template<int ExpectedVersion>
[[deprecated("Parameter ${param_name} has been updated to version ${version}")]]
constexpr const ${struct_name}* ${param_name}_outdated() {
    return detail::${const_name}_DATA;
}

template<int ExpectedVersion>
[[nodiscard]] constexpr const ${struct_name}* ${param_name}() {
    if constexpr (ExpectedVersion > ${version}) {
        static_assert(ExpectedVersion <= ${version},
            "Parameter ${param_name} version ${version} is older than expected version");
        return nullptr;  // Never reached
    } else if constexpr (ExpectedVersion < ${version}) {
        return ${param_name}_outdated<ExpectedVersion>();
    } else {
        return detail::${const_name}_DATA;
    }
}

constexpr size_t ${param_name}_size() {
    return ${const_name}_SIZE;
}

"""

TABLE_ACCESSOR_V1_TEMPLATE = """\
/// ${description}
/// Access ${param_name} with version check (current version: ${version})
template<int ExpectedVersion>
[[nodiscard]] constexpr const ${struct_name}* ${param_name}() {
    static_assert(ExpectedVersion <= ${version},
        "Parameter ${param_name} version ${version} is older than expected version");
    return detail::${const_name}_DATA;
}

constexpr size_t ${param_name}_size() {
    return ${const_name}_SIZE;
}

"""

SIMPLE_VALUE_TEMPLATE = """\
namespace detail { constexpr ${cpp_type} ${const_name}_VALUE = ${value}; }

"""

SIMPLE_ACCESSOR_TEMPLATE = """\
/// ${description}
template<int ExpectedVersion>
[[deprecated("Parameter ${param_name} has been updated to version ${version}")]]
constexpr ${cpp_type} ${param_name}_outdated() {
    return detail::${const_name}_VALUE;
}

/// Access ${param_name} with version check (current version: ${version})
template<int ExpectedVersion>
[[nodiscard]] constexpr ${cpp_type} ${param_name}() {
    if constexpr (ExpectedVersion > ${version}) {
        static_assert(ExpectedVersion <= ${version},
            "Parameter ${param_name} version ${version} is older than expected version");
        return {};  // Never reached
    } else if constexpr (ExpectedVersion < ${version}) {
        return ${param_name}_outdated<ExpectedVersion>();
    } else {
        return detail::${const_name}_VALUE;
    }
}

"""

SIMPLE_ACCESSOR_V1_TEMPLATE = """\
/// ${description}
/// Access ${param_name} with version check (current version: ${version})
template<int ExpectedVersion>
[[nodiscard]] constexpr ${cpp_type} ${param_name}() {
    static_assert(ExpectedVersion <= ${version},
        "Parameter ${param_name} version ${version} is older than expected version");
    return detail::${const_name}_VALUE;
}

"""

FOOTER_TEMPLATE = "#endif  // ${guard_name}\n"


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
        # Use repository-relative path to create unique guard
        if output_file and package_path:
            # Extract base filename without path and extension
            import os

            base_name = os.path.basename(output_file)
            # Remove extension
            if base_name.endswith(".h"):
                base_name = base_name[:-2]

            # Construct path: package_path/base_name
            repo_path = package_path + "/" + base_name if package_path else base_name
            guard_name = (
                repo_path.upper().replace("/", "_").replace(".", "_").replace("-", "_")
                + "_H"
            )
        else:
            guard_name = "GENERATED_PARAMS_H"

    output = []

    # Header
    output.append(HEADER_TEMPLATE.replace("${guard_name}", guard_name))

    # Namespace open
    if namespace:
        output.append(NAMESPACE_OPEN.replace("${namespace}", namespace))
        output.append("")

    # Generate structs for tables
    for param in parameters:
        if param["type"] == "table":
            struct_name = pascal_case(param["name"]) + "Row"
            fields = []
            for col in param["columns"]:
                cpp_type = get_type("cpp", col["type"])
                unit_comment = f"  ///< Unit: {col['unit']}" if col.get("unit") else ""
                fields.append(f"    {cpp_type} {col['name']};{unit_comment}")

            output.append(
                TABLE_STRUCT_TEMPLATE.replace("${struct_name}", struct_name).replace(
                    "${fields}", "\n".join(fields)
                )
            )

    # Generate constants and accessors
    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        const_name = param_name.upper()
        version = param.get("version", 1)
        description = param.get("description", "")
        unit = param.get("unit", "")

        if unit:
            description += f" - Unit: {unit}"

        if param_type == "table":
            struct_name = pascal_case(param_name) + "Row"
            rows = param["rows"]
            columns = param["columns"]

            # Generate data array
            row_strs = []
            for row in rows:
                values = []
                for i, col in enumerate(columns):
                    values.append(format_value(col["type"], row[i], "cpp"))
                row_strs.append(f"    {{{', '.join(values)}}},")

            output.append(
                TABLE_DATA_TEMPLATE.replace("${struct_name}", struct_name)
                .replace("${const_name}", const_name)
                .replace("${rows}", "\n".join(row_strs))
                .replace("${size}", str(len(rows)))
            )

            # Generate accessor
            template = (
                TABLE_ACCESSOR_TEMPLATE if version > 1 else TABLE_ACCESSOR_V1_TEMPLATE
            )
            output.append(
                template.replace("${struct_name}", struct_name)
                .replace("${param_name}", param_name)
                .replace("${const_name}", const_name)
                .replace("${version}", str(version))
                .replace("${description}", description)
            )
        else:
            # Simple parameter
            cpp_type = get_type("cpp", param_type)
            value = format_value(param_type, param["value"], "cpp")

            output.append(
                SIMPLE_VALUE_TEMPLATE.replace("${cpp_type}", cpp_type)
                .replace("${const_name}", const_name)
                .replace("${value}", value)
            )

            template = (
                SIMPLE_ACCESSOR_TEMPLATE if version > 1 else SIMPLE_ACCESSOR_V1_TEMPLATE
            )
            output.append(
                template.replace("${cpp_type}", cpp_type)
                .replace("${param_name}", param_name)
                .replace("${const_name}", const_name)
                .replace("${version}", str(version))
                .replace("${description}", description)
            )

    # Namespace close
    if namespace:
        output.append(NAMESPACE_CLOSE.replace("${namespace}", namespace))
        output.append("")

    # Footer
    output.append(FOOTER_TEMPLATE.replace("${guard_name}", guard_name))

    return "".join(output)
