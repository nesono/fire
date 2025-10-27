"""C++ code generation."""

def _to_pascal_case(snake_case):
    """Convert snake_case to PascalCase."""
    parts = snake_case.split("_")
    return "".join([part.capitalize() for part in parts])

def _format_cpp_value(value, param_type):
    """Format a value for C++ code."""
    if param_type == "float":
        # Ensure float formatting
        return str(float(value))
    elif param_type == "integer":
        return str(value)
    elif param_type == "string":
        # Escape special characters
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return '"{}"'.format(escaped)
    elif param_type == "boolean":
        return "true" if value else "false"
    else:
        fail("Unknown parameter type: {}".format(param_type))

def _get_cpp_type(param_type):
    """Get C++ type for parameter type."""
    type_map = {
        "boolean": "bool",
        "float": "double",
        "integer": "int",
        "string": "const char*",
    }
    return type_map.get(param_type, "unknown")

def _generate_header_guard(namespace):
    """Generate header guard name from namespace."""
    return namespace.replace(".", "_").upper() + "_PARAMS_H"

def _generate_namespace_open(namespace):
    """Generate namespace opening statements."""
    lines = []
    parts = namespace.split(".")
    for part in parts:
        lines.append("namespace {} {{".format(part))
    return lines

def _generate_namespace_close(namespace):
    """Generate namespace closing statements."""
    lines = []
    parts = namespace.split(".")
    for part in reversed(parts):
        lines.append("}} // namespace {}".format(part))
    return lines

def _generate_simple_parameter(param):
    """Generate C++ code for a simple (non-table) parameter."""
    lines = []

    param_name = param["name"]
    param_type = param["type"]
    value = param["value"]
    description = param.get("description", "")
    unit = param.get("unit", "")

    # Generate documentation comment
    comment_parts = []
    if description:
        comment_parts.append(description)
    if unit:
        comment_parts.append("Unit: {}".format(unit))

    if comment_parts:
        lines.append("/// {}".format(" - ".join(comment_parts)))

    # Generate declaration
    cpp_type = _get_cpp_type(param_type)
    cpp_value = _format_cpp_value(value, param_type)
    lines.append("constexpr {} {} = {};".format(cpp_type, param_name, cpp_value))

    return lines

def _generate_table_parameter(param):
    """Generate C++ code for a table parameter."""
    lines = []

    param_name = param["name"]
    description = param.get("description", "")
    columns = param["columns"]
    rows = param["rows"]

    # Generate struct name
    struct_name = _to_pascal_case(param_name) + "Row"

    # Generate struct definition
    lines.append("struct {} {{".format(struct_name))

    for col in columns:
        col_name = col["name"]
        col_type = col["type"]
        cpp_type = _get_cpp_type(col_type)
        col_unit = col.get("unit", "")

        # Add field documentation
        if col_unit:
            lines.append("    /// Unit: {}".format(col_unit))

        lines.append("    {} {};".format(cpp_type, col_name))

    lines.append("};")
    lines.append("")

    # Generate array declaration
    if description:
        lines.append("/// {}".format(description))
    lines.append("constexpr {} {}[] = {{".format(struct_name, param_name))

    # Generate rows
    for row in rows:
        row_values = []
        for cell, col in zip(row, columns):
            formatted_value = _format_cpp_value(cell, col["type"])
            row_values.append(formatted_value)

        lines.append("    {{{}}},".format(", ".join(row_values)))

    lines.append("};")
    lines.append("")

    # Generate size constant
    lines.append("/// Number of rows in {}".format(param_name))
    lines.append("constexpr size_t {}_size = {};".format(param_name, len(rows)))

    return lines

def _generate_parameter(param):
    """Generate C++ code for a single parameter."""
    if param["type"] == "table":
        return _generate_table_parameter(param)
    else:
        return _generate_simple_parameter(param)

def generate_cpp_header(param_data):
    """Generate C++ header file content from parameter data.

    Args:
        param_data: Dictionary with validated parameter data

    Returns:
        String containing C++ header file content
    """
    lines = []

    namespace = param_data["namespace"]
    parameters = param_data["parameters"]

    # Generate header guard
    header_guard = _generate_header_guard(namespace)
    lines.append("#ifndef {}".format(header_guard))
    lines.append("#define {}".format(header_guard))
    lines.append("")

    # Add includes
    lines.append("#include <cstddef>  // for size_t")
    lines.append("")

    # Generate namespace opening
    lines.extend(_generate_namespace_open(namespace))
    lines.append("")

    # Generate parameters
    for param in parameters:
        lines.extend(_generate_parameter(param))
        lines.append("")

    # Generate namespace closing
    lines.extend(_generate_namespace_close(namespace))
    lines.append("")

    # Close header guard
    lines.append("#endif // {}".format(header_guard))

    return "\n".join(lines)

# Export generator function
cpp_generator = struct(
    generate = generate_cpp_header,
)
