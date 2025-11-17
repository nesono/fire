#!/usr/bin/env python3
"""Generate code from parameter JSON file."""

import json
import sys
from pathlib import Path

# Import existing generators
sys.path.insert(0, str(Path(__file__).parent))

def load_starlark_module(module_path):
    """Load a Starlark module and extract its generate function."""
    # For now, we'll inline the logic here since we can't directly import Starlark
    # We'll call the existing generator .bzl files indirectly
    pass

def main():
    if len(sys.argv) < 4:
        print("Usage: generate_code.py <json_file> <language> <output_file> [--namespace=...]", file=sys.stderr)
        sys.exit(1)

    json_file = sys.argv[1]
    language = sys.argv[2]
    output_file = sys.argv[3]

    # Parse optional arguments
    cpp_namespace = None
    for arg in sys.argv[4:]:
        if arg.startswith("--namespace="):
            cpp_namespace = arg.split("=", 1)[1]

    # Read JSON parameter data
    with open(json_file, 'r') as f:
        param_data = json.load(f)

    # Generate code based on language
    if language == "cpp":
        code = generate_cpp(param_data, cpp_namespace=cpp_namespace)
    elif language == "python":
        code = generate_python(param_data)
    elif language == "go":
        code = generate_go(param_data)
    elif language == "rust":
        code = generate_rust(param_data)
    elif language == "java":
        code = generate_java(param_data)
    else:
        print(f"Unsupported language: {language}", file=sys.stderr)
        sys.exit(1)

    # Write output
    with open(output_file, 'w') as f:
        f.write(code)

def generate_cpp(param_data, cpp_namespace=None):
    """Generate C++ header from parameter data.

    Args:
        param_data: Parameter data dictionary from JSON
        cpp_namespace: Optional C++ namespace override (e.g., "outer::inner")
                      If None, uses the namespace from param_data.
                      If empty string, no namespace is used.
    """
    parameters = param_data["parameters"]
    source_label = param_data.get("source_label", "")

    # Determine namespace to use
    if cpp_namespace is None:
        # Use the namespace from param_data, converted from dots to ::
        namespace = param_data["namespace"].replace(".", "::")
    else:
        # Use the explicitly provided namespace (could be empty)
        namespace = cpp_namespace

    # Create include guard
    if namespace:
        guard_name = namespace.upper().replace("::", "_") + "_PARAMS_H"
    else:
        # Use source label or generic name for guard
        guard_base = source_label.replace("//", "").replace("/", "_").replace(":", "_") if source_label else "GENERATED"
        guard_name = guard_base.upper() + "_PARAMS_H"

    lines = []
    lines.append(f"#ifndef {guard_name}")
    lines.append(f"#define {guard_name}")
    lines.append("")
    lines.append("#include <cstddef>  // for size_t")
    lines.append("")

    # Only add namespace declaration if namespace is provided
    if namespace:
        lines.append(f"namespace {namespace} {{")
        lines.append("")

    # Generate constants for simple parameters and struct definitions for tables
    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        description = param.get("description", "")
        unit = param.get("unit", "")

        # Add documentation comment
        if description:
            doc = description
            if unit:
                doc += f" - Unit: {unit}"
            lines.append(f"/// {doc}")

        if param_type == "table":
            # Generate struct for table
            columns = param["columns"]
            struct_name = "".join(word.capitalize() for word in param_name.split("_")) + "Row"

            lines.append(f"struct {struct_name} {{")
            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                col_unit = col.get("unit", "")
                cpp_type = _get_cpp_type(col_type)

                if col_unit:
                    lines.append(f"    /// Unit: {col_unit}")
                lines.append(f"    {cpp_type} {col_name};")
            lines.append("};")
            lines.append("")

            if description:
                lines.append(f"/// {description}")

            # Generate array constant
            const_name = param_name.upper()
            lines.append(f"constexpr {struct_name} {const_name}[] = {{")

            rows = param["rows"]
            for row in rows:
                # rows are arrays, not dicts
                values = []
                for i, col in enumerate(columns):
                    val = row[i]
                    if col["type"] == "string":
                        values.append(f'"{val}"')
                    elif col["type"] == "bool":
                        values.append("true" if val else "false")
                    else:
                        values.append(str(val))
                lines.append(f"    {{{', '.join(values)}}},")
            lines.append("};")
            lines.append("")

            # Add size constant
            lines.append(f"constexpr size_t {const_name}_SIZE = {len(rows)};")

        else:
            # Simple parameter
            value = param["value"]
            cpp_type = _get_cpp_type(param_type)
            const_name = param_name.upper()

            if param_type == "string":
                lines.append(f"constexpr const char* {const_name} = \"{value}\";")
            elif param_type in ["bool", "boolean"]:
                bool_val = "true" if value else "false"
                lines.append(f"constexpr {cpp_type} {const_name} = {bool_val};")
            else:
                lines.append(f"constexpr {cpp_type} {const_name} = {value};")

        lines.append("")

    # Only close namespace if one was opened
    if namespace:
        lines.append(f"}}  // namespace {namespace}")
        lines.append("")

    lines.append(f"#endif  // {guard_name}")
    lines.append("")

    return "\n".join(lines)

