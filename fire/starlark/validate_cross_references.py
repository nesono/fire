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

from pydantic import ValidationError

from fire.starlark import file_io_common, markdown_common, path_common
from fire.starlark.pydantic_tools import format_validation_errors  # type: ignore
from fire.starlark.requirement_models import RequirementMetadata

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


def _find_requirement_heading_index(lines: list[str], req_id: str) -> int | None:
    """Find the line index of the requirement heading.

    Returns the index of the line starting with '## REQ_ID', or None if not found.
    """
    for i, line in enumerate(lines):
        if line.startswith(f"## {req_id}"):
            return i
    return None


def _is_metadata_line(line: str, known_fields: list[str]) -> bool:
    """Check if a line looks like metadata."""
    if "|" in line:
        return True
    if ":" in line and not line.startswith("#"):
        parts = line.split(":", 1)
        key = parts[0].strip().lower()
        return len(parts) == 2 and key in known_fields
    return False


def _should_stop_collection(line: str, collected_lines: list[str]) -> bool:
    """Check if we should stop collecting metadata lines."""
    if not line:
        return bool(collected_lines)
    if collected_lines and not collected_lines[-1].endswith("|"):
        return True
    return False


def _join_metadata_lines(lines: list[str]) -> str:
    """Join metadata lines and strip final trailing pipe."""
    joined = " ".join(lines).rstrip()
    if joined.endswith("|"):
        joined = joined[:-1].rstrip()
    return joined


def _extract_next_metadata_line(lines: list[str], start_index: int) -> str | None:
    """Extract metadata lines after start_index, supporting multi-line continuation."""
    known_fields = ["sil", "sec", "version", "parent"]
    collected_lines = []

    for j in range(start_index + 1, len(lines)):
        next_line = lines[j].strip()

        if not next_line and not collected_lines:
            continue

        if _should_stop_collection(next_line, collected_lines):
            break

        if not _is_metadata_line(next_line, known_fields):
            break

        collected_lines.append(next_line)
        if not next_line.endswith("|"):
            break

    return _join_metadata_lines(collected_lines) if collected_lines else None


def _parse_field_value(value: str) -> int | bool | str:
    """Parse a single metadata field value to its appropriate type.

    Handles:
    - Markdown links (returned as-is)
    - Integers (converted to int)
    - Booleans (true/false converted to bool)
    - Strings (returned as-is)
    """
    # Markdown links stay as strings
    if value.startswith("[") and "](" in value:
        # Validate it matches the expected link pattern
        match = re.match(markdown_common.MARKDOWN_LINK_PATTERN, value)
        if match:
            return value

    # Parse integers
    if value.isdigit():
        return int(value)

    # Parse booleans
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Default: return as string
    return value


def _parse_metadata_fields(metadata_line: str, req_id: str) -> dict:
    """Parse pipe-separated metadata fields into a frontmatter dictionary.

    Splits the line by '|' and parses each 'key: value' pair.
    Keys are normalized to lowercase. Values are typed using _parse_field_value.

    Special handling for Parent field:
    - Multiple Parent fields are aggregated into a list
    - Stored as frontmatter["parent"] = [value1, value2, ...]
    - Always stored as list for consistency, even if single parent
    """
    frontmatter = {"id": req_id}
    parent_values = []

    for field in metadata_line.split("|"):
        field = field.strip()
        if not field or ":" not in field:
            continue

        # Split by first ':' to get key and value
        parts = field.split(":", 1)
        key = parts[0].strip().lower()
        value = parts[1].strip() if len(parts) > 1 else ""

        # Special handling for parent field - aggregate into list
        if key == "parent":
            parent_values.append(_parse_field_value(value))
        else:
            frontmatter[key] = _parse_field_value(value)

    # Store parent as list if any parent values were found
    if parent_values:
        frontmatter["parent"] = parent_values

    return frontmatter


def parse_inline_metadata_for_requirement(content, req_id):
    """Parse inline metadata for a specific requirement ID.

    Looks for ## REQ-ID heading followed by a line with pipe-separated fields.
    Format: Key1: value1 | Key2: value2 | Key3: [link](url)
    Returns tuple of (RequirementMetadata | None, ValidationError | None).
    """
    # Find the requirement heading
    lines = content.split("\n")
    heading_index = _find_requirement_heading_index(lines, req_id)
    if heading_index is None:
        return None, None

    # Extract the metadata line following the heading
    metadata_line = _extract_next_metadata_line(lines, heading_index)
    if not metadata_line:
        return None, None

    # Parse the metadata fields into a dictionary
    frontmatter = _parse_metadata_fields(metadata_line, req_id)

    # Validate with Pydantic
    try:
        metadata = RequirementMetadata.model_validate(frontmatter)
        return metadata, None
    except ValidationError as e:
        return None, e


def extract_markdown_references(body):
    """Extract parameter and requirement references from Markdown body."""
    # Resolve reference-style links to inline links first
    try:
        body = markdown_common.resolve_reference_links(body)
    except ValueError:
        # If there are undefined references, just continue with original text
        # The undefined references won't match our patterns anyway
        pass

    param_refs = []
    req_refs = []

    # Extract parameter references using common pattern
    for match in re.finditer(markdown_common.PARAM_REFERENCE_PATTERN, body):
        param_name = match.group(1)
        full_url = match.group(2)
        clean_path, version = path_common.extract_version_from_url(full_url)
        param_refs.append((param_name, clean_path, version))

    # Extract requirement references using common pattern
    for match in re.finditer(markdown_common.REQUIREMENT_REFERENCE_PATTERN, body):
        req_id = match.group(1)
        full_url = match.group(2)
        clean_path, version = path_common.extract_version_from_url(full_url)
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

    # Normalize repository-relative path
    file_path, error = path_common.normalize_repo_path(file_path)
    if error:
        return (False, f"Parameter reference {error}: '{param_path}'")

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
    content, error = file_io_common.read_file_safe(abs_path)
    if error:
        return False, error

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
    # Normalize repository-relative path
    req_path, error = path_common.normalize_repo_path(req_path)
    if error:
        return (False, f"Requirement reference {error}: '{req_path}'")

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
    content, error = file_io_common.read_file_safe(abs_path)
    if error:
        return False, error

    # Parse inline metadata (pipe-separated format)
    metadata, validation_error = parse_inline_metadata_for_requirement(content, req_id)

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

    content, error = file_io_common.read_file_safe(file_path)
    if error:
        return [error]

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
            # Normalize path for dependency checking
            if param_path.startswith("/"):
                normalized_path, _ = path_common.normalize_repo_path(param_path)
            else:
                normalized_path = param_path
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
            # Normalize path for dependency checking
            if req_path.startswith("/"):
                normalized_path, _ = path_common.normalize_repo_path(req_path)
            else:
                normalized_path = req_path
            # Remove fragment if present
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
