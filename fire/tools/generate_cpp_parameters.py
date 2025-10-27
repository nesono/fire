#!/usr/bin/env python3
"""Tool to generate C++ header files from parameter files."""

import sys
import json
import argparse
from fire.parameters.cpp_generator import CppGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate C++ header from parameters")
    parser.add_argument("input", help="Input parameter file (.params)")
    parser.add_argument("output", help="Output C++ header file (.h)")
    parser.add_argument("--namespace", help="Override namespace for generated code")

    args = parser.parse_args()

    try:
        # Load validated parameter data (stored as JSON)
        with open(args.input, "r") as f:
            param_data = json.load(f)

        # Override namespace if specified
        if args.namespace:
            param_data["namespace"] = args.namespace

        # Generate C++ code
        generator = CppGenerator()
        cpp_code = generator.generate(param_data)

        # Write output
        with open(args.output, "w") as f:
            f.write(cpp_code)

        print(f"Successfully generated {args.output}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
