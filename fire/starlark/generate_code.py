#!/usr/bin/env python3
"""Generate code from Fire parameter definitions.

Usage:
    generate_code.py cpp <input> <output_dir> [--namespace=<ns>]
    generate_code.py python <input> <output_dir>
    generate_code.py go <input> <output_dir>
    generate_code.py rust <input> <output_dir>
    generate_code.py java <input> <output_dir> [--namespace=<ns>]

Arguments:
    <input>      Path to the YAML parameter data file
    <output_dir> Path to the output directory (TreeArtifact)

Options:
    --namespace=<ns>    C++ namespace or Java package
"""

import argparse
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import yaml

from fire.starlark.generators.cpp import generate_cpp_files
from fire.starlark.generators.go import generate_go_files
from fire.starlark.generators.java import generate_java_files
from fire.starlark.generators.python import generate_python_files
from fire.starlark.generators.rust import generate_rust_files


def yaml_to_items(yaml_data):
    """Convert YAML parameter format to flat list of per-version items.

    Each item contains all information needed to render a single
    parameter-version file.
    """
    params = yaml_data.get("parameters", {})
    groups = defaultdict(list)

    version_re = re.compile(r"^(.+)_v(\d+)$")

    for key, param_def in params.items():
        m = version_re.match(key)
        if m:
            base_name = m.group(1)
            version = int(m.group(2))
        else:
            base_name = key
            version = param_def.get("version", 1)

        entry = {
            "base_name": base_name,
            "version": version,
        }
        entry.update(param_def)
        groups[base_name].append(entry)

    items = []
    for base_name, entries in groups.items():
        entries.sort(key=lambda v: v["version"])
        max_version = entries[-1]["version"]
        for entry in entries:
            entry["max_version"] = max_version
            entry["is_latest"] = entry["version"] == max_version
            items.append(entry)

    return items


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
    cpp_parser = subparsers.add_parser("cpp", help="Generate C++ headers")
    cpp_parser.add_argument("input", help="Input YAML file")
    cpp_parser.add_argument("output", help="Output directory path")
    cpp_parser.add_argument(
        "--namespace",
        dest="cpp_namespace",
        help="C++ namespace (overrides auto-derived)",
    )

    # Python subcommand
    py_parser = subparsers.add_parser("python", help="Generate Python modules")
    py_parser.add_argument("input", help="Input YAML file")
    py_parser.add_argument("output", help="Output directory path")

    # Go subcommand
    go_parser = subparsers.add_parser("go", help="Generate Go packages")
    go_parser.add_argument("input", help="Input YAML file")
    go_parser.add_argument("output", help="Output directory path")
    go_parser.add_argument("--namespace", dest="namespace", help="Package namespace")

    # Rust subcommand
    rust_parser = subparsers.add_parser("rust", help="Generate Rust modules")
    rust_parser.add_argument("input", help="Input YAML file")
    rust_parser.add_argument("output", help="Output directory path")

    # Java subcommand
    java_parser = subparsers.add_parser("java", help="Generate Java classes")
    java_parser.add_argument("input", help="Input YAML file")
    java_parser.add_argument("output", help="Output directory path")
    java_parser.add_argument(
        "--namespace",
        dest="namespace",
        help="Java package namespace (e.g., com.example)",
    )
    java_parser.add_argument(
        "--class-name",
        dest="class_name",
        help="Java class name (defaults to PascalCase of output filename)",
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
        items = yaml_to_items(yaml_data)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate files based on language
    if args.language == "cpp":
        files = generate_cpp_files(
            items,
            cpp_namespace=getattr(args, "cpp_namespace", None) or "",
            package_path=args.package_path,
        )
    elif args.language == "python":
        files = generate_python_files(items)
    elif args.language == "go":
        # Derive Go package name from the output directory name
        go_package = Path(args.output).name
        files = generate_go_files(items, package_name=go_package)
    elif args.language == "rust":
        files = generate_rust_files(items)
    elif args.language == "java":
        # Determine class name (default to PascalCase of output filename)
        class_name = getattr(args, "class_name", None)
        if not class_name:
            # Derive from output filename (strip .srcjar if present)
            output_name = Path(args.output).stem
            # Convert to PascalCase: remove underscores and capitalize
            class_name = "".join(word.capitalize() for word in output_name.split("_"))
        files = generate_java_files(items, namespace=namespace, class_name=class_name)
    else:
        print(f"Error: Unknown language: {args.language}", file=sys.stderr)
        sys.exit(1)

    # Write output files
    output_path = Path(args.output)
    if output_path.suffix == ".srcjar":
        # Java: write files into a srcjar (zip file)
        with zipfile.ZipFile(output_path, "w") as zf:
            for rel_path, content in files:
                zf.writestr(rel_path, content)
    elif output_path.suffix == ".rs":
        # Rust: write single lib.rs file directly
        if len(files) != 1:
            print(
                f"Error: Expected single Rust file but got {len(files)}",
                file=sys.stderr,
            )
            sys.exit(1)
        _, content = files[0]
        output_path.write_text(content)
    else:
        # All other languages: write files into a directory (TreeArtifact)
        output_path.mkdir(parents=True, exist_ok=True)
        for rel_path, content in files:
            file_path = output_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)


if __name__ == "__main__":
    main()
