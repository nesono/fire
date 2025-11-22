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


def parse_inline_metadata_for_requirement(content, req_id):
    """Parse inline metadata for a specific requirement ID.

    Looks for ## REQ-ID heading followed by a line with pipe-separated fields.
    Format: Key1: value1 | Key2: value2 | Key3: [link](url)
    Returns the parsed metadata as a dict with 'id' and other fields.
    """
    lines = content.split('\n')
    metadata_line = None

    for i, line in enumerate(lines):
        if line.startswith(f'## {req_id}'):
            # The next non-empty line should be the metadata line
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if next_line:
                    # Check if this is a metadata line (contains | or single Key: value)
                    if '|' in next_line:
                        metadata_line = next_line
                        break
                    elif ':' in next_line and not next_line.startswith('#'):
                        # Simple heuristic: metadata lines have key: value format
                        # and the key is a known metadata field (SIL, Sec, Version, Parent)
                        parts = next_line.split(':', 1)
                        key = parts[0].strip().lower()
                        known_fields = ['sil', 'sec', 'version', 'parent']
                        if len(parts) == 2 and key in known_fields:
                            metadata_line = next_line
                            break
                    # If it's not metadata, break (don't keep searching)
                    break
            break

    if not metadata_line:
        return None

    # Parse pipe-separated fields: Key1: value1 | Key2: value2 | Parent: [REQ-ID](path)
    frontmatter = {'id': req_id}

    # Split by | to get individual fields
    fields = metadata_line.split('|')

    for field in fields:
        field = field.strip()
        if not field or ':' not in field:
            continue

        # Split by first : to get key and value
        parts = field.split(':', 1)
        key = parts[0].strip().lower()  # Normalize key to lowercase
        value = parts[1].strip() if len(parts) > 1 else ''

        # Check if value contains a markdown link [text](url)
        if value.startswith('[') and '](' in value:
            # This is a parent reference - extract just the requirement ID
            # Format: [REQ-ID](/path/to/file.md?version=N#REQ-ID)
            match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', value)
            if match:
                frontmatter[key] = value  # Keep full markdown link for parent
                continue

        # Try to parse as int
        if value.isdigit():
            frontmatter[key] = int(value)
        # Parse booleans
        elif value.lower() == 'true':
            frontmatter[key] = True
        elif value.lower() == 'false':
            frontmatter[key] = False
        else:
            frontmatter[key] = value

    return frontmatter


def extract_markdown_references(body):
    """Extract parameter, requirement, and test references from markdown body."""
    param_refs = []
    req_refs = []
    test_refs = []

    # Pattern for [@param](path#param)
    param_pattern = r'\[@([a-zA-Z_][a-zA-Z0-9_]*)\]\(([^)]+)\)'
    for match in re.finditer(param_pattern, body):
        param_name = match.group(1)
        param_path = match.group(2)
        param_refs.append((param_name, param_path))

    # Pattern for [REQ-ID](path.md?version=N#anchor) or [REQ-ID](path.md)
    req_pattern = r'\[([A-Z][A-Z0-9_-]+)\]\(([^)]+\.md[^)]*)\)'
    for match in re.finditer(req_pattern, body):
        req_id = match.group(1)
        full_url = match.group(2)

        # Extract version from query parameter if present
        version = None
        clean_path = full_url
        if '?' in full_url:
            path_part, query_part = full_url.split('?', 1)
            # Extract query string (before # if present)
            query_str = query_part.split('#')[0] if '#' in query_part else query_part
            # Parse version=N
            for param in query_str.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key == 'version' and value.isdigit():
                        version = int(value)
            # Reconstruct clean path with fragment if present
            clean_path = path_part
            if '#' in query_part:
                clean_path = clean_path + '#' + query_part.split('#')[1]

        req_refs.append((req_id, clean_path, version))

    # Pattern for [test_name](//package:target)
    test_pattern = r'\[([a-zA-Z_][a-zA-Z0-9_]*)\]\((//[^)]+:[^)]+)\)'
    for match in re.finditer(test_pattern, body):
        test_name = match.group(1)
        test_label = match.group(2)
        test_refs.append((test_name, test_label))

    return param_refs, req_refs, test_refs


