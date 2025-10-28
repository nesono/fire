"""Python code generation for parameters."""

def _generate_python_value(param):
    """Generate Python value representation.

    Args:
        param: Parameter dictionary

    Returns:
        String representation of the value in Python syntax
    """
    param_type = param["type"]
    value = param.get("value", None)

    if param_type == "string":
        # Escape quotes in string values
        escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
        return "\"{}\"".format(escaped)
    elif param_type == "boolean":
        return "True" if value else "False"
    elif param_type == "float":
        return str(float(value))
    elif param_type == "integer":
        return str(int(value))
    elif param_type == "table":
        return None  # Tables handled separately

    return None

def _generate_table_class(param, class_name):
    """Generate Python dataclass for table parameter.

    Args:
        param: Table parameter dictionary
        class_name: Name for the dataclass

    Returns:
        List of lines for the dataclass definition
    """
    lines = []
    columns = param.get("columns", [])
    rows = param.get("rows", [])

    # Generate dataclass
    lines.append("@dataclasses.dataclass(frozen=True)")
    lines.append("class {}:".format(class_name))
    lines.append("    \"\"\"{}\"\"\"".format(param.get("description", "")))

    # Generate fields
    for col in columns:
        col_name = col["name"]
        col_type = col["type"]
        unit = col.get("unit", "")

        # Map types
        if col_type == "float":
            py_type = "float"
        elif col_type == "integer":
            py_type = "int"
        elif col_type == "string":
            py_type = "str"
        elif col_type == "boolean":
            py_type = "bool"
        else:
            py_type = "Any"

        unit_comment = "  # Unit: {}".format(unit) if unit else ""
        lines.append("    {}: {}{}".format(col_name, py_type, unit_comment))

    lines.append("")

    # Generate data list
    lines.append("")
    lines.append("{}_DATA: typing.List[{}] = [".format(param["name"].upper(), class_name))

    for row in rows:
        values = []
        for i, col in enumerate(columns):
            val = row[i]
            col_type = col["type"]

            if col_type == "string":
                escaped = str(val).replace("\\", "\\\\").replace("\"", "\\\"")
                values.append("\"{}\"".format(escaped))
            elif col_type == "boolean":
                values.append("True" if val else "False")
            else:
                values.append(str(val))

        lines.append("    {}({}),".format(class_name, ", ".join(values)))

    lines.append("]")
    lines.append("")

    return lines

def _to_pascal_case(snake_str):
    """Convert snake_case to PascalCase.

    Args:
        snake_str: String in snake_case

    Returns:
        String in PascalCase
    """
    components = snake_str.split("_")
    return "".join([c.capitalize() for c in components])

def generate_python_code(_namespace, parameters, source_label = None):
    """Generate Python module with parameters.

    Args:
        _namespace: Module namespace (not used in Python generation, kept for API consistency)
        parameters: List of parameter dictionaries
        source_label: Optional Bazel label for traceability

    Returns:
        Python module content as string
    """
    lines = []

    # Header
    lines.append("\"\"\"Generated parameter definitions.\"\"\"")
    lines.append("# This file is auto-generated. Do not edit manually.")
    if source_label:
        lines.append("# Generated from: {}".format(source_label))
    lines.append("")
    lines.append("import dataclasses")
    lines.append("import typing")
    lines.append("from typing import Any, List")
    lines.append("")
    lines.append("")

    # Generate simple parameters
    for param in parameters:
        if param["type"] != "table":
            name = param["name"]
            value_str = _generate_python_value(param)
            unit = param.get("unit", "")
            description = param.get("description", "")

            # Add docstring comment
            lines.append("# {}".format(description))
            if unit:
                lines.append("# Unit: {}".format(unit))

            lines.append("{}: {} = {}".format(
                name.upper(),
                _get_python_type(param["type"]),
                value_str,
            ))
            lines.append("")

    # Generate table classes
    for param in parameters:
        if param["type"] == "table":
            class_name = _to_pascal_case(param["name"]) + "Row"
            table_lines = _generate_table_class(param, class_name)
            lines.extend(table_lines)

    return "\n".join(lines)

def _get_python_type(param_type):
    """Get Python type annotation for parameter type.

    Args:
        param_type: Parameter type string

    Returns:
        Python type annotation
    """
    if param_type == "float":
        return "float"
    elif param_type == "integer":
        return "int"
    elif param_type == "string":
        return "str"
    elif param_type == "boolean":
        return "bool"
    return "Any"

# Export generator
python_generator = struct(
    generate = generate_python_code,
)
