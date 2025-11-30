"""Rust code generator for Fire parameters."""

from fire.starlark.generators.base import get_type, pascal_case, format_value

# Templates for Rust code generation
HEADER_TEMPLATE = """\
// Generated parameter constants with version checking

"""

TABLE_STRUCT_TEMPLATE = """\
#[derive(Debug, Clone, Copy)]
pub struct ${struct_name} {
${fields}
}

"""

TABLE_DATA_TEMPLATE = """\
const ${const_name}_DATA: [${struct_name}; ${size}] = [
${rows}
];

pub const ${const_name}_SIZE: usize = ${size};

"""

TABLE_ACCESSOR_TEMPLATE = """\
/// Access ${param_name} with version check (current version: ${version})
#[deprecated(note = "Parameter ${param_name} has been updated to version ${version}")]
const fn ${param_name}_outdated() -> &'static [${struct_name}; ${size}] {
    &${const_name}_DATA
}

pub const fn ${param_name}<const EXPECTED_VERSION: i32>() -> &'static [${struct_name}; ${size}] {
    const { assert!(EXPECTED_VERSION <= ${version}, "Parameter ${param_name} version ${version} is older than expected version"); }

    if EXPECTED_VERSION <= ${version_minus} {
        ${param_name}_outdated()
    } else {
        &${const_name}_DATA
    }
}

"""

TABLE_ACCESSOR_V1_TEMPLATE = """\
/// Access ${param_name} with version check (current version: ${version})
pub const fn ${param_name}<const EXPECTED_VERSION: i32>() -> &'static [${struct_name}; ${size}] {
    assert!(EXPECTED_VERSION <= ${version}, "Parameter ${param_name} version ${version} is older than expected version");
    &${const_name}_DATA
}

"""

SIMPLE_VALUE_STRING_TEMPLATE = """\
const ${const_name}_VALUE: &str = "${value}";

"""

SIMPLE_VALUE_TEMPLATE = """\
const ${const_name}_VALUE: ${rust_type} = ${value};

"""

SIMPLE_ACCESSOR_TEMPLATE = """\
/// Access ${param_name} with version check (current version: ${version})
#[deprecated(note = "Parameter ${param_name} has been updated to version ${version}")]
const fn ${param_name}_outdated() -> ${rust_type} {
    ${const_name}_VALUE
}

pub const fn ${param_name}<const EXPECTED_VERSION: i32>() -> ${rust_type} {
    const { assert!(EXPECTED_VERSION <= ${version}, "Parameter ${param_name} version ${version} is older than expected version"); }

    if EXPECTED_VERSION <= ${version_minus} {
        ${param_name}_outdated()
    } else {
        ${const_name}_VALUE
    }
}

"""

SIMPLE_ACCESSOR_V1_TEMPLATE = """\
/// Access ${param_name} with version check (current version: ${version})
pub const fn ${param_name}<const EXPECTED_VERSION: i32>() -> ${rust_type} {
    assert!(EXPECTED_VERSION <= ${version}, "Parameter ${param_name} version ${version} is older than expected version");
    ${const_name}_VALUE
}

"""


def generate_rust(param_data: dict) -> str:
    """Generate Rust module from parameter data."""
    parameters = param_data["parameters"]

    output = [HEADER_TEMPLATE]

    # Generate structs for tables
    for param in parameters:
        if param["type"] == "table":
            struct_name = pascal_case(param["name"]) + "Row"
            fields = []
            for col in param["columns"]:
                rust_type = get_type("rust", col["type"])
                fields.append(f"    pub {col['name']}: {rust_type},")

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

        if param_type == "table":
            struct_name = pascal_case(param_name) + "Row"
            rows = param["rows"]
            columns = param["columns"]

            # Generate data
            row_strs = []
            for row in rows:
                values = []
                for i, col in enumerate(columns):
                    val = format_value(col["type"], row[i], "rust")
                    values.append(f"{col['name']}: {val}")
                row_strs.append(f"    {struct_name} {{ {', '.join(values)} }},")

            output.append(
                TABLE_DATA_TEMPLATE.replace("${struct_name}", struct_name)
                .replace("${const_name}", const_name)
                .replace("${rows}", "\n".join(row_strs))
                .replace("${size}", str(len(rows)))
            )

            # Accessor
            if version > 1:
                output.append(
                    TABLE_ACCESSOR_TEMPLATE.replace("${struct_name}", struct_name)
                    .replace("${param_name}", param_name)
                    .replace("${const_name}", const_name)
                    .replace("${version}", str(version))
                    .replace("${version_plus}", str(version + 1))
                    .replace("${version_minus}", str(version - 1))
                    .replace("${size}", str(len(rows)))
                )
            else:
                output.append(
                    TABLE_ACCESSOR_V1_TEMPLATE.replace("${struct_name}", struct_name)
                    .replace("${param_name}", param_name)
                    .replace("${const_name}", const_name)
                    .replace("${version}", str(version))
                    .replace("${size}", str(len(rows)))
                )
        else:
            # Simple parameter
            value = param["value"]
            rust_type = get_type("rust", param_type)

            if param_type == "string":
                output.append(
                    SIMPLE_VALUE_STRING_TEMPLATE.replace(
                        "${const_name}", const_name
                    ).replace("${value}", str(value))
                )
            else:
                formatted_value = (
                    str(value).lower() if param_type == "bool" else str(value)
                )
                output.append(
                    SIMPLE_VALUE_TEMPLATE.replace("${const_name}", const_name)
                    .replace("${rust_type}", rust_type)
                    .replace("${value}", formatted_value)
                )

            # Accessor
            if version > 1:
                output.append(
                    SIMPLE_ACCESSOR_TEMPLATE.replace("${param_name}", param_name)
                    .replace("${const_name}", const_name)
                    .replace("${rust_type}", rust_type)
                    .replace("${version}", str(version))
                    .replace("${version_plus}", str(version + 1))
                    .replace("${version_minus}", str(version - 1))
                )
            else:
                output.append(
                    SIMPLE_ACCESSOR_V1_TEMPLATE.replace("${param_name}", param_name)
                    .replace("${const_name}", const_name)
                    .replace("${rust_type}", rust_type)
                    .replace("${version}", str(version))
                )

    return "".join(output)
