#!/usr/bin/env python3
"""Validates that cross-references in requirements actually exist.

ARCHITECTURE NOTE:
This Python file is a THIN WRAPPER for file I/O only. The validation logic
is defined in Starlark files which are the source of truth:

This Python implementation mirrors that Starlark logic to enable build-time
validation via file I/O. When updating validation rules, update the Starlark
files first, then mirror changes here.

WHY PYTHON?: Starlark rules cannot directly read arbitrary files during build.
Python handles file I/O and applies the same validation rules defined in Starlark.
"""

import os
import re
import sys

from typing import Final
from fire.starlark.pydantic_tools import format_validation_errors  # type: ignore

_BARE_TODO_RE: Final = re.compile(r"TODO(?!\([A-Z]+-[0-9]+\))")


def validate_no_bare_todos(content: str, file_path: str) -> list[str]:
    """Scan entire file for bare or malformed TODO markers.

    Every occurrence of 'TODO' must use the format TODO(KEY-1234).
    Returns list of error strings.
    """
    errors: list[str] = []
    for line_num, line in enumerate(content.split("\n"), start=1):
        for match in _BARE_TODO_RE.finditer(line):
            snippet = line[match.start() : match.start() + 30]
            errors.append(
                f"{file_path}:{line_num}: Bare or malformed TODO found: "
                f"'{snippet}'. Must use format TODO(KEY-1234)"
            )
    return errors


def parse_inline_metadata_for_requirement(content, req_id):
    """Parse inline metadata for a specific requirement ID.

    Looks for ## REQ-ID heading followed by a line with pipe-separated fields.
    Format: Key1: value1 | Key2: value2 | Key3: [link](url)
    Returns tuple of (RequirementMetadata | None, ValidationError | None).
    """
    from fire.starlark.requirement_models import RequirementMetadata
    from pydantic import ValidationError

    lines = content.split("\n")
    metadata_line = None

    for i, line in enumerate(lines):
        if line.startswith(f"## {req_id}"):
            # The next non-empty line should be the metadata line
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if next_line:
                    # Check if this is a metadata line (contains | or single Key: value)
                    if "|" in next_line:
                        metadata_line = next_line
                        break
                    elif ":" in next_line and not next_line.startswith("#"):
                        # Simple heuristic: metadata lines have key: value format
                        # and the key is a known metadata field (SIL, Sec, Version, Parent)
                        parts = next_line.split(":", 1)
                        key = parts[0].strip().lower()
                        known_fields = ["sil", "sec", "version", "parent"]
                        if len(parts) == 2 and key in known_fields:
                            metadata_line = next_line
                            break
                    # If it's not metadata, break (don't keep searching)
                    break
            break

    if not metadata_line:
        return None, None

    # Parse pipe-separated fields: Key1: value1 | Key2: value2 | Parent: [REQ-ID](path)
    frontmatter = {"id": req_id}

    # Split by | to get individual fields
    fields = metadata_line.split("|")

    for field in fields:
        field = field.strip()
        if not field or ":" not in field:
            continue

        # Split by first : to get key and value
        parts = field.split(":", 1)
        key = parts[0].strip().lower()  # Normalize key to lowercase
        value = parts[1].strip() if len(parts) > 1 else ""

        # Check if value contains a markdown link [text](url)
        if value.startswith("[") and "](" in value:
            # This is a parent reference - extract just the requirement ID
            # Format: [REQ-ID](/path/to/file.md?version=N#REQ-ID)
            match = re.match(r"\[([^\]]+)\]\(([^\)]+)\)", value)
            if match:
                frontmatter[key] = value  # Keep full markdown link for parent
                continue

        # Try to parse as int
        if value.isdigit():
            frontmatter[key] = int(value)
        # Parse booleans
        elif value.lower() == "true":
            frontmatter[key] = True
        elif value.lower() == "false":
            frontmatter[key] = False
        else:
            frontmatter[key] = value

    # Validate with Pydantic
    try:
        metadata = RequirementMetadata.model_validate(frontmatter)
        return metadata, None
    except ValidationError as e:
        return None, e


