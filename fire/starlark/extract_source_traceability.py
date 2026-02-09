#!/usr/bin/env python3
"""Build source-to-requirement traceability from declarative Bazel linkage.

Validates that requirement IDs declared in implements/verifies mappings
exist in the dependency requirement files, checks version consistency,
and produces a JSON trace file.
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


def parse_versioned_req(ref: str) -> tuple[str, int | None]:
    """Parse a versioned requirement reference like 'REQ_BC_FORCE?version=1'.

    Returns:
        Tuple of (req_id, version). Version is None if not specified.
    """
    if "?" not in ref:
        return ref, None

    req_id, query = ref.split("?", 1)
    version = None
    for param in query.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            if key == "version" and value.isdigit():
                version = int(value)
    return req_id, version


def extract_requirements_from_file(
    file_path: str,
) -> tuple[dict[str, int | None], str | None]:
    """Extract requirement IDs and versions from a requirement markdown file.

    Returns:
        Tuple of (req_map, error) where req_map maps req_id to its
        current version (or None if no metadata).
    """
    content, error = file_io_common.read_file_safe(file_path)
    if error:
        return {}, error

    req_map: dict[str, int | None] = {}
    for match in _REQ_ID_PATTERN.finditer(content):
        req_id = match.group(1)
        metadata, _ = parse_inline_metadata_for_requirement(content, req_id)
        req_map[req_id] = metadata.version if metadata is not None else None

    return req_map, None


def validate_mapping(
    mapping: dict[str, list[str]],
    available_reqs: dict[str, int | None],
    relationship: str,
) -> tuple[dict[str, list[dict]], list[str]]:
    """Validate an implements or verifies mapping against available requirements.

    Args:
        mapping: Dict of source_file -> list of "REQ_ID?version=N" strings.
        available_reqs: Dict of req_id -> current_version from dep files.
        relationship: "implements" or "verifies" for error messages.

    Returns:
        Tuple of (validated_output, errors) where validated_output maps
        source files to lists of {req_id, version} dicts.
    """
    errors: list[str] = []
    output: dict[str, list[dict]] = {}

    for source_file, refs in mapping.items():
        entries: list[dict] = []
        for ref in refs:
            req_id, declared_version = parse_versioned_req(ref)

            if req_id not in available_reqs:
                errors.append(
                    f"{source_file}: {relationship} references requirement "
                    f"'{req_id}' which was not found in any dep file"
                )
                continue

            if declared_version is None:
                errors.append(
                    f"{source_file}: {relationship} reference '{req_id}' "
                    f"is missing ?version= suffix"
                )
                continue

            actual_version = available_reqs[req_id]
            if actual_version is not None and declared_version < actual_version:
                # ANSI: \033[91m = light red, \033[0m = reset
                print(
                    f"\033[91mWARNING:\033[0m OUTDATED {relationship.upper()}! "
                    f"{source_file}: {relationship} {req_id} at version="
                    f"{declared_version}, but requirement is at version="
                    f"{actual_version}"
                )

            if actual_version is not None and declared_version > actual_version:
                errors.append(
                    f"{source_file}: {relationship} references {req_id} at "
                    f"version={declared_version}, but requirement is only at "
                    f"version={actual_version}"
                )
                continue

            entry: dict = {"req_id": req_id, "version": declared_version}
            entries.append(entry)

        if entries:
            output[source_file] = entries

    return output, errors


def build_trace_output(
    implements: dict[str, list[dict]],
    verifies: dict[str, list[dict]],
) -> dict:
    """Build the JSON trace output structure."""
    result: dict = {}
    if implements:
        result["implements"] = implements
    if verifies:
        result["verifies"] = verifies
    return result


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
        "--implements-json",
        default="{}",
        help="JSON dict mapping source files to versioned requirement refs",
    )
    parser.add_argument(
        "--verifies-json",
        default="{}",
        help="JSON dict mapping test files to versioned requirement refs",
    )

    args = parser.parse_args()

    implements_map: dict[str, list[str]] = json.loads(args.implements_json)
    verifies_map: dict[str, list[str]] = json.loads(args.verifies_json)

    # Collect all requirement IDs and versions from dep files
    all_errors: list[str] = []
    available_reqs: dict[str, int | None] = {}

    for dep_file in args.deps:
        if not dep_file.endswith(".md"):
            continue
        req_map, error = extract_requirements_from_file(dep_file)
        if error:
            all_errors.append(error)
        available_reqs.update(req_map)

    # Validate implements and verifies mappings
    impl_output, impl_errors = validate_mapping(
        implements_map, available_reqs, "implements"
    )
    all_errors.extend(impl_errors)

    ver_output, ver_errors = validate_mapping(verifies_map, available_reqs, "verifies")
    all_errors.extend(ver_errors)

    if all_errors:
        print("Source traceability validation failed:")
        for error in all_errors:
            print(f"  ERROR: {error}")
        sys.exit(1)

    trace_output = build_trace_output(impl_output, ver_output)

    with open(args.output, "w") as f:
        json.dump(trace_output, f, indent=2)
        f.write("\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
