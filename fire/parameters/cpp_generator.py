"""C++ code generator for parameter files."""

from typing import Any, Dict, List


class CppGenerator:
    """Generates C++ header files from parameter data."""

    # Type mapping from parameter types to C++ types
    TYPE_MAP = {
        "float": "double",
        "integer": "int",
        "string": "const char*",
        "boolean": "bool",
    }

    def generate(self, param_data: Dict[str, Any]) -> str:
        """
        Generate C++ header file content from parameter data.

        Args:
            param_data: Validated parameter data

        Returns:
            C++ header file content as a string
        """
        namespace = param_data["namespace"]
        parameters = param_data["parameters"]

        lines = []

        # Generate header guard
        header_guard = self._generate_header_guard(namespace)
        lines.append(f"#ifndef {header_guard}")
        lines.append(f"#define {header_guard}")
        lines.append("")

        # Add includes
        lines.append("#include <cstddef>  // for size_t")
        lines.append("")

        # Generate namespace opening
        namespace_parts = namespace.split(".")
        for part in namespace_parts:
            lines.append(f"namespace {part} {{")
        lines.append("")

        # Generate parameters
        for param in parameters:
            self._generate_parameter(param, lines)
            lines.append("")

        # Generate namespace closing
        for part in reversed(namespace_parts):
            lines.append(f"}} // namespace {part}")
        lines.append("")

        # Close header guard
        lines.append(f"#endif // {header_guard}")

        return "\n".join(lines)

    def _generate_header_guard(self, namespace: str) -> str:
        """Generate header guard name from namespace."""
        # Convert namespace to uppercase with underscores
        guard = namespace.replace(".", "_").upper() + "_PARAMS_H"
        return guard

    def _generate_parameter(self, param: Dict[str, Any], lines: List[str]) -> None:
        """Generate C++ code for a single parameter."""
        param_type = param["type"]
        param_name = param["name"]
        description = param.get("description", "")
        unit = param.get("unit", "")

        # Generate documentation comment
        comment_parts = []
        if description:
            comment_parts.append(description)
        if unit:
            comment_parts.append(f"Unit: {unit}")

        if comment_parts:
            lines.append(f"/// {' - '.join(comment_parts)}")

        if param_type == "table":
            self._generate_table_parameter(param, lines)
        else:
            self._generate_simple_parameter(param, lines)

    def _generate_simple_parameter(
        self, param: Dict[str, Any], lines: List[str]
    ) -> None:
        """Generate C++ code for a simple (non-table) parameter."""
        param_type = param["type"]
        param_name = param["name"]
        value = param["value"]

        cpp_type = self.TYPE_MAP[param_type]
        cpp_value = self._format_value(value, param_type)

        lines.append(f"constexpr {cpp_type} {param_name} = {cpp_value};")

    def _generate_table_parameter(
        self, param: Dict[str, Any], lines: List[str]
    ) -> None:
        """Generate C++ code for a table parameter."""
        param_name = param["name"]
        columns = param["columns"]
        rows = param["rows"]

        # Generate struct name (capitalize first letter of each word)
        struct_name = self._to_pascal_case(param_name) + "Row"

        # Generate struct definition
        lines.append(f"struct {struct_name} {{")

        for col in columns:
            col_name = col["name"]
            col_type = col["type"]
            cpp_type = self.TYPE_MAP[col_type]

            # Add field documentation
            col_unit = col.get("unit", "")
            if col_unit:
                lines.append(f"    /// Unit: {col_unit}")

            lines.append(f"    {cpp_type} {col_name};")

        lines.append("};")
        lines.append("")

        # Generate array declaration
        lines.append(f"/// {param['description']}")
        lines.append(f"constexpr {struct_name} {param_name}[] = {{")

        for row in rows:
            row_values = []
            for cell, col in zip(row, columns):
                formatted_value = self._format_value(cell, col["type"])
                row_values.append(formatted_value)

            lines.append(f"    {{{', '.join(row_values)}}},")

        lines.append("};")
        lines.append("")

        # Generate size constant
        lines.append(f"/// Number of rows in {param_name}")
        lines.append(f"constexpr size_t {param_name}_size = {len(rows)};")

    def _format_value(self, value: Any, param_type: str) -> str:
        """Format a value for C++ code."""
        if param_type == "float":
            # Ensure float formatting
            if isinstance(value, int):
                return f"{float(value)}"
            return str(value)
        elif param_type == "integer":
            return str(value)
        elif param_type == "string":
            # Escape special characters and wrap in quotes
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        elif param_type == "boolean":
            return "true" if value else "false"
        else:
            raise ValueError(f"Unknown parameter type: {param_type}")

    def _to_pascal_case(self, snake_case: str) -> str:
        """Convert snake_case to PascalCase."""
        parts = snake_case.split("_")
        return "".join(part.capitalize() for part in parts)