def extract_markdown_references(body):
    """Extract parameter and requirement references from Markdown body."""
    param_refs = []
    req_refs = []

    # Pattern for [@param](path?version=N#param)
    param_pattern = r"\[@([a-zA-Z_][a-zA-Z0-9_]*)\]\(([^)]+)\)"
    for match in re.finditer(param_pattern, body):
        param_name = match.group(1)
        full_url = match.group(2)

        # Extract version from query parameter if present
        version = None
        clean_path = full_url
        if "?" in full_url:
            path_part, query_part = full_url.split("?", 1)
            # Extract query string (before # if present)
            query_str = query_part.split("#")[0] if "#" in query_part else query_part
            # Parse version=N
            for param in query_str.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    if key == "version" and value.isdigit():
                        version = int(value)
            # Reconstruct clean path with fragment if present
            clean_path = path_part
            if "#" in query_part:
                clean_path = clean_path + "#" + query_part.split("#")[1]

        param_refs.append((param_name, clean_path, version))

    # Pattern for [REQ-ID](path.md?version=N#anchor) or [REQ-ID](path.md)
    req_pattern = r"\[([A-Z][A-Z0-9_-]+)\]\(([^)]+\.md[^)]*)\)"
    for match in re.finditer(req_pattern, body):
        req_id = match.group(1)
        full_url = match.group(2)

        # Extract version from query parameter if present
        version = None
        clean_path = full_url
        if "?" in full_url:
            path_part, query_part = full_url.split("?", 1)
            # Extract query string (before # if present)
            query_str = query_part.split("#")[0] if "#" in query_part else query_part
            # Parse version=N
            for param in query_str.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    if key == "version" and value.isdigit():
                        version = int(value)
            # Reconstruct clean path with fragment if present
            clean_path = path_part
            if "#" in query_part:
                clean_path = clean_path + "#" + query_part.split("#")[1]

        req_refs.append((req_id, clean_path, version))

    return param_refs, req_refs


def validate_parameter_reference(
    param_name, param_path, workspace_root, ref_version=None, source_file=None
):
    """Validate that a parameter reference exists and check version if specified."""
    # Extract file path and anchor
    if "#" in param_path:
        file_path, anchor = param_path.split("#", 1)
    else:
        file_path = param_path
        anchor = param_name

    # Check that path is repository-relative (starts with /)
    if not file_path.startswith("/"):
        return (
            False,
            f"Parameter reference path must be repository-relative (start with /): '{param_path}'",
        )

    # Strip leading slash for repository-relative paths (e.g., /examples/foo.yaml -> examples/foo.yaml)
    # Markdown uses /path for repository-relative, but os.path.join treats it as absolute
    if file_path.startswith("/"):
        file_path = file_path[1:]

    # Check that link text matches anchor
    if param_name != anchor:
        return (
            False,
            f"Parameter link text '{param_name}' does not match anchor '{anchor}' in {param_path}",
        )

    # Convert to absolute path
    abs_path = os.path.join(workspace_root, file_path)

    # Check if file exists, or try the _validated.yaml version from parameter_library
    if not os.path.exists(abs_path):
        # parameter_library outputs foo_validated.yaml from foo.yaml
        if file_path.endswith(".yaml"):
            validated_path = file_path[:-5] + "_validated.yaml"
            validated_abs_path = os.path.join(workspace_root, validated_path)
            if os.path.exists(validated_abs_path):
                abs_path = validated_abs_path
            else:
                return False, f"Parameter file does not exist: {file_path}"
        else:
            return False, f"Parameter file does not exist: {file_path}"

    # Read file and check if parameter is defined
    try:
        with open(abs_path, "r") as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"

    # Check version if ref_version is specified
    if ref_version is None:
        return False, f"Parameter '{anchor}' misses version in {file_path}"

    # Find the max version to check for staleness warning
    max_version = 0
    for line in content.split("\n"):
        version_match = re.match(rf"^\s*{re.escape(anchor)}_v(\d+)\s*:", line)
        if version_match:
            v = int(version_match.group(1))
            if v > max_version:
                max_version = v

    # Look for parameter definition using _vN suffix key format
    # e.g., "  param_name_v2:" in the YAML file
    versioned_key = f"{anchor}_v{ref_version}:"
    if versioned_key not in content:
        # Check if the base parameter exists at all (any version)
        if f"{anchor}_v" not in content:
            return False, f"Parameter '{anchor}' not found in {file_path}"
        # Parameter exists but not at the requested version
        # Find the max version available
        if ref_version > max_version:
            return (
                False,
                f"Parameter {anchor} expects a future version ({ref_version}), but max version is {max_version}",
            )

    # ANSI color codes: \033[91m = light red, \033[0m = reset
    # Print to stdout so Bazel shows these warnings even when validation passes
    if max_version > 0 and ref_version < max_version:
        print(
            f"\033[91mWARNING:\033[0m PARAMETER VERSION MISMATCH! {source_file}: Reference to @{param_name} specifies version={ref_version}, but {file_path} is at version={max_version}"
        )

    return True, None


