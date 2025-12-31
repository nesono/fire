"""Python code generator for Fire parameters."""

from fire.starlark.generators.base import get_type, pascal_case

# Templates for Python code generation
HEADER_TEMPLATE = '''\
"""Generated parameter constants with version checking."""

from dataclasses import dataclass
import warnings

'''

TABLE_DATACLASS_TEMPLATE = """\
@dataclass(frozen=True)
class ${class_name}:
${fields}

"""

TABLE_DATA_TEMPLATE = """\
_${const_name}_DATA = [
${rows}
]

"""

TABLE_ACCESSOR_TEMPLATE = '''\
def ${param_name}(expected_version: int) -> list[${class_name}]:
    """Access ${param_name} with version check (current version: ${version})."""
    if expected_version > ${version}:
        raise RuntimeError(
            f"Parameter ${param_name} version ${version} is older than expected version {expected_version}"
        )
    if expected_version < ${version}:
        warnings.warn(
            f"Parameter ${param_name} has been updated to version ${version}, expected {expected_version}",
            DeprecationWarning,
            stacklevel=2
        )
    return _${const_name}_DATA

'''

SIMPLE_VALUE_TEMPLATE = """\
_${const_name}_VALUE = ${value}

"""

SIMPLE_ACCESSOR_TEMPLATE = '''\
def ${param_name}(expected_version: int) -> ${py_type}:
    """Access ${param_name} with version check (current version: ${version})."""
    if expected_version > ${version}:
        raise RuntimeError(
            f"Parameter ${param_name} version ${version} is older than expected version {expected_version}"
        )
    if expected_version < ${version}:
        warnings.warn(
            f"Parameter ${param_name} has been updated to version ${version}, expected {expected_version}",
            DeprecationWarning,
            stacklevel=2
        )
    return _${const_name}_VALUE

'''


def generate_python(param_data: dict) -> str:
    """Generate Python module from parameter data."""
    parameters = param_data["parameters"]

    output = [HEADER_TEMPLATE]

    # Generate dataclasses for tables
    for param in parameters:
        if param["type"] == "table":
            class_name = pascal_case(param["name"]) + "Row"
            fields = []
            for col in param["columns"]:
                py_type = get_type("python", col["type"])
                fields.append(f"    {col['name']}: {py_type}")

            output.append(
                TABLE_DATACLASS_TEMPLATE.replace("${class_name}", class_name).replace(
                    "${fields}", "\n".join(fields)
                )
            )

    # Generate data and accessors
    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        const_name = param_name.upper()
        version = param.get("version", 1)

        if param_type == "table":
            class_name = pascal_case(param_name) + "Row"
            rows = param["rows"]
            columns = param["columns"]

            # Generate data
            row_strs = []
            for row in rows:
                values = []
                for i, col in enumerate(columns):
                    val = row[i]
                    if col["type"] == "string":
                        values.append(f'{col["name"]}="{val}"')
                    else:
                        values.append(f'{col["name"]}={val}')
                row_strs.append(f"    {class_name}({', '.join(values)}),")

            output.append(
                TABLE_DATA_TEMPLATE.replace("${const_name}", const_name).replace(
                    "${rows}", "\n".join(row_strs)
                )
            )

            output.append(
                TABLE_ACCESSOR_TEMPLATE.replace("${param_name}", param_name)
                .replace("${class_name}", class_name)
                .replace("${const_name}", const_name)
                .replace("${version}", str(version))
            )
        else:
            # Simple parameter
            value = param["value"]
            py_type = get_type("python", param_type)

            if param_type == "string":
                value_str = f'"{value}"'
            else:
                value_str = str(value)

            output.append(
                SIMPLE_VALUE_TEMPLATE.replace("${const_name}", const_name).replace(
                    "${value}", value_str
                )
            )

            output.append(
                SIMPLE_ACCESSOR_TEMPLATE.replace("${param_name}", param_name)
                .replace("${py_type}", py_type)
                .replace("${const_name}", const_name)
                .replace("${version}", str(version))
            )

    return "".join(output)
