"""Rust code generation for parameters."""

def _generate_rust_value(param):
    """Generate Rust value representation.

    Args:
        param: Parameter dictionary

    Returns:
        String representation of the value in Rust syntax
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
        # Ensure float has decimal point for Rust
        val_str = str(float(value))
        if "." not in val_str and "e" not in val_str.lower():
            val_str += ".0"
        return val_str
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

def _to_screaming_snake_case(snake_str):
    """Convert snake_case to SCREAMING_SNAKE_CASE.

    Args:
        snake_str: String in snake_case

    Returns:
        String in SCREAMING_SNAKE_CASE
    """
    return snake_str.upper()

def _generate_table_struct(param, struct_name):
    """Generate Rust struct for table parameter.

    Args:
        param: Table parameter dictionary
        struct_name: Name for the struct

    Returns:
        List of lines for the struct definition
    """
    lines = []
    columns = param.get("columns", [])
    rows = param.get("rows", [])

    # Generate struct with derives
    lines.append("/// {}".format(param.get("description", "")))
    lines.append("#[derive(Debug, Clone, Copy)]")
    lines.append("pub struct {} {{".format(struct_name))

    # Generate fields
    for col in columns:
        col_name = col["name"]
        col_type = col["type"]
        unit = col.get("unit", "")

        # Map types
        if col_type == "float":
            rust_type = "f64"
        elif col_type == "integer":
            rust_type = "i32"
        elif col_type == "string":
            rust_type = "&'static str"
        elif col_type == "boolean":
            rust_type = "bool"
        else:
            rust_type = "String"

        unit_comment = "  // Unit: {}".format(unit) if unit else ""
        lines.append("    pub {}: {},{}".format(col_name, rust_type, unit_comment))

    lines.append("}")
    lines.append("")

    # Generate data constant
    const_name = _to_screaming_snake_case(param["name"])
    lines.append("/// {} table data".format(param.get("description", "")))
    lines.append("pub const {}: &[{}] = &[".format(const_name, struct_name))

    for row in rows:
        values = []
        for i, col in enumerate(columns):
            val = row[i]
            col_type = col["type"]
            col_name = col["name"]

            if col_type == "string":
                escaped = str(val).replace("\\", "\\\\").replace("\"", "\\\"")
                values.append("{}: \"{}\"".format(col_name, escaped))
            elif col_type == "boolean":
                values.append("{}: {}".format(col_name, "true" if val else "false"))
            elif col_type == "float":
                val_str = str(float(val))
                if "." not in val_str and "e" not in val_str.lower():
                    val_str += ".0"
                values.append("{}: {}".format(col_name, val_str))
            else:
                values.append("{}: {}".format(col_name, str(val)))

        lines.append("    {} {{ {} }},".format(struct_name, ", ".join(values)))

    lines.append("];")
    lines.append("")

    # Generate size constant
    size_const_name = "{}_SIZE".format(const_name)
    lines.append("/// Number of entries in {}".format(const_name))
    lines.append("pub const {}: usize = {};".format(size_const_name, len(rows)))
    lines.append("")

    return lines

def generate_rust_code(_namespace, parameters, source_label = None):
    """Generate Rust module with parameters.

    Args:
        _namespace: Namespace (not used in Rust generation, kept for API consistency)
        parameters: List of parameter dictionaries
        source_label: Optional Bazel label for traceability

    Returns:
        Rust module content as string
    """
    lines = []

    # Header
    lines.append("// This file is auto-generated. Do not edit manually.")
    if source_label:
        lines.append("// Generated from: {}".format(source_label))
    lines.append("")

    # Generate simple parameters
    for param in parameters:
        if param["type"] != "table":
            name = _to_screaming_snake_case(param["name"])
            value_str = _generate_rust_value(param)
            unit = param.get("unit", "")
            description = param.get("description", "")

            # Add doc comment
            lines.append("/// {}".format(description))
            if unit:
                lines.append("/// Unit: {}".format(unit))

            rust_type = _get_rust_type(param["type"])
            lines.append("pub const {}: {} = {};".format(name, rust_type, value_str))
            lines.append("")

    # Generate table structs
    for param in parameters:
        if param["type"] == "table":
            struct_name = _to_pascal_case(param["name"]) + "Row"
            table_lines = _generate_table_struct(param, struct_name)
            lines.extend(table_lines)

    return "\n".join(lines)

def _get_rust_type(param_type):
    """Get Rust type for parameter type.

    Args:
        param_type: Parameter type string

    Returns:
        Rust type string
    """
    if param_type == "float":
        return "f64"
    elif param_type == "integer":
        return "i32"
    elif param_type == "string":
        return "&'static str"
    elif param_type == "boolean":
        return "bool"
    return "String"

# Export generator
rust_generator = struct(
    generate = generate_rust_code,
)
