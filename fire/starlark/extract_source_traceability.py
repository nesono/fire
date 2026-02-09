#!/usr/bin/env python3
"""Build source-to-requirement traceability from declarative Bazel linkage.

This script reads requirement files from declared deps, extracts their
requirement IDs and versions, and produces a JSON mapping that links
the declared source files to those requirements. No source code parsing
is performed — the linkage is purely file-based via the Bazel rule.
"""

import argparse
import json
import re
import sys

from fire.starlark import file_io_common
from fire.starlark.validate_cross_references import (
    parse_inline_metadata_for_requirement,
)

_REQ_ID_PATTERN: re.Pattern[str] = re.compile(
    r"^## ([A-Z][A-Z0-9_-]+)\s*$", re.MULTILINE
)


def extract_requirements_from_file(
    file_path: str,
) -> tuple[list[dict], str | None]:
    """Extract requirement IDs and versions from a requirement markdown file.

    Returns:
        Tuple of (requirements, error) where requirements is a list of
        dicts with req_id, path, and version keys.
    """
    content, error = file_io_common.read_file_safe(file_path)
    if error:
        return [], error

    requirements: list[dict] = []
    for match in _REQ_ID_PATTERN.finditer(content):
        req_id = match.group(1)
        metadata, _ = parse_inline_metadata_for_requirement(content, req_id)
        entry: dict = {"req_id": req_id, "path": file_path}
        if metadata is not None:
            entry["version"] = metadata.version
        requirements.append(entry)

    return requirements, None


def build_trace_output(
    source_files: list[str],
    requirements: list[dict],
) -> dict:
    """Build the JSON trace output structure.

    Each source file is linked to all requirements from the declared deps.
    """
    sources: dict[str, list[dict]] = {}
    for src in source_files:
        sources[src] = list(requirements)
    return {"sources": sources}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build source-to-requirement traceability mapping"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--dep",
        action="append",
        default=[],
        dest="deps",
        help="Requirement file dependency (repeatable)",
    )
    parser.add_argument(
        "source_files",
        nargs="+",
        help="Source files to link",
    )

    args = parser.parse_args()

    all_errors: list[str] = []
    all_requirements: list[dict] = []

    for dep_file in args.deps:
        if not dep_file.endswith(".md"):
            continue
        reqs, error = extract_requirements_from_file(dep_file)
        if error:
            all_errors.append(error)
        all_requirements.extend(reqs)

    if all_errors:
        print("Source traceability extraction failed:")
        for error in all_errors:
            print(f"  ERROR: {error}")
        sys.exit(1)

    trace_output = build_trace_output(args.source_files, all_requirements)

    with open(args.output, "w") as f:
        json.dump(trace_output, f, indent=2)
        f.write("\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
