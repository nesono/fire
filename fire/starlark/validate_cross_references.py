#!/usr/bin/env python3
"""Validates that cross-references in requirements actually exist.

ARCHITECTURE NOTE:
This Python file is a THIN WRAPPER for file I/O only. The validation logic
is defined in Starlark files which are the source of truth:

  - fire/starlark/reference_validator.bzl    (frontmatter validation)
  - fire/starlark/markdown_parser.bzl        (body reference validation)
  - fire/starlark/requirement_validator.bzl  (YAML parsing)

This Python implementation mirrors that Starlark logic to enable build-time
validation via file I/O. When updating validation rules, update the Starlark
files first, then mirror changes here.

WHY PYTHON?: Starlark rules cannot directly read arbitrary files during build.
Python handles file I/O and applies the same validation rules defined in Starlark.
"""

import os
import re
import sys


def parse_inline_yaml_for_requirement(content, req_id):
    """Parse inline YAML block for a specific requirement ID.

    Looks for ## REQ-ID heading followed by ```yaml block.
    Returns the parsed YAML as a dict with 'id' and other fields.
    """
    lines = content.split('\n')
    in_req_section = False
    in_yaml_block = False
    yaml_lines = []

    for i, line in enumerate(lines):
        if line.startswith(f'## {req_id}'):
            in_req_section = True
            continue

        if in_req_section:
            if line.startswith('## ') and not line.startswith(f'## {req_id}'):
                # Hit next section, stop
                break

            if line.strip() == '```yaml':
                in_yaml_block = True
                continue

            if in_yaml_block:
                if line.strip() == '```':
                    # End of YAML block
                    break
                yaml_lines.append(line)

    if not yaml_lines:
        return None

    # Parse simple YAML key: value pairs
    frontmatter = {'id': req_id}  # Add the ID from the heading
    for line in yaml_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if ':' in stripped:
            parts = stripped.split(':', 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ''

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
    current_dict_item = None
    base_indent = 0

    for i in range(1, end_idx):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip())

        # List item
        if stripped.startswith("-"):
            rest = stripped[1:].strip()

            # Check if next line (if exists) is indented more - indicates a multi-line dict item
            is_multiline_dict = False
            if i + 1 < end_idx:
                next_line = lines[i + 1]
                next_stripped = next_line.strip()
                if next_stripped and not next_stripped.startswith("-"):
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent > indent and ":" in next_stripped:
                        is_multiline_dict = True

            # Check if this is a dict item (either multi-line or single-line)
            # Dict items have format "- key: value" where key is a dict-like key (path, version, etc.)
            # NOT Bazel labels (//...:...) or ISO standards (ISO ...:...)
            is_dict_item = False
            if ":" in rest and not rest.startswith("//") and not rest.startswith("ISO "):
                # Check if this looks like a dict key (starts with alphanumeric word followed by colon)
                parts = rest.split(":", 1)
                potential_key = parts[0].strip()
                # Common dict keys we expect: path, version, description, etc.
                if potential_key.replace("_", "").replace("-", "").isalnum():
                    is_dict_item = True

            if is_dict_item:
                parts = rest.split(":", 1)
                dict_key = parts[0].strip()
                dict_value = parts[1].strip() if len(parts) > 1 else ""

                # Start a new dict item (or continue multi-line dict)
                if is_multiline_dict:
                    current_dict_item = {dict_key: dict_value}
                    if current_key and current_list and isinstance(frontmatter[current_key], dict):
                        if current_list not in frontmatter[current_key]:
                            frontmatter[current_key][current_list] = []
                        frontmatter[current_key][current_list].append(current_dict_item)
                else:
                    # Single-line dict item
                    single_dict = {dict_key: dict_value}
                    if current_key and current_list and isinstance(frontmatter[current_key], dict):
                        if current_list not in frontmatter[current_key]:
                            frontmatter[current_key][current_list] = []
                        frontmatter[current_key][current_list].append(single_dict)
                    current_dict_item = None  # Don't expect continuation
            else:
                # Simple string item (even if it contains ':')
                if current_key and current_list and isinstance(frontmatter[current_key], dict):
                    if current_list not in frontmatter[current_key]:
                        frontmatter[current_key][current_list] = []
                    frontmatter[current_key][current_list].append(rest)
                    current_dict_item = None

        # Key-value pair
        elif ":" in stripped:
            parts = stripped.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            if indent == 0 or indent == base_indent:
                # Top-level key (or back to base level)
                current_key = key
                if value:
                    frontmatter[key] = value
                else:
                    frontmatter[key] = {}
                    current_list = None
                base_indent = indent
                current_dict_item = None
            elif current_dict_item is not None and indent > base_indent + 2:
                # Additional key in the current dict item (must be indented beyond list level)
                current_dict_item[key] = value
            elif current_key and indent > base_indent:
                # Nested key under current_key
                current_dict_item = None  # Exit dict mode when we see a new nested key
                if value:
                    if isinstance(frontmatter[current_key], dict):
                        frontmatter[current_key][key] = value
                else:
                    if isinstance(frontmatter[current_key], dict):
                        frontmatter[current_key][key] = []
                        current_list = key

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

    # Strip leading slash for repository-relative paths (e.g., /examples/foo.bzl -> examples/foo.bzl)
    # Markdown uses /path for repository-relative, but os.path.join treats it as absolute
    if file_path.startswith('/'):
        file_path = file_path[1:]

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

        # Try to parse frontmatter first (for traditional frontmatter style)
        frontmatter, _ = parse_frontmatter(content)

        # If no frontmatter, try parsing inline YAML block (for ## REQ-ID style)
        if not frontmatter or frontmatter.get('id') != req_id:
            frontmatter = parse_inline_yaml_for_requirement(content, req_id)

        if not frontmatter or frontmatter.get('id') != req_id:
            return False, f"Requirement file {req_path} does not contain ID '{req_id}'"

        # Check version if ref_version is specified
        if ref_version is not None:
            actual_version = frontmatter.get('version')
            if actual_version is None:
                print(f"WARNING: {source_file}: Reference to {req_id} specifies version={ref_version}, but {path_without_fragment} has no version field")
            elif actual_version != ref_version:
                print(f"WARNING: {source_file}: Reference to {req_id} specifies version={ref_version}, but {path_without_fragment} is at version={actual_version}")

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


