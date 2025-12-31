"""Java code generator for Fire parameters."""

from fire.starlark.generators.base import (
    get_type,
    pascal_case,
    camel_case,
    format_value,
)

# Templates for Java code generation
HEADER_WITH_PACKAGE_TEMPLATE = """\
// This file is auto-generated. Do not edit manually.
package ${namespace};

/**
 * Generated parameter definitions with version checking.
 */
public final class ${class_name} {

    private ${class_name}() {
        // Utility class, no instantiation
    }

"""

HEADER_NO_PACKAGE_TEMPLATE = """\
// This file is auto-generated. Do not edit manually.

/**
 * Generated parameter definitions with version checking.
 */
public final class ${class_name} {

    private ${class_name}() {
        // Utility class, no instantiation
    }

"""

TABLE_RECORD_TEMPLATE = """\
    public record ${record_name}(${fields}) {}

    private static final ${record_name}[] ${const_name}_DATA = new ${record_name}[] {
${rows}
    };

"""

TABLE_ACCESSOR_TEMPLATE = """\
    /**
     * Access ${param_name} with version check (current version: ${version}).
     */
    public static ${record_name}[] ${param_name}(int expectedVersion) {
        if (expectedVersion > ${version}) {
            throw new IllegalArgumentException(
                "Parameter ${param_name} version ${version} is older than expected version " + expectedVersion);
        }
        if (expectedVersion < ${version}) {
            System.err.println("Warning: Parameter ${param_name} has been updated to version ${version}, expected " + expectedVersion);
        }
        return ${const_name}_DATA;
    }

"""

SIMPLE_VALUE_STRING_TEMPLATE = """\
    private static final ${java_type} ${const_name}_VALUE = "${value}";

"""

SIMPLE_VALUE_TEMPLATE = """\
    private static final ${java_type} ${const_name}_VALUE = ${value};

"""

SIMPLE_ACCESSOR_TEMPLATE = """\
    /**
     * Access ${param_name} with version check (current version: ${version}).
     */
    public static ${java_type} ${param_name}(int expectedVersion) {
        if (expectedVersion > ${version}) {
            throw new IllegalArgumentException(
                "Parameter ${param_name} version ${version} is older than expected version " + expectedVersion);
        }
        if (expectedVersion < ${version}) {
            System.err.println("Warning: Parameter ${param_name} has been updated to version ${version}, expected " + expectedVersion);
        }
        return ${const_name}_VALUE;
    }

"""

FOOTER_TEMPLATE = """\
}
"""


def generate_java(param_data: dict) -> str:
    """Generate Java class from parameter data."""
    namespace = param_data["namespace"]
    parameters = param_data["parameters"]
    class_name = param_data.get("class_name", "Parameters")

    # Choose header template based on namespace
    if namespace:
        header = HEADER_WITH_PACKAGE_TEMPLATE.replace("${namespace}", namespace)
    else:
        header = HEADER_NO_PACKAGE_TEMPLATE
    output = [header.replace("${class_name}", class_name)]

    # Generate records and accessors
    for param in parameters:
        param_name = param["name"]
        method_name = camel_case(param_name)
        param_type = param["type"]
        const_name = param_name.upper()
        version = param.get("version", 1)

        if param_type == "table":
            record_name = pascal_case(param_name) + "Row"
            rows = param["rows"]
            columns = param["columns"]

            # Generate record fields (camelCase)
            fields = []
            for col in columns:
                java_type = get_type("java", col["type"])
                fields.append(f"{java_type} {camel_case(col['name'])}")

            # Generate data rows
            row_strs = []
            for row in rows:
                values = []
                for i, col in enumerate(columns):
                    values.append(format_value(col["type"], row[i], "java"))
                row_strs.append(f"        new {record_name}({', '.join(values)}),")

            output.append(
                TABLE_RECORD_TEMPLATE.replace("${record_name}", record_name)
                .replace("${fields}", ", ".join(fields))
                .replace("${const_name}", const_name)
                .replace("${rows}", "\n".join(row_strs))
            )

            output.append(
                TABLE_ACCESSOR_TEMPLATE.replace("${param_name}", method_name)
                .replace("${record_name}", record_name)
                .replace("${const_name}", const_name)
                .replace("${version}", str(version))
            )
        else:
            # Simple parameter
            value = param["value"]
            java_type = get_type("java", param_type)

            if param_type == "string":
                output.append(
                    SIMPLE_VALUE_STRING_TEMPLATE.replace("${java_type}", java_type)
                    .replace("${const_name}", const_name)
                    .replace("${value}", str(value))
                )
            elif param_type == "bool":
                bool_val = "true" if value else "false"
                output.append(
                    SIMPLE_VALUE_TEMPLATE.replace("${java_type}", java_type)
                    .replace("${const_name}", const_name)
                    .replace("${value}", bool_val)
                )
            else:
                output.append(
                    SIMPLE_VALUE_TEMPLATE.replace("${java_type}", java_type)
                    .replace("${const_name}", const_name)
                    .replace("${value}", str(value))
                )

            output.append(
                SIMPLE_ACCESSOR_TEMPLATE.replace("${param_name}", method_name)
                .replace("${java_type}", java_type)
                .replace("${const_name}", const_name)
                .replace("${version}", str(version))
            )

    output.append(FOOTER_TEMPLATE)

    return "".join(output)