def _get_cpp_type(param_type):
    """Map parameter type to C++ type."""
    type_map = {
        "float": "double",
        "int": "int",
        "integer": "int",
        "string": "const char*",
        "bool": "bool",
        "boolean": "bool",
    }
    return type_map.get(param_type, param_type)

def generate_python(param_data):
    """Generate Python module from parameter data."""
    namespace = param_data["namespace"]
    parameters = param_data["parameters"]
    source_label = param_data.get("source_label", "")

    lines = []
    lines.append('"""Generated parameter constants."""')
    lines.append("")
    lines.append("from dataclasses import dataclass")
    lines.append("")

    # Generate dataclasses for tables
    for param in parameters:
        if param["type"] == "table":
            param_name = param["name"]
            columns = param["columns"]

            class_name = "".join(word.capitalize() for word in param_name.split("_")) + "Row"
            lines.append("@dataclass(frozen=True)")
            lines.append(f"class {class_name}:")

            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                py_type = _get_python_type(col_type)
                lines.append(f"    {col_name}: {py_type}")

            lines.append("")

    # Generate constants
    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        const_name = param_name.upper()

        if param_type == "table":
            class_name = "".join(word.capitalize() for word in param_name.split("_")) + "Row"
            rows = param["rows"]
            columns = param["columns"]

            lines.append(f"{const_name}_DATA = [")
            for row in rows:
                # rows are arrays, not dicts
                values = []
                for i, col in enumerate(columns):
                    val = row[i]
                    if col["type"] == "string":
                        values.append(f'{col["name"]}="{val}"')
                    else:
                        values.append(f'{col["name"]}={val}')
                lines.append(f"    {class_name}({', '.join(values)}),")
            lines.append("]")
        else:
            value = param["value"]
            if param_type == "string":
                lines.append(f'{const_name} = "{value}"')
            else:
                lines.append(f"{const_name} = {value}")

        lines.append("")

    return "\n".join(lines)

def _get_python_type(param_type):
    """Map parameter type to Python type."""
    type_map = {
        "float": "float",
        "int": "int",
        "integer": "int",
        "string": "str",
        "bool": "bool",
        "boolean": "bool",
    }
    return type_map.get(param_type, param_type)

