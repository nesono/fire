"""Java code generation for parameters."""

def _generate_java_value(param):
    """Generate Java value representation.

    Args:
        param: Parameter dictionary

    Returns:
        String representation of the value in Java syntax
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
        return "{}".format(float(value))
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

def _to_camel_case(snake_str):
    """Convert snake_case to camelCase.

    Args:
        snake_str: String in snake_case

    Returns:
        String in camelCase
    """
    components = snake_str.split("_")
    return components[0] + "".join([c.capitalize() for c in components[1:]])

def _generate_table_class(param, class_name, indent = "    "):
    """Generate Java record class for table parameter.

    Args:
        param: Table parameter dictionary
        class_name: Name for the record class
        indent: Indentation string

    Returns:
        List of lines for the record class definition
    """
    lines = []
    columns = param.get("columns", [])
    rows = param.get("rows", [])

    # Generate record class
    lines.append("{}/**".format(indent))
    lines.append("{} * {}".format(indent, param.get("description", "")))
    lines.append("{} */".format(indent))

    # Build record fields
    fields = []
    for col in columns:
        col_name = _to_camel_case(col["name"])
        col_type = col["type"]

        # Map types
        if col_type == "float":
            java_type = "double"
        elif col_type == "integer":
            java_type = "int"
        elif col_type == "string":
            java_type = "String"
        elif col_type == "boolean":
            java_type = "boolean"
        else:
            java_type = "Object"

        fields.append("{} {}".format(java_type, col_name))

    lines.append("{}public record {}({}) {{}}".format(
        indent,
        class_name,
        ", ".join(fields),
    ))
    lines.append("")

    # Generate data array
    lines.append("{}public static final {}[] {} = {{".format(
        indent,
        class_name,
        param["name"].upper(),
    ))

    for row in rows:
        values = []
        for i, col in enumerate(columns):
            val = row[i]
            col_type = col["type"]

            if col_type == "string":
                escaped = str(val).replace("\\", "\\\\").replace("\"", "\\\"")
                values.append("\"{}\"".format(escaped))
            elif col_type == "boolean":
                values.append("true" if val else "false")
            elif col_type == "float":
                values.append(str(float(val)))
            else:
                values.append(str(val))

        lines.append("{}    new {}({}),".format(indent, class_name, ", ".join(values)))

    lines.append("{}}};".format(indent))
    lines.append("")

    return lines

def generate_java_code(namespace, parameters, class_name = "Parameters", source_label = None):
    """Generate Java class with parameters.

    Args:
        namespace: Java package namespace (e.g., "com.example.vehicle")
        parameters: List of parameter dictionaries
        class_name: Name of the generated class
        source_label: Optional Bazel label for traceability

    Returns:
        Java class content as string
    """
    lines = []

    # Header
    lines.append("// This file is auto-generated. Do not edit manually.")
    if source_label:
        lines.append("// Generated from: {}".format(source_label))
    lines.append("package {};".format(namespace.replace(".", ".").replace("::", ".")))
    lines.append("")
    lines.append("/**")
    lines.append(" * Generated parameter definitions.")
    lines.append(" */")
    lines.append("public final class {} {{".format(class_name))
    lines.append("")
    lines.append("    private {}() {{".format(class_name))
    lines.append("        // Utility class, no instantiation")
    lines.append("    }")
    lines.append("")

    # Generate simple parameters
    for param in parameters:
        if param["type"] != "table":
            name = param["name"].upper()
            value_str = _generate_java_value(param)
            unit = param.get("unit", "")
            description = param.get("description", "")

            # Add javadoc
            lines.append("    /**")
            lines.append("     * {}".format(description))
            if unit:
                lines.append("     * Unit: {}".format(unit))
            lines.append("     */")

            java_type = _get_java_type(param["type"])
            lines.append("    public static final {} {} = {};".format(
                java_type,
                name,
                value_str,
            ))
            lines.append("")

    # Generate table classes
    for param in parameters:
        if param["type"] == "table":
            record_class_name = _to_pascal_case(param["name"]) + "Row"
            table_lines = _generate_table_class(param, record_class_name)
            lines.extend(table_lines)

    lines.append("}")

    return "\n".join(lines)

def _get_java_type(param_type):
    """Get Java type for parameter type.

    Args:
        param_type: Parameter type string

    Returns:
        Java type string
    """
    if param_type == "float":
        return "double"
    elif param_type == "integer":
        return "int"
    elif param_type == "string":
        return "String"
    elif param_type == "boolean":
        return "boolean"
    return "Object"

# Export generator
java_generator = struct(
    generate = generate_java_code,
)
