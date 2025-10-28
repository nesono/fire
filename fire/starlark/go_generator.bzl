"""Go code generation for parameters."""

def _generate_go_value(param):
    """Generate Go value representation.

    Args:
        param: Parameter dictionary

    Returns:
        String representation of the value in Go syntax
    """
    param_type = param["type"]
    value = param.get("value", None)

    if param_type == "string":
        # Escape quotes and backslashes in string values
        escaped = str(value).replace("\\", "\\\\").replace("\"", "\\\"")
        return "\"{}\"".format(escaped)
    elif param_type == "boolean":
        return "true" if value else "false"
    elif param_type == "float":
        return str(float(value))
    elif param_type == "integer":
        return str(int(value))
    elif param_type == "table":
        return None  # Tables handled separately

    return None

def _to_pascal_case(snake_str):
    """Convert snake_case to PascalCase.

    Args:
        snake_str: String in snake_case

    Returns:
        String in PascalCase
    """
    components = snake_str.split("_")
    return "".join([c.capitalize() for c in components])

def _generate_table_struct(param, struct_name):
    """Generate Go struct for table parameter.

    Args:
        param: Table parameter dictionary
        struct_name: Name for the struct

    Returns:
        List of lines for the struct definition
    """
    lines = []
    columns = param.get("columns", [])
    rows = param.get("rows", [])

    # Generate struct
    lines.append("// {} - {}".format(struct_name, param.get("description", "")))
    lines.append("type {} struct {{".format(struct_name))

    # Generate fields
    for col in columns:
        col_name = _to_pascal_case(col["name"])
        col_type = col["type"]
        unit = col.get("unit", "")

        # Map types
        if col_type == "float":
            go_type = "float64"
        elif col_type == "integer":
            go_type = "int"
        elif col_type == "string":
            go_type = "string"
        elif col_type == "boolean":
            go_type = "bool"
        else:
            go_type = "interface{}"

        unit_comment = " // Unit: {}".format(unit) if unit else ""
        lines.append("    {} {}{}".format(col_name, go_type, unit_comment))

    lines.append("}")
    lines.append("")

    # Generate data slice
    var_name = _to_pascal_case(param["name"])
    lines.append("// {} contains the table data".format(var_name))
    lines.append("var {} = []{} {{".format(var_name, struct_name))

    for row in rows:
        values = []
        for i, col in enumerate(columns):
            val = row[i]
            col_type = col["type"]
            col_name = _to_pascal_case(col["name"])

            if col_type == "string":
                escaped = str(val).replace("\\", "\\\\").replace("\"", "\\\"")
                values.append("{}: \"{}\"".format(col_name, escaped))
            elif col_type == "boolean":
                values.append("{}: {}".format(col_name, "true" if val else "false"))
            else:
                values.append("{}: {}".format(col_name, str(val)))

        lines.append("    {{{}}},".format(", ".join(values)))

    lines.append("}")
    lines.append("")

    return lines

def generate_go_code(_namespace, parameters, package_name = "parameters"):
    """Generate Go package with parameters.

    Args:
        _namespace: Go package namespace (not used in Go generation, kept for API consistency)
        parameters: List of parameter dictionaries
        package_name: Package name for the generated code

    Returns:
        Go package content as string
    """
    lines = []

    # Header
    lines.append("// This file is auto-generated. Do not edit manually.")
    lines.append("package {}".format(package_name))
    lines.append("")

    # Generate simple parameters
    for param in parameters:
        if param["type"] != "table":
            name = _to_pascal_case(param["name"])
            value_str = _generate_go_value(param)
            unit = param.get("unit", "")
            description = param.get("description", "")

            # Add comment
            lines.append("// {} - {}".format(name, description))
            if unit:
                lines.append("// Unit: {}".format(unit))

            go_type = _get_go_type(param["type"])
            lines.append("const {} {} = {}".format(name, go_type, value_str))
            lines.append("")

    # Generate table structs
    for param in parameters:
        if param["type"] == "table":
            struct_name = _to_pascal_case(param["name"]) + "Row"
            table_lines = _generate_table_struct(param, struct_name)
            lines.extend(table_lines)

    return "\n".join(lines)

def _get_go_type(param_type):
    """Get Go type for parameter type.

    Args:
        param_type: Parameter type string

    Returns:
        Go type string
    """
    if param_type == "float":
        return "float64"
    elif param_type == "integer":
        return "int"
    elif param_type == "string":
        return "string"
    elif param_type == "boolean":
        return "bool"
    return "interface{}"

# Export generator
go_generator = struct(
    generate = generate_go_code,
)