def validate_requirement_file(file_path, workspace_root):
    """Validate all cross-references in a single requirement file."""
    errors = []

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return [f"Error reading {file_path}: {e}"]

    frontmatter, body = parse_frontmatter(content)

    # Extract references from markdown body (even if no frontmatter)
    if not frontmatter:
        body = content  # Use full content as body if no frontmatter
    param_refs, req_refs, test_refs = extract_markdown_references(body)

    # Only do frontmatter validation if frontmatter exists
    if frontmatter:
        # Extract frontmatter references
        fm_refs = frontmatter.get('references', {})

        # Check lexicographic sorting of frontmatter references
        for ref_type in ['parameters', 'tests', 'standards']:
            ref_list = fm_refs.get(ref_type, [])
            if not ref_list:
                continue

            # Extract sortable values (skip dict items)
            sortable_items = []
            for item in ref_list:
                if isinstance(item, dict):
                    # For dict items, use the 'path' key if available, otherwise skip
                    if 'path' in item:
                        sortable_items.append(item['path'])
                else:
                    sortable_items.append(item)

            # Check if sorted
            sorted_items = sorted(sortable_items)
            if sortable_items != sorted_items:
                errors.append(
                    f"{file_path}: Frontmatter '{ref_type}' references are not sorted lexicographically.\n"
                    f"  Current order: {sortable_items}\n"
                    f"  Expected order: {sorted_items}"
                )

        # Check requirements separately (must be dicts with 'path' and 'version' keys)
        req_list = fm_refs.get('requirements', [])
        if req_list:
            sortable_reqs = []
            for i, req_ref in enumerate(req_list):
                if isinstance(req_ref, dict):
                    # Require both 'path' and 'version'
                    if 'path' not in req_ref:
                        errors.append(f"{file_path}: Requirement reference #{i+1} missing 'path' key")
                    if 'version' not in req_ref:
                        errors.append(f"{file_path}: Requirement reference #{i+1} missing 'version' key (path: {req_ref.get('path', 'unknown')})")
                    sortable_reqs.append(req_ref.get('path', ''))
                else:
                    # Requirement references must be dicts with path and version
                    errors.append(
                        f"{file_path}: Requirement reference '{req_ref}' must use dict format with 'path' and 'version' keys.\n"
                        f"  Example format:\n"
                        f"    - path: {req_ref}\n"
                        f"      version: 1"
                    )
                    sortable_reqs.append(req_ref)

            sorted_reqs = sorted(sortable_reqs)
            if sortable_reqs != sorted_reqs:
                errors.append(
                    f"{file_path}: Frontmatter 'requirements' references are not sorted lexicographically.\n"
                    f"  Current order: {sortable_reqs}\n"
                    f"  Expected order: {sorted_reqs}"
                )

        # Extract parameters (handle both string and dict formats)
        fm_params = set()
        for param_ref in fm_refs.get('parameters', []):
            if isinstance(param_ref, dict):
                # Skip dict items for now (shouldn't happen for parameters)
                continue
            else:
                fm_params.add(param_ref)

        # Extract requirement paths from frontmatter (handle both string and dict formats)
        fm_reqs = set()
        for req_ref in fm_refs.get('requirements', []):
            if isinstance(req_ref, dict):
                fm_reqs.add(req_ref.get('path', ''))
            else:
                fm_reqs.add(req_ref)

        # Extract tests (handle both string and dict formats)
        fm_tests = set()
        for test_ref in fm_refs.get('tests', []):
            if isinstance(test_ref, dict):
                # Skip dict items for now (shouldn't happen for tests)
                continue
            else:
                fm_tests.add(test_ref)

        # Build sets of body references
        body_params = set(param_path for _, param_path in param_refs)
        body_reqs = set(req_path for _, req_path, _ in req_refs)
        body_tests = set(test_label for _, test_label in test_refs)

        # Check bi-directional consistency: all body refs must be in frontmatter
        for param_path in body_params:
            if param_path not in fm_params:
                errors.append(f"{file_path}: Body references parameter '{param_path}' not declared in frontmatter")

        for req_path in body_reqs:
            if req_path not in fm_reqs:
                errors.append(f"{file_path}: Body references requirement '{req_path}' not declared in frontmatter")

        for test_label in body_tests:
            if test_label not in fm_tests:
                errors.append(f"{file_path}: Body references test '{test_label}' not declared in frontmatter")

        # Check reverse: all frontmatter refs must be used in body
        for param_path in fm_params:
            if param_path not in body_params:
                errors.append(f"{file_path}: Frontmatter declares parameter '{param_path}' but it's not used in body")

        for req_path in fm_reqs:
            if req_path and req_path not in body_reqs:
                errors.append(f"{file_path}: Frontmatter declares requirement '{req_path}' but it's not used in body")

        for test_label in fm_tests:
            if test_label not in body_tests:
                errors.append(f"{file_path}: Frontmatter declares test '{test_label}' but it's not used in body")

    # Validate parameter references exist
    for param_name, param_path in param_refs:
        valid, error = validate_parameter_reference(param_name, param_path, workspace_root)
        if not valid:
            errors.append(f"{file_path}: {error}")

    # Validate requirement references exist and check versions
    for req_id, req_path, ref_version in req_refs:
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
