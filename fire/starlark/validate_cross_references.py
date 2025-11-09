#!/usr/bin/env python3
"""Validates that cross-references in requirements actually exist."""

import os
import re
import sys


def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return None, content

    lines = content.split("\n")
    if len(lines) < 3:
        return None, content

    # Find closing ---
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return None, content

    # Simple YAML parsing for references section
    frontmatter = {}
    current_key = None
    current_list = None
    indent_level = 0

    for i in range(1, end_idx):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip())

        # Top-level key
        if ":" in stripped and not stripped.startswith("-"):
            parts = stripped.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            if indent == 0:
                current_key = key
                if value:
                    frontmatter[key] = value
                else:
                    frontmatter[key] = {}
                    current_list = None
                indent_level = indent
            elif current_key and indent > indent_level:
                # Nested key under current_key
                if value:
                    if isinstance(frontmatter[current_key], dict):
                        frontmatter[current_key][key] = value
                else:
                    if isinstance(frontmatter[current_key], dict):
                        frontmatter[current_key][key] = []
                        current_list = key

        # List item
        elif stripped.startswith("-"):
            item = stripped[1:].strip()
            if current_key and current_list and isinstance(frontmatter[current_key], dict):
                if current_list not in frontmatter[current_key]:
                    frontmatter[current_key][current_list] = []
                frontmatter[current_key][current_list].append(item)

    body = "\n".join(lines[end_idx + 1:])
    return frontmatter, body


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

    # Pattern for [REQ-ID](path)
    req_pattern = r'\[([A-Z][A-Z0-9_-]+)\]\(([^)]+\.md)\)'
    for match in re.finditer(req_pattern, body):
        req_id = match.group(1)
        req_path = match.group(2)
        req_refs.append((req_id, req_path))

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

    # Check that link text matches anchor
    if param_name != anchor:
        return False, f"Parameter link text '{param_name}' does not match anchor '{anchor}' in {param_path}"

    # Convert to absolute path
    abs_path = os.path.join(workspace_root, file_path)

    # Check if file exists
    if not os.path.exists(abs_path):
        return False, f"Parameter file does not exist: {file_path}"

    # Read file and check if parameter is defined
    try:
        with open(abs_path, 'r') as f:
            content = f.read()

        # Look for parameter definition (simple check for the parameter name)
        # In Starlark, parameters are defined like: "param_name": {...}
        if f'"{anchor}"' in content or f"'{anchor}'" in content:
            return True, None
        else:
            return False, f"Parameter '{anchor}' not found in {file_path}"

    except Exception as e:
        return False, f"Error reading {file_path}: {e}"


def validate_requirement_reference(req_id, req_path, workspace_root):
    """Validate that a requirement reference exists."""
    # Check that link text matches filename
    filename = os.path.basename(req_path)
    expected_filename = f"{req_id}.md"
    if filename != expected_filename:
        return False, f"Requirement link text '{req_id}' does not match filename '{filename}' (expected '{expected_filename}')"

    # Convert to absolute path
    abs_path = os.path.join(workspace_root, req_path)

    # Check if file exists
    if not os.path.exists(abs_path):
        return False, f"Requirement file does not exist: {req_path}"

    # Read file and verify it contains the correct requirement ID
    try:
        with open(abs_path, 'r') as f:
            content = f.read()

        frontmatter, _ = parse_frontmatter(content)
        if frontmatter and frontmatter.get('id') == req_id:
            return True, None
        else:
            return False, f"Requirement file {req_path} does not contain ID '{req_id}'"

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


def validate_requirement_file(file_path, workspace_root):
    """Validate all cross-references in a single requirement file."""
    errors = []

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return [f"Error reading {file_path}: {e}"]

    frontmatter, body = parse_frontmatter(content)

    if not frontmatter:
        # No frontmatter, skip validation
        return []

    # Extract references from markdown body
    param_refs, req_refs, test_refs = extract_markdown_references(body)

    # Validate parameter references
    for param_name, param_path in param_refs:
        valid, error = validate_parameter_reference(param_name, param_path, workspace_root)
        if not valid:
            errors.append(f"{file_path}: {error}")

    # Validate requirement references
    for req_id, req_path in req_refs:
        valid, error = validate_requirement_reference(req_id, req_path, workspace_root)
        if not valid:
            errors.append(f"{file_path}: {error}")

    # Validate test references
    for test_name, test_label in test_refs:
        valid, error = validate_test_reference(test_name, test_label, workspace_root)
        if not valid:
            errors.append(f"{file_path}: {error}")

    return errors


def main():
    if len(sys.argv) < 3:
        print("Usage: validate_cross_references.py <workspace_root> <requirement_files...>")
        sys.exit(1)

    workspace_root = sys.argv[1]
    requirement_files = sys.argv[2:]

    all_errors = []

    for req_file in requirement_files:
        errors = validate_requirement_file(req_file, workspace_root)
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
