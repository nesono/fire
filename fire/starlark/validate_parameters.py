#!/usr/bin/env python3
"""Validates parameter YAML files against JSON schema.

This script reads a parameter YAML file and validates it against
the parameter JSON schema.
"""

import argparse
import json
import sys

import jsonschema
import yaml


def load_yaml(yaml_path):
    """Load YAML file."""
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def load_schema(schema_path):
    """Load JSON schema file."""
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_parameters(yaml_path, schema_path):
    """Validate parameter YAML file against JSON schema.

    Returns:
        Tuple of (success, errors) where errors is a list of error messages.
    """
    try:
        data = load_yaml(yaml_path)
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML syntax: {e}"]
    except Exception as e:
        return False, [f"Failed to load YAML: {e}"]

    if data is None:
        return False, ["YAML file is empty"]

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        return False, [f"Failed to load schema: {e}"]

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        # Format a user-friendly error message
        path = (
            " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        )
        return False, [f"Validation error at '{path}': {e.message}"]
    except jsonschema.SchemaError as e:
        return False, [f"Invalid schema: {e.message}"]

    return True, []


def main():
    parser = argparse.ArgumentParser(
        description="Validate parameter YAML files against JSON schema"
    )
    parser.add_argument("yaml_file", help="Path to the parameter YAML file")
    parser.add_argument("--schema", required=True, help="Path to the JSON schema file")

    args = parser.parse_args()

    success, errors = validate_parameters(args.yaml_file, args.schema)

    if not success:
        print(f"Parameter validation failed for {args.yaml_file}:")
        for error in errors:
            print(f"  ERROR: {error}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
