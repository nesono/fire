#!/usr/bin/env python3
"""Validates parameter YAML files using Pydantic models.

This script reads a parameter YAML file and validates it against
the Pydantic parameter models. It also injects inferred types into
the output YAML so that code generators can use them.
"""

import argparse
import sys

from pydantic import ValidationError  # type: ignore

from fire.starlark import file_io_common
from fire.starlark.parameter_models import ParameterFile  # type: ignore
from fire.starlark.pydantic_tools import format_validation_errors  # type: ignore

_DISCRIMINATOR_TAGS = [
    "i64",
    "f64",
    "string",
    "bool",
    "table",
]


def validate_parameters(yaml_path):
    """Validate parameter YAML file using Pydantic models.

    Args:
        yaml_path: Path to the YAML file to validate

    Returns:
        Tuple of (data, errors) where:
        - data: validated data dict with injected types if successful, None otherwise
        - errors: list of error messages if validation failed, empty list otherwise
    """
    data, error = file_io_common.load_yaml_safe(yaml_path)
    if error:
        return None, [error]

    if data is None:
        return None, ["YAML file is empty"]

    try:
        ParameterFile.model_validate(data)
        # If validation succeeds, data now has injected type fields
        return data, []
    except ValidationError as e:
        return None, format_validation_errors(e, skip_loc_tags=_DISCRIMINATOR_TAGS)


def main():
    parser = argparse.ArgumentParser(
        description="Validate parameter YAML files using Pydantic models"
    )
    parser.add_argument("yaml_file", help="Path to the parameter YAML file")
    parser.add_argument("output_file", help="Path to the validated YAML file")

    args = parser.parse_args()

    data, errors = validate_parameters(args.yaml_file)

    if errors:
        print(f"Parameter validation failed for {args.yaml_file}:")
        for error in errors:
            print(f"  ERROR: {error}")
        sys.exit(1)

    # Write validated YAML with injected type fields to output
    error = file_io_common.write_yaml_safe(args.output_file, data)
    if error:
        print(f"Failed to write output file: {error}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
