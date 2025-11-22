#!/usr/bin/env python3
"""Validates parameter YAML files.

This script reads a parameter YAML file and validates its structure
and content.
"""

import argparse
import json
import os
import re
import sys

import yaml


def load_yaml(yaml_path):
    """Load YAML file."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def validate_table_rows(param_name, param_def):
    """Validate that table rows match column definitions."""
    errors = []
    columns = param_def.get('columns', [])
    rows = param_def.get('rows', [])

    num_columns = len(columns)

    for i, row in enumerate(rows):
        if len(row) != num_columns:
            errors.append(
                f"Parameter '{param_name}': Row {i+1} has {len(row)} values, "
                f"expected {num_columns} (number of columns)"
            )
            continue

        # Validate each value type
        for j, (value, col) in enumerate(zip(row, columns)):
            col_name = col['name']
            col_type = col['type']

            if col_type == 'integer':
                if not isinstance(value, int) or isinstance(value, bool):
                    errors.append(
                        f"Parameter '{param_name}': Row {i+1}, column '{col_name}' "
                        f"expected integer, got {type(value).__name__}"
                    )
            elif col_type == 'float':
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    errors.append(
                        f"Parameter '{param_name}': Row {i+1}, column '{col_name}' "
                        f"expected float, got {type(value).__name__}"
                    )
            elif col_type == 'string':
                if not isinstance(value, str):
                    errors.append(
                        f"Parameter '{param_name}': Row {i+1}, column '{col_name}' "
                        f"expected string, got {type(value).__name__}"
                    )
            elif col_type == 'boolean':
                if not isinstance(value, bool):
                    errors.append(
                        f"Parameter '{param_name}': Row {i+1}, column '{col_name}' "
                        f"expected boolean, got {type(value).__name__}"
                    )

    return errors


def validate_parameter_names(params):
    """Validate parameter names follow naming conventions."""
    errors = []
    import re

    pattern = re.compile(r'^[a-z][a-z0-9_]*$')

    for name in params.keys():
        if not pattern.match(name):
            errors.append(
                f"Parameter name '{name}' is invalid. "
                "Names must start with lowercase letter and contain only "
                "lowercase letters, numbers, and underscores."
            )

    return errors


def validate_parameter_structure(data):
    """Validate the basic structure of parameter data."""
    errors = []

    if not isinstance(data, dict):
        return [f"Expected dictionary, got {type(data).__name__}"]

    if 'parameters' not in data:
        return ["Missing required 'parameters' key"]

    params = data['parameters']
    if not isinstance(params, dict):
        return [f"'parameters' must be a dictionary, got {type(params).__name__}"]

    if len(params) == 0:
        return ["'parameters' must contain at least one parameter"]

    valid_types = ['integer', 'float', 'string', 'boolean', 'table']

    for name, param_def in params.items():
        if not isinstance(param_def, dict):
            errors.append(f"Parameter '{name}' must be a dictionary")
            continue

        # Check required fields
        if 'type' not in param_def:
            errors.append(f"Parameter '{name}' missing required field 'type'")
        elif param_def['type'] not in valid_types:
            errors.append(f"Parameter '{name}' has invalid type '{param_def['type']}', must be one of: {valid_types}")

        if 'description' not in param_def:
            errors.append(f"Parameter '{name}' missing required field 'description'")

        param_type = param_def.get('type')

        # For non-table types, require 'value'
        if param_type != 'table':
            if 'value' not in param_def:
                errors.append(f"Parameter '{name}' missing required field 'value'")
            else:
                # Type check the value
                value = param_def['value']
                if param_type == 'integer' and not isinstance(value, int):
                    errors.append(f"Parameter '{name}' value must be integer, got {type(value).__name__}")
                elif param_type == 'float' and not isinstance(value, (int, float)):
                    errors.append(f"Parameter '{name}' value must be float, got {type(value).__name__}")
                elif param_type == 'string' and not isinstance(value, str):
                    errors.append(f"Parameter '{name}' value must be string, got {type(value).__name__}")
                elif param_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Parameter '{name}' value must be boolean, got {type(value).__name__}")
        else:
            # Table type requires columns and rows
            if 'columns' not in param_def:
                errors.append(f"Parameter '{name}' (table) missing required field 'columns'")
            if 'rows' not in param_def:
                errors.append(f"Parameter '{name}' (table) missing required field 'rows'")

    return errors


def validate_parameters(yaml_path, schema_path=None):
    """Validate parameter YAML file.

    Returns:
        Tuple of (success, errors) where errors is a list of error messages.
    """
    errors = []

    try:
        data = load_yaml(yaml_path)
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML syntax: {e}"]
    except Exception as e:
        return False, [f"Failed to load YAML: {e}"]

    if data is None:
        return False, ["YAML file is empty"]

    # Validate structure
    errors.extend(validate_parameter_structure(data))
    if errors:
        return False, errors

    params = data.get('parameters', {})

    # Validate parameter names
    errors.extend(validate_parameter_names(params))

    # Validate table rows
    for name, param_def in params.items():
        if param_def.get('type') == 'table':
            errors.extend(validate_table_rows(name, param_def))

    if errors:
        return False, errors

    return True, []


def yaml_to_json_format(data):
    """Convert YAML parameter format to JSON format for code generators.

    Converts from:
        parameters:
          param_name:
            type: float
            value: 1.0
            ...

    To:
        [
          {
            "name": "param_name",
            "type": "float",
            "value": 1.0,
            ...
          },
          ...
        ]
    """
    params = data.get('parameters', {})
    result = []

    for name, param_def in params.items():
        param = {'name': name}
        param.update(param_def)
        result.append(param)

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Validate parameter YAML files against JSON schema'
    )
    parser.add_argument('yaml_file', help='Path to the parameter YAML file')
    parser.add_argument('--schema', required=True, help='Path to the JSON schema file')
    parser.add_argument('--output-json', help='Output path for converted JSON (optional)')

    args = parser.parse_args()

    success, errors = validate_parameters(args.yaml_file, args.schema)

    if not success:
        print(f"Parameter validation failed for {args.yaml_file}:")
        for error in errors:
            print(f"  ERROR: {error}")
        sys.exit(1)

    print(f"Parameter validation passed for {args.yaml_file}")

    # Optionally output JSON format
    if args.output_json:
        data = load_yaml(args.yaml_file)
        json_data = yaml_to_json_format(data)
        with open(args.output_json, 'w') as f:
            json.dump(json_data, f, indent=2)
        print(f"Converted to JSON: {args.output_json}")

    sys.exit(0)


if __name__ == "__main__":
    main()
