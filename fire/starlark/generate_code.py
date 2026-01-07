#!/usr/bin/env python3
"""Generate code from Fire parameter definitions.

Usage:
    generate_code.py cpp <input> <output> [--namespace=<ns>]
    generate_code.py python <input> <output>
    generate_code.py go <input> <output>
    generate_code.py rust <input> <output>
    generate_code.py java <input> <output> [--class-name=<name>]

Arguments:
    <input>   Path to the YAML parameter data file
    <output>  Path to write the generated code

Options:
    --namespace=<ns>    C++ namespace (overrides auto-derived namespace)
    --class-name=<name> Java class name [default: Parameters]
"""

import argparse
import sys
from pathlib import Path

import yaml

from fire.starlark.generators.cpp import generate_cpp
from fire.starlark.generators.python import generate_python
from fire.starlark.generators.go import generate_go
from fire.starlark.generators.rust import generate_rust
from fire.starlark.generators.java import generate_java


def yaml_to_internal_format(yaml_data, namespace=""):
    """Convert YAML parameter format to internal format for generators."""
    params = yaml_data.get("parameters", {})
    parameters = []

    for name, param_def in params.items():
        param = {"name": name}
        param.update(param_def)
        parameters.append(param)

    return {"namespace": namespace, "parameters": parameters}


def main():
    parser = argparse.ArgumentParser(
        description="Generate code from Fire parameter definitions"
    )
    parser.add_argument(
        "--package-path",
        default="",
        help="Bazel package path (for generating unique identifiers)",
    )
    subparsers = parser.add_subparsers(dest="language", required=True)

    # C++ subcommand
    cpp_parser = subparsers.add_parser("cpp", help="Generate C++ header")
    cpp_parser.add_argument("input", help="Input JSON file")
    cpp_parser.add_argument("output", help="Output file path")
    cpp_parser.add_argument(
        "--namespace",
        dest="cpp_namespace",
        help="C++ namespace (overrides auto-derived)",
    )

    # Python subcommand
    py_parser = subparsers.add_parser("python", help="Generate Python module")
    py_parser.add_argument("input", help="Input JSON file")
    py_parser.add_argument("output", help="Output file path")

    # Go subcommand
    go_parser = subparsers.add_parser("go", help="Generate Go package")
    go_parser.add_argument("input", help="Input YAML file")
    go_parser.add_argument("output", help="Output file path")
    go_parser.add_argument(
        "--namespace", dest="namespace", help="Package namespace (e.g., examples)"
    )

    # Rust subcommand
    rust_parser = subparsers.add_parser("rust", help="Generate Rust module")
    rust_parser.add_argument("input", help="Input JSON file")
    rust_parser.add_argument("output", help="Output file path")

    # Java subcommand
    java_parser = subparsers.add_parser("java", help="Generate Java class")
    java_parser.add_argument("input", help="Input YAML file")
    java_parser.add_argument("output", help="Output file path")
    java_parser.add_argument(
        "--class-name", dest="class_name", default="Parameters", help="Java class name"
    )
    java_parser.add_argument(
        "--namespace",
        dest="namespace",
        help="Java package namespace (e.g., com.example)",
    )

    args = parser.parse_args()

    # Determine namespace
    namespace = (
        getattr(args, "namespace", None) or getattr(args, "cpp_namespace", None) or ""
    )

    # Load parameter data
    try:
        with open(args.input, "r") as f:
            yaml_data = yaml.safe_load(f)
        param_data = yaml_to_internal_format(yaml_data, namespace)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate code based on language
    if args.language == "cpp":
        code = generate_cpp(
            param_data,
            getattr(args, "cpp_namespace", None),
            args.output,
            args.package_path,
        )
    elif args.language == "python":
        code = generate_python(param_data)
    elif args.language == "go":
        code = generate_go(param_data)
    elif args.language == "rust":
        code = generate_rust(param_data)
    elif args.language == "java":
        param_data["class_name"] = args.class_name
        code = generate_java(param_data)
    else:
        print(f"Error: Unknown language: {args.language}", file=sys.stderr)
        sys.exit(1)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code)


if __name__ == "__main__":
    main()