def validate_requirement_reference(
    req_id, req_path, workspace_root, ref_version=None, source_file=None
):
    """Validate that a requirement reference exists and check version if specified."""
    # Check that path is repository-relative (starts with /)
    # Extract the path part before checking (handle fragments and query params)
    path_to_check = req_path.split("#")[0] if "#" in req_path else req_path
    path_to_check = (
        path_to_check.split("?")[0] if "?" in path_to_check else path_to_check
    )

    if not path_to_check.startswith("/"):
        return (
            False,
            f"Requirement reference path must be repository-relative (start with /): '{req_path}'",
        )

    # Strip leading slash for repository-relative paths (e.g., /examples/foo.md -> examples/foo.md)
    # Markdown uses /path for repository-relative, but os.path.join treats it as absolute
    if req_path.startswith("/"):
        req_path = req_path[1:]

    # Remove fragment if present (e.g., path.md#REQ-ID -> path.md)
    path_without_fragment = req_path.split("#")[0] if "#" in req_path else req_path

    # Check that filename has valid extension
    filename = os.path.basename(path_without_fragment)
    if not (filename.endswith(".md") or filename.endswith(".sysreq.md")):
        return (
            False,
            f"Requirement file must have .md or .sysreq.md extension: {filename}",
        )

    # Convert to absolute path
    abs_path = os.path.join(workspace_root, path_without_fragment)

    # Check if file exists
    if not os.path.exists(abs_path):
        return False, f"Requirement file does not exist: {req_path}"

    # Read file and verify it contains the correct requirement ID
    try:
        with open(abs_path, "r") as f:
            content = f.read()

        # Parse inline metadata (pipe-separated format)
        metadata, validation_error = parse_inline_metadata_for_requirement(
            content, req_id
        )

        if metadata is None:
            if validation_error:
                error_messages = format_validation_errors(validation_error)
                return (
                    False,
                    f"Requirement file {req_path} validation failed: {'; '.join(error_messages)}",
                )
            else:
                return (
                    False,
                    f"Requirement file {req_path} does not contain ID '{req_id}'",
                )

        # Check version if ref_version is specified
        if ref_version is not None:
            actual_version = metadata.version
            # ANSI color codes: \033[91m = light red, \033[0m = reset
            # Print to stdout so Bazel shows these warnings even when validation passes
            if actual_version != ref_version:
                print(
                    f"\033[91mWARNING:\033[0m REQUIREMENT VERSION MISMATCH! {source_file}: Reference to {req_id} specifies version={ref_version}, but {path_without_fragment} is at version={actual_version}"
                )

        return True, None

    except Exception as e:
        return False, f"Error reading {req_path}: {e}"