def validate_parameter_reference(param_name, param_path, workspace_root):
    """Validate that a parameter reference exists."""
    # Extract file path and anchor
    if '#' in param_path:
        file_path, anchor = param_path.split('#', 1)
    else:
        file_path = param_path
        anchor = param_name

    # Strip leading slash for repository-relative paths (e.g., /examples/foo.yaml -> examples/foo.yaml)
    # Markdown uses /path for repository-relative, but os.path.join treats it as absolute
    if file_path.startswith('/'):
        file_path = file_path[1:]

    # Check that link text matches anchor
    if param_name != anchor:
        return False, f"Parameter link text '{param_name}' does not match anchor '{anchor}' in {param_path}"

    # Convert to absolute path
    abs_path = os.path.join(workspace_root, file_path)

    # Check if file exists, or try the _validated.yaml version from parameter_library
    if not os.path.exists(abs_path):
        # parameter_library outputs foo_validated.yaml from foo.yaml
        if file_path.endswith('.yaml'):
            validated_path = file_path[:-5] + '_validated.yaml'
            validated_abs_path = os.path.join(workspace_root, validated_path)
            if os.path.exists(validated_abs_path):
                abs_path = validated_abs_path
            else:
                return False, f"Parameter file does not exist: {file_path}"
        else:
            return False, f"Parameter file does not exist: {file_path}"

    # Read file and check if parameter is defined
    try:
        with open(abs_path, 'r') as f:
            content = f.read()

        # Look for parameter definition
        # In YAML, parameters are defined as keys under 'parameters:'
        # e.g., "  param_name:" at the start of a line
        if f'{anchor}:' in content:
            return True, None
        else:
            return False, f"Parameter '{anchor}' not found in {file_path}"

    except Exception as e:
        return False, f"Error reading {file_path}: {e}"


def validate_requirement_reference(req_id, req_path, workspace_root, ref_version=None, source_file=None):
    """Validate that a requirement reference exists and check version if specified."""
    # Strip leading slash for repository-relative paths (e.g., /examples/foo.md -> examples/foo.md)
    # Markdown uses /path for repository-relative, but os.path.join treats it as absolute
    if req_path.startswith('/'):
        req_path = req_path[1:]

    # Remove fragment if present (e.g., path.md#REQ-ID -> path.md)
    path_without_fragment = req_path.split('#')[0] if '#' in req_path else req_path

    # Check that filename has valid extension
    filename = os.path.basename(path_without_fragment)
    if not (filename.endswith('.md') or filename.endswith('.sysreq.md')):
        return False, f"Requirement file must have .md or .sysreq.md extension: {filename}"

    # Convert to absolute path
    abs_path = os.path.join(workspace_root, path_without_fragment)

    # Check if file exists
    if not os.path.exists(abs_path):
        return False, f"Requirement file does not exist: {req_path}"

    # Read file and verify it contains the correct requirement ID
    try:
        with open(abs_path, 'r') as f:
            content = f.read()

        # Parse inline metadata (pipe-separated format)
        frontmatter = parse_inline_metadata_for_requirement(content, req_id)

        if not frontmatter or frontmatter.get('id') != req_id:
            return False, f"Requirement file {req_path} does not contain ID '{req_id}'"

        # Check version if ref_version is specified
        if ref_version is not None:
            actual_version = frontmatter.get('version')
            # ANSI color codes: \033[91m = light red, \033[0m = reset
            # Print to stdout so Bazel shows these warnings even when validation passes
            if actual_version is None:
                print(f"\033[91mWARNING:\033[0m REQUIREMENT VERSION MISMATCH! {source_file}: Reference to {req_id} specifies version={ref_version}, but {path_without_fragment} has no version field")
            elif actual_version != ref_version:
                print(f"\033[91mWARNING:\033[0m REQUIREMENT VERSION MISMATCH! {source_file}: Reference to {req_id} specifies version={ref_version}, but {path_without_fragment} is at version={actual_version}")

        return True, None

    except Exception as e:
        return False, f"Error reading {req_path}: {e}"