def generate_go(param_data):
    """Generate Go package from parameter data."""
    namespace = param_data["namespace"]
    parameters = param_data["parameters"]

    # Get package name from last component of namespace
    package_name = namespace.split(".")[-1]

    lines = []
    lines.append(f"package {package_name}")
    lines.append("")

    # Generate structs for tables
    for param in parameters:
        if param["type"] == "table":
            param_name = param["name"]
            columns = param["columns"]

            struct_name = "".join(word.capitalize() for word in param_name.split("_")) + "Row"
            lines.append(f"type {struct_name} struct {{")

            for col in columns:
                col_name = "".join(word.capitalize() for word in col["name"].split("_"))
                col_type = col["type"]
                go_type = _get_go_type(col_type)
                lines.append(f"    {col_name} {go_type}")

            lines.append("}")
            lines.append("")

    # Generate constants
    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        const_name = "".join(word.capitalize() for word in param_name.split("_"))

        if param_type == "table":
            struct_name = "".join(word.capitalize() for word in param_name.split("_")) + "Row"
            rows = param["rows"]
            columns = param["columns"]

            lines.append(f"var {const_name} = []{struct_name}{{")
            for row in rows:
                # rows are arrays, not dicts
                values = []
                for i, col in enumerate(columns):
                    col_name = "".join(word.capitalize() for word in col["name"].split("_"))
                    val = row[i]
                    if col["type"] == "string":
                        values.append(f'{col_name}: "{val}"')
                    else:
                        values.append(f"{col_name}: {val}")
                lines.append(f"    {{{', '.join(values)}}},")
            lines.append("}")
        else:
            value = param["value"]
            if param_type == "string":
                lines.append(f'const {const_name} = "{value}"')
            elif param_type in ["bool", "boolean"]:
                bool_val = "true" if value else "false"
                lines.append(f"const {const_name} = {bool_val}")
            else:
                lines.append(f"const {const_name} = {value}")

        lines.append("")

    return "\n".join(lines)

def _get_go_type(param_type):
    """Map parameter type to Go type."""
    type_map = {
        "float": "float64",
        "int": "int",
        "integer": "int",
        "string": "string",
        "bool": "bool",
        "boolean": "bool",
    }
    return type_map.get(param_type, param_type)

def generate_rust(param_data):
    """Generate Rust module from parameter data."""
    namespace = param_data["namespace"]
    parameters = param_data["parameters"]

    lines = []
    lines.append("// Generated parameter constants")
    lines.append("")

    # Generate structs for tables
    for param in parameters:
        if param["type"] == "table":
            param_name = param["name"]
            columns = param["columns"]

            struct_name = "".join(word.capitalize() for word in param_name.split("_")) + "Row"
            lines.append("#[derive(Debug, Clone, Copy)]")
            lines.append(f"pub struct {struct_name} {{")

            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                rust_type = _get_rust_type(col_type)
                lines.append(f"    pub {col_name}: {rust_type},")

            lines.append("}")
            lines.append("")

    # Generate constants
    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        const_name = param_name.upper()

        if param_type == "table":
            struct_name = "".join(word.capitalize() for word in param_name.split("_")) + "Row"
            rows = param["rows"]
            columns = param["columns"]

            lines.append(f"pub const {const_name}: [{struct_name}; {len(rows)}] = [")
            for row in rows:
                # rows are arrays, not dicts
                values = []
                for i, col in enumerate(columns):
                    col_name = col["name"]
                    val = row[i]
                    if col["type"] == "string":
                        values.append(f'{col_name}: "{val}"')
                    else:
                        values.append(f"{col_name}: {val}")
                lines.append(f"    {struct_name} {{ {', '.join(values)} }},")
            lines.append("];")
        else:
            value = param["value"]
            rust_type = _get_rust_type(param_type)
            if param_type == "string":
                lines.append(f'pub const {const_name}: &str = "{value}";')
            else:
                lines.append(f"pub const {const_name}: {rust_type} = {str(value).lower()};")

        lines.append("")

    # Add size constants for tables
    for param in parameters:
        if param["type"] == "table":
            const_name = param["name"].upper()
            lines.append(f"pub const {const_name}_SIZE: usize = {len(param['rows'])};")
            lines.append("")

    return "\n".join(lines)

