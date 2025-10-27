"""Bazel rules for parameter management using pure Starlark - simplified version."""

# Provider to pass parameter information between rules
ParameterInfo = provider(
    doc = "Information about a parameter library",
    fields = {
        "json_file": "The JSON parameter file",
    },
)

def _parameter_library_impl(ctx):
    """Implementation of the parameter_library rule."""
    src = ctx.file.src

    return [
        DefaultInfo(files = depset([src])),
        ParameterInfo(
            json_file = src,
        ),
    ]

parameter_library = rule(
    implementation = _parameter_library_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = [".json"],
            mandatory = True,
            doc = "The parameter JSON file",
        ),
    },
    doc = "Declares a parameter library from a JSON file",
)

def _cc_parameter_library_impl(ctx):
    """Implementation of the cc_parameter_library rule."""

    # Get the parameter library dependency
    param_info = ctx.attr.parameter_library[ParameterInfo]
    json_file = param_info.json_file

    # Create output header file
    header = ctx.actions.declare_file(ctx.attr.name + ".h")

    # Create a generator script that uses our Starlark logic
    generator_script = ctx.actions.declare_file(ctx.attr.name + "_gen.sh")

    # We'll use a Python script to do the actual generation
    # (reading JSON and calling our generator logic)
    generator_code = """#!/bin/bash
python3 - "$@" <<'PYTHON_EOF'
import json
import sys

# Read the JSON file
with open(sys.argv[1], 'r') as f:
    param_data = json.load(f)

# Override namespace if provided
if len(sys.argv) > 3 and sys.argv[3]:
    param_data['namespace'] = sys.argv[3]

# Generate C++ code (inline the logic here)
def to_pascal_case(snake_case):
    parts = snake_case.split('_')
    return ''.join(part.capitalize() for part in parts)

def format_cpp_value(value, param_type):
    if param_type == 'float':
        return str(float(value))
    elif param_type == 'integer':
        return str(value)
    elif param_type == 'string':
        escaped = value.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"')
        return f'"{escaped}"'
    elif param_type == 'boolean':
        return 'true' if value else 'false'

def get_cpp_type(param_type):
    type_map = {
        'float': 'double',
        'integer': 'int',
        'string': 'const char*',
        'boolean': 'bool',
    }
    return type_map.get(param_type, 'unknown')

def generate_header_guard(namespace):
    return namespace.replace('.', '_').upper() + '_PARAMS_H'

def generate_cpp_header(param_data):
    lines = []
    namespace = param_data['namespace']
    parameters = param_data['parameters']

    # Header guard
    header_guard = generate_header_guard(namespace)
    lines.append(f'#ifndef {header_guard}')
    lines.append(f'#define {header_guard}')
    lines.append('')

    # Includes
    lines.append('#include <cstddef>  // for size_t')
    lines.append('')

    # Namespace opening
    for part in namespace.split('.'):
        lines.append(f'namespace {part} {{')
    lines.append('')

    # Generate parameters
    for param in parameters:
        param_type = param['type']
        param_name = param['name']
        description = param.get('description', '')
        unit = param.get('unit', '')

        # Documentation
        comment_parts = []
        if description:
            comment_parts.append(description)
        if unit:
            comment_parts.append(f'Unit: {unit}')
        if comment_parts:
            lines.append(f'/// {" - ".join(comment_parts)}')

        if param_type == 'table':
            # Generate table
            columns = param['columns']
            rows = param['rows']
            struct_name = to_pascal_case(param_name) + 'Row'

            lines.append(f'struct {struct_name} {{')
            for col in columns:
                col_name = col['name']
                col_type = get_cpp_type(col['type'])
                col_unit = col.get('unit', '')
                if col_unit:
                    lines.append(f'    /// Unit: {col_unit}')
                lines.append(f'    {col_type} {col_name};')
            lines.append('};')
            lines.append('')

            lines.append(f'/// {description}')
            lines.append(f'constexpr {struct_name} {param_name}[] = {{')
            for row in rows:
                row_values = [format_cpp_value(cell, col['type'])
                             for cell, col in zip(row, columns)]
                lines.append(f'    {{{", ".join(row_values)}}},')
            lines.append('};')
            lines.append('')
            lines.append(f'/// Number of rows in {param_name}')
            lines.append(f'constexpr size_t {param_name}_size = {len(rows)};')
        else:
            # Simple parameter
            cpp_type = get_cpp_type(param_type)
            cpp_value = format_cpp_value(param['value'], param_type)
            lines.append(f'constexpr {cpp_type} {param_name} = {cpp_value};')

        lines.append('')

    # Namespace closing
    for part in reversed(namespace.split('.')):
        lines.append(f'}} // namespace {part}')
    lines.append('')

    # Close header guard
    lines.append(f'#endif // {header_guard}')

    return '\\n'.join(lines)

# Generate and write
cpp_code = generate_header_guard(param_data)
with open(sys.argv[2], 'w') as f:
    f.write(generate_cpp_header(param_data))

PYTHON_EOF
"""

    ctx.actions.write(
        output = generator_script,
        content = generator_code,
        is_executable = True,
    )

    # Run generator
    args = [json_file.path, header.path]
    if ctx.attr.namespace:
        args.append(ctx.attr.namespace)

    ctx.actions.run(
        inputs = [json_file],
        outputs = [header],
        executable = generator_script,
        arguments = args,
        mnemonic = "GenerateCppParameters",
        progress_message = "Generating C++ header from %s" % json_file.short_path,
    )

    # Create compilation context
    compilation_context = cc_common.create_compilation_context(
        headers = depset([header]),
        includes = depset([header.dirname]),
    )

    cc_info = CcInfo(
        compilation_context = compilation_context,
    )

    return [
        DefaultInfo(files = depset([header])),
        cc_info,
    ]

cc_parameter_library = rule(
    implementation = _cc_parameter_library_impl,
    attrs = {
        "namespace": attr.string(
            doc = "C++ namespace for the generated code (overrides the namespace in the parameter file)",
        ),
        "parameter_library": attr.label(
            mandatory = True,
            providers = [ParameterInfo],
            doc = "The parameter_library target to generate C++ code from",
        ),
    },
    fragments = ["cpp"],
    doc = "Generates a C++ header file from a parameter library",
)