def validate_requirement_file(file_path, workspace_root, allowed_deps=None):
    """Validate all cross-references in a single requirement file.

    Args:
        file_path: Path to the requirement file to validate
        workspace_root: Workspace root directory
        allowed_deps: Set of allowed dependency file paths (for strict validation)
    """
    errors = []
    if allowed_deps is None:
        allowed_deps = set()

    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        return [f"Error reading {file_path}: {e}"]

    # Validate no bare/malformed TODOs in the entire file
    errors.extend(validate_no_bare_todos(content, file_path))

    # Validate the requirement file's own metadata
    # Find all requirement IDs in the file and validate each one
    req_id_pattern = r"^## ([A-Z][A-Z0-9_-]+)\s*$"
    for match in re.finditer(req_id_pattern, content, re.MULTILINE):
        req_id = match.group(1)
        metadata, validation_error = parse_inline_metadata_for_requirement(
            content, req_id
        )

        if metadata is None:
            if validation_error:
                for msg in format_validation_errors(validation_error):
                    errors.append(f"{file_path}: Requirement '{req_id}' - {msg}")
            else:
                errors.append(f"{file_path}: Requirement ID '{req_id}' has no metadata")
            continue

        # Validation now handled by Pydantic model - no manual checks needed!

    # Extract references from markdown body
    param_refs, req_refs = extract_markdown_references(content)

    # Validate parameter references exist
    for param_name, param_path, ref_version in param_refs:
        # Check if this parameter file is in allowed_deps (strict dependency checking)
        # Only enforce if allowed_deps is not None (i.e., was explicitly passed)
        if allowed_deps is not None:
            # Strip leading slash for comparison
            normalized_path = (
                param_path[1:] if param_path.startswith("/") else param_path
            )
            # Remove fragment if present
            normalized_path = (
                normalized_path.split("#")[0]
                if "#" in normalized_path
                else normalized_path
            )

            # Check both the original path and the _validated.yaml version from parameter_library
            validated_path = None
            if normalized_path.endswith(".yaml"):
                validated_path = normalized_path[:-5] + "_validated.yaml"

            if normalized_path not in allowed_deps and (
                validated_path is None or validated_path not in allowed_deps
            ):
                errors.append(
                    f"{file_path}: References parameter file '{param_path}' which is not in declared dependencies.\n"
                    f"       Add the target containing '{normalized_path}' to 'deps' in your requirement_library().\n"
                    f'       Example: deps = [":vehicle_params"]'
                )
                continue  # Skip further validation for this parameter

        valid, error = validate_parameter_reference(
            param_name, param_path, workspace_root, ref_version, file_path
        )
        if not valid:
            errors.append(f"{file_path}: {error}")

    # Validate requirement references exist and check versions
    for req_id, req_path, ref_version in req_refs:
        # Check if this requirement is in allowed_deps (strict dependency checking)
        # Only enforce if allowed_deps is not None (i.e., was explicitly passed)
        if allowed_deps is not None:
            # Strip leading slash and fragment for comparison
            normalized_path = req_path[1:] if req_path.startswith("/") else req_path
            normalized_path = (
                normalized_path.split("#")[0]
                if "#" in normalized_path
                else normalized_path
            )

            if normalized_path not in allowed_deps:
                errors.append(
                    f"{file_path}: References requirement '{req_path}' which is not in declared dependencies.\n"
                    f"       Add the target containing '{normalized_path}' to 'deps' in your requirement_library().\n"
                    f'       Example: deps = [":vehicle_requirements"]'
                )
                continue  # Skip further validation for this requirement

        valid, error = validate_requirement_reference(
            req_id, req_path, workspace_root, ref_version, file_path
        )
        if not valid:
            errors.append(f"{file_path}: {error}")

    return errors


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate cross-references in requirement documents"
    )
    parser.add_argument("workspace_root", help="Workspace root directory")
    parser.add_argument(
        "--allowed-deps", nargs="*", default=None, help="Allowed dependency file paths"
    )
    parser.add_argument(
        "requirement_files", nargs="+", help="Requirement files to validate"
    )

    args = parser.parse_args()

    workspace_root = args.workspace_root
    # Convert to set for faster lookup, or keep as None if not provided
    allowed_deps = set(args.allowed_deps) if args.allowed_deps is not None else None
    requirement_files = args.requirement_files

    all_errors = []

    for req_file in requirement_files:
        errors = validate_requirement_file(req_file, workspace_root, allowed_deps)
        all_errors.extend(errors)

    if all_errors:
        print("Cross-reference validation failed:")
        for error in all_errors:
            print(f"  ERROR: {error}")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