def validate_test_reference(test_name, test_label, workspace_root):
    """Validate that a test target exists by checking BUILD file."""
    try:
        # Parse the Bazel label to get package and target
        # Format: //package/path:target_name
        if not test_label.startswith('//'):
            return False, f"Invalid test label format: {test_label}"

        label_parts = test_label[2:].split(':')
        if len(label_parts) != 2:
            return False, f"Invalid test label format (missing :): {test_label}"

        package_path = label_parts[0]
        target_name = label_parts[1]

        # Check that link text matches target name
        if test_name != target_name:
            return False, f"Test link text '{test_name}' does not match target name '{target_name}' in {test_label}"

        # Check if BUILD.bazel or BUILD file exists in the package
        build_file = None
        for build_name in ['BUILD.bazel', 'BUILD']:
            potential_path = os.path.join(workspace_root, package_path, build_name)
            if os.path.exists(potential_path):
                build_file = potential_path
                break

        if not build_file:
            return False, f"No BUILD file found for package: //{package_path}"

        # Read BUILD file and check if target name appears
        with open(build_file, 'r') as f:
            build_content = f.read()

        # Simple check: target name should appear in BUILD file
        # This is not perfect but avoids recursive Bazel invocation
        if f'name = "{target_name}"' in build_content or f"name = '{target_name}'" in build_content:
            return True, None
        else:
            return False, f"Test target '{target_name}' not found in {build_file}"

    except Exception as e:
        return False, f"Error validating test target {test_label}: {e}"


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
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return [f"Error reading {file_path}: {e}"]

    # Extract references from markdown body
    param_refs, req_refs, test_refs = extract_markdown_references(content)

    # Validate parameter references exist
    for param_name, param_path in param_refs:
        # Check if this parameter file is in allowed_deps (strict dependency checking)
        # Only enforce if allowed_deps is not None (i.e., was explicitly passed)
        if allowed_deps is not None:
            # Strip leading slash for comparison
            normalized_path = param_path[1:] if param_path.startswith('/') else param_path
            # Remove fragment if present
            normalized_path = normalized_path.split('#')[0] if '#' in normalized_path else normalized_path

            # Check both the original path and the _validated.yaml version from parameter_library
            validated_path = None
            if normalized_path.endswith('.yaml'):
                validated_path = normalized_path[:-5] + '_validated.yaml'

            if normalized_path not in allowed_deps and (validated_path is None or validated_path not in allowed_deps):
                errors.append(
                    f"{file_path}: References parameter file '{param_path}' which is not in declared dependencies.\n"
                    f"       Add the target containing '{normalized_path}' to 'deps' in your requirement_library().\n"
                    f"       Example: deps = [\":vehicle_params\"]"
                )
                continue  # Skip further validation for this parameter

        valid, error = validate_parameter_reference(param_name, param_path, workspace_root)
        if not valid:
            errors.append(f"{file_path}: {error}")

    # Validate requirement references exist and check versions
    for req_id, req_path, ref_version in req_refs:
        # Check if this requirement is in allowed_deps (strict dependency checking)
        # Only enforce if allowed_deps is not None (i.e., was explicitly passed)
        if allowed_deps is not None:
            # Strip leading slash and fragment for comparison
            normalized_path = req_path[1:] if req_path.startswith('/') else req_path
            normalized_path = normalized_path.split('#')[0] if '#' in normalized_path else normalized_path

            if normalized_path not in allowed_deps:
                errors.append(
                    f"{file_path}: References requirement '{req_path}' which is not in declared dependencies.\n"
                    f"       Add the target containing '{normalized_path}' to 'deps' in your requirement_library().\n"
                    f"       Example: deps = [\":vehicle_requirements\"]"
                )
                continue  # Skip further validation for this requirement

        valid, error = validate_requirement_reference(req_id, req_path, workspace_root, ref_version, file_path)
        if not valid:
            errors.append(f"{file_path}: {error}")

    # Validate test references exist
    for test_name, test_label in test_refs:
        valid, error = validate_test_reference(test_name, test_label, workspace_root)
        if not valid:
            errors.append(f"{file_path}: {error}")

    return errors


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Validate cross-references in requirement documents')
    parser.add_argument('workspace_root', help='Workspace root directory')
    parser.add_argument('--allowed-deps', nargs='*', default=None, help='Allowed dependency file paths')
    parser.add_argument('requirement_files', nargs='+', help='Requirement files to validate')

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
        print(f"Cross-reference validation passed for {len(requirement_files)} requirement(s)")
        sys.exit(0)


if __name__ == "__main__":
    main()
