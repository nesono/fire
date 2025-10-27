#!/usr/bin/env python3
"""Tool to validate parameter files."""

import json
import sys

import yaml

from fire.parameters.validator import ParameterValidator, ValidationError


def main():
    """Validate a parameter YAML file and output as JSON."""
    if len(sys.argv) != 3:
        print(
            "Usage: validate_parameters <input.yaml> <output.params>", file=sys.stderr
        )
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        # Load YAML file
        with open(input_path, "r") as f:
            param_data = yaml.safe_load(f)

        # Validate
        validator = ParameterValidator()
        validator.validate(param_data)

        # Write validated data as JSON for easier consumption by other tools
        with open(output_path, "w") as f:
            json.dump(param_data, f, indent=2)

        print(f"Successfully validated {input_path}", file=sys.stderr)

    except ValidationError as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