def _get_rust_type(param_type):
    """Map parameter type to Rust type."""
    type_map = {
        "float": "f64",
        "int": "i32",
        "integer": "i32",
        "string": "&'static str",
        "bool": "bool",
        "boolean": "bool",
    }
    return type_map.get(param_type, param_type)

def generate_java(param_data):
    """Generate Java class from parameter data."""
    namespace = param_data["namespace"]
    parameters = param_data["parameters"]
    source_label = param_data.get("source_label", "")

    # Extract class name from source label or use default
    # Source label format: //package:target_name
    class_name = "Parameters"
    if source_label and ":" in source_label:
        target_name = source_label.split(":")[-1]
        # Convert to PascalCase
        class_name = "".join(word.capitalize() for word in target_name.split("_"))

    lines = []
    lines.append("// This file is auto-generated. Do not edit manually.")
    if source_label:
        lines.append(f"// Generated from: {source_label}")
    lines.append(f"package {namespace};")
    lines.append("")
    lines.append("/**")
    lines.append(" * Generated parameter definitions.")
    lines.append(" */")
    lines.append(f"public final class {class_name} {{")
    lines.append("")
    lines.append(f"    private {class_name}() {{")
    lines.append("        // Utility class, no instantiation")
    lines.append("    }")
    lines.append("")

    # Generate record classes for tables first
    for param in parameters:
        if param["type"] == "table":
            param_name = param["name"]
            columns = param["columns"]
            description = param.get("description", "")

            # Record class name
            record_name = "".join(word.capitalize() for word in param_name.split("_")) + "Row"

            if description:
                lines.append("    /**")
                lines.append(f"     * {description}")
                lines.append("     */")

            # Build record fields (convert to camelCase)
            fields = []
            for col in columns:
                col_name_parts = col["name"].split("_")
                camel_name = col_name_parts[0] + "".join(word.capitalize() for word in col_name_parts[1:])
                col_type = col["type"]
                java_type = _get_java_type(col_type)
                fields.append(f"{java_type} {camel_name}")

            lines.append(f"    public record {record_name}({', '.join(fields)}) {{}}")
            lines.append("")

    # Generate constants
    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        description = param.get("description", "")
        unit = param.get("unit", "")
        const_name = param_name.upper()

        if param_type == "table":
            # Generate array of records
            record_name = "".join(word.capitalize() for word in param_name.split("_")) + "Row"
            rows = param["rows"]
            columns = param["columns"]

            lines.append(f"    public static final {record_name}[] {const_name} = {{")
            for row in rows:
                # rows are arrays, not dicts
                values = []
                for i, col in enumerate(columns):
                    val = row[i]
                    if col["type"] == "string":
                        values.append(f'"{val}"')
                    elif col["type"] in ["bool", "boolean"]:
                        values.append("true" if val else "false")
                    else:
                        values.append(str(val))
                lines.append(f"        new {record_name}({', '.join(values)}),")
            lines.append("    };")
        else:
            # Simple constant
            value = param["value"]
            java_type = _get_java_type(param_type)

            # Add documentation
            if description or unit:
                lines.append("    /**")
                if description:
                    lines.append(f"     * {description}")
                if unit:
                    lines.append(f"     * Unit: {unit}")
                lines.append("     */")

            if param_type == "string":
                lines.append(f'    public static final {java_type} {const_name} = "{value}";')
            elif param_type in ["bool", "boolean"]:
                bool_val = "true" if value else "false"
                lines.append(f"    public static final {java_type} {const_name} = {bool_val};")
            else:
                lines.append(f"    public static final {java_type} {const_name} = {value};")

        lines.append("")

    lines.append("}")
    lines.append("")

    return "\n".join(lines)

def _get_java_type(param_type):
    """Map parameter type to Java type."""
    type_map = {
        "float": "double",
        "int": "int",
        "integer": "int",
        "string": "String",
        "bool": "boolean",
        "boolean": "boolean",
    }
    return type_map.get(param_type, param_type)

if __name__ == "__main__":
    main()
