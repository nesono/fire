#!/usr/bin/env python3
"""Validates parameter YAML files using Pydantic models.

This script reads a parameter YAML file and validates it against
the Pydantic parameter models.
"""

import argparse
import sys

import yaml
from pydantic import ValidationError  # type: ignore

from fire.starlark.parameter_models import ParameterFile  # type: ignore
from fire.starlark.pydantic_tools import format_validation_errors  # type: ignore

_DISCRIMINATOR_TAGS = [
    "i32",
    "i64",
    "u32",
    "u64",
    "f32",
    "f64",
    "string",
    "bool",
    "table",
]


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
        return False, format_validation_errors(e, skip_loc_tags=_DISCRIMINATOR_TAGS)

    return True, []


def main():
    parser = argparse.ArgumentParser(
        description="Validate parameter YAML files using Pydantic models"
    )
    parser.add_argument("yaml_file", help="Path to the parameter YAML file")
    parser.add_argument("output_file", help="Path to the validated YAML file")

    args = parser.parse_args()

    success, errors = validate_parameters(args.yaml_file)

    if not success:
        print(f"Parameter validation failed for {args.yaml_file}:")
        for error in errors:
            print(f"  ERROR: {error}")
        sys.exit(1)

    # copy input to output
    with open(args.yaml_file) as input_file:
        with open(args.output_file, "w") as output_file:
            output_file.write(input_file.read())

    sys.exit(0)


if __name__ == "__main__":
    main()
