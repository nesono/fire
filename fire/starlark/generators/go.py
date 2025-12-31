"""Go code generator for Fire parameters."""

from fire.starlark.generators.base import get_type, pascal_case, format_value

# Templates for Go code generation
HEADER_TEMPLATE = """\
package ${package_name}

import (
    "fmt"
)

"""

TABLE_STRUCT_TEMPLATE = """\
type ${struct_name} struct {
${fields}
}

"""

TABLE_DATA_TEMPLATE = """\
var ${const_name_lower}Data = []${struct_name}{
${rows}
}

"""

TABLE_ACCESSOR_TEMPLATE = """\
// ${param_name_pascal} returns ${param_name} with version check (current version: ${version})
func ${param_name_pascal}(expectedVersion int) []${struct_name} {
    if expectedVersion > ${version} {
        panic(fmt.Sprintf("Parameter ${param_name} version ${version} is older than expected version %d", expectedVersion))
    }
    if expectedVersion < ${version} {
        fmt.Printf("Warning: Parameter ${param_name} has been updated to version ${version}, expected %d\\n", expectedVersion)
    }
    return ${const_name_lower}Data
}

"""

SIMPLE_VALUE_TEMPLATE_STRING = """\
var ${const_name_lower}Value = "${value}"

"""

SIMPLE_VALUE_TEMPLATE_BOOL = """\
var ${const_name_lower}Value = ${value}

"""

SIMPLE_VALUE_TEMPLATE_NUMERIC = """\
var ${const_name_lower}Value ${go_type} = ${value}

"""

SIMPLE_ACCESSOR_TEMPLATE = """\
// ${param_name_pascal} returns ${param_name} with version check (current version: ${version})
func ${param_name_pascal}(expectedVersion int) ${go_type} {
    if expectedVersion > ${version} {
        panic(fmt.Sprintf("Parameter ${param_name} version ${version} is older than expected version %d", expectedVersion))
    }
    if expectedVersion < ${version} {
        fmt.Printf("Warning: Parameter ${param_name} has been updated to version ${version}, expected %d\\n", expectedVersion)
    }
    return ${const_name_lower}Value
}

"""


def generate_go(param_data: dict) -> str:
    """Generate Go package from parameter data."""
    namespace = param_data["namespace"]
    parameters = param_data["parameters"]

    # Get package name from last component of namespace
    package_name = namespace.split(".")[-1]

    output = [HEADER_TEMPLATE.replace("${package_name}", package_name)]

    # Generate structs for tables
    for param in parameters:
        if param["type"] == "table":
            struct_name = pascal_case(param["name"]) + "Row"
            fields = []
            for col in param["columns"]:
                go_type = get_type("go", col["type"])
                field_name = pascal_case(col["name"])
                fields.append(f"    {field_name} {go_type}")

            output.append(
                TABLE_STRUCT_TEMPLATE.replace("${struct_name}", struct_name).replace(
                    "${fields}", "\n".join(fields)
                )
            )

    # Generate data and accessors
    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        const_name = param_name.upper()
        version = param.get("version", 1)
        param_name_pascal = pascal_case(param_name)

        if param_type == "table":
            struct_name = pascal_case(param_name) + "Row"
            rows = param["rows"]
            columns = param["columns"]

            # Generate data
            row_strs = []
            for row in rows:
                values = []
                for i, col in enumerate(columns):
                    field_name = pascal_case(col["name"])
                    val = format_value(col["type"], row[i], "go")
                    values.append(f"{field_name}: {val}")
                row_strs.append(f"    {{{', '.join(values)}}},")

            output.append(
                TABLE_DATA_TEMPLATE.replace("${const_name_lower}", const_name.lower())
                .replace("${struct_name}", struct_name)
                .replace("${rows}", "\n".join(row_strs))
            )

            output.append(
                TABLE_ACCESSOR_TEMPLATE.replace("${param_name}", param_name)
                .replace("${param_name_pascal}", param_name_pascal)
                .replace("${struct_name}", struct_name)
                .replace("${const_name_lower}", const_name.lower())
                .replace("${version}", str(version))
            )
        else:
            # Simple parameter
            value = param["value"]
            go_type = get_type("go", param_type)

            if param_type == "string":
                output.append(
                    SIMPLE_VALUE_TEMPLATE_STRING.replace(
                        "${const_name_lower}", const_name.lower()
                    ).replace("${value}", str(value))
                )
            elif param_type == "bool":
                bool_val = "true" if value else "false"
                output.append(
                    SIMPLE_VALUE_TEMPLATE_BOOL.replace(
                        "${const_name_lower}", const_name.lower()
                    ).replace("${value}", bool_val)
                )
            else:
                output.append(
                    SIMPLE_VALUE_TEMPLATE_NUMERIC.replace(
                        "${const_name_lower}", const_name.lower()
                    )
                    .replace("${go_type}", go_type)
                    .replace("${value}", str(value))
                )

            output.append(
                SIMPLE_ACCESSOR_TEMPLATE.replace("${param_name}", param_name)
                .replace("${param_name_pascal}", param_name_pascal)
                .replace("${go_type}", go_type)
                .replace("${const_name_lower}", const_name.lower())
                .replace("${version}", str(version))
            )

    return "".join(output)
