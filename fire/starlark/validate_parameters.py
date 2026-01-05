#!/usr/bin/env python3
"""Validates parameter YAML files using Pydantic models.

This script reads a parameter YAML file and validates it against
the Pydantic parameter models.
"""

import argparse
import sys

import yaml
from pydantic import ValidationError  # type: ignore

from parameter_models import ParameterFile  # type: ignore


def load_yaml(yaml_path):
    """Load YAML file."""
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def validate_parameters(yaml_path):
    """Validate parameter YAML file using Pydantic models.

    Args:
        yaml_path: Path to the YAML file to validate

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
        ParameterFile.model_validate(data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            # Build the path string (skip discriminator tags like 'i32', 'bool', etc.)
            path_parts = []
            for p in error["loc"]:
                p_str = str(p)
                # Skip discriminator tags
                if p_str not in [
                    "i32",
                    "i64",
                    "u32",
                    "u64",
                    "f32",
                    "f64",
                    "string",
                    "bool",
                    "table",
                ]:
                    path_parts.append(p_str)
            path = " -> ".join(path_parts) if path_parts else "root"

            # Format the message to match schema style
            msg = error["msg"]

            # Handle specific error types to match schema messages
            error_type = error["type"]
            if error_type == "missing":
                field = error["loc"][-1] if error["loc"] else "field"
                msg = f"'{field}' is a required property"
            elif error_type == "string_too_short":
                # Keep original message which contains "should have at least X character"
                msg = f"{msg}"
            elif error_type == "greater_than_equal":
                # Keep original message which contains ">= X"
                msg = f"{msg}"
            elif error_type == "literal_error":
                msg = "value is not a valid enumeration member"
            elif error_type == "int_type":
                msg = "value is not a valid integer"
            elif error_type == "float_type":
                msg = "value is not a valid number"
            elif error_type == "string_type":
                msg = "value is not a valid string"
            elif error_type == "bool_type":
                msg = "value is not a valid boolean"
            elif error_type == "extra_forbidden":
                field = error["loc"][-1] if error["loc"] else "field"
                msg = (
                    f"Additional properties are not allowed ('{field}' was unexpected)"
                )
            elif error_type == "too_short":
                # Keep original message which contains "should have at least X item"
                msg = f"{msg}"
            elif error_type == "string_pattern_mismatch":
                pattern = error.get("ctx", {}).get("pattern", "")
                value = error.get("input", "")
                msg = f"'{value}' does not match '{pattern}'"
            elif error_type == "value_error":
                # Custom validation errors from field_validator
                msg = msg.replace("Value error, ", "")
            elif error_type == "union_tag_invalid":
                # Discriminated union tag mismatch
                msg = "value is not a valid enumeration member"

            errors.append(f"Validation error at '{path}': {msg}")

        return False, errors

    return True, []


def main():
    parser = argparse.ArgumentParser(
        description="Validate parameter YAML files against JSON schema"
    )
    parser.add_argument("yaml_file", help="Path to the parameter YAML file")

    args = parser.parse_args()

    success, errors = validate_parameters(args.yaml_file)

    if not success:
        print(f"Parameter validation failed for {args.yaml_file}:")
        for error in errors:
            print(f"  ERROR: {error}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
