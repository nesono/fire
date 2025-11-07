#!/usr/bin/env python3
"""Generate requirement reports from markdown files."""

import sys
import re
from pathlib import Path


def parse_simple_yaml(yaml_text):
    """Simple YAML parser for requirement frontmatter."""
    result = {}
    lines = yaml_text.strip().split('\n')

    # Parse into a list of (indent, key, value, is_list_item) tuples
    parsed_lines = []
    for line in lines:
        if not line.strip() or line.strip().startswith('#'):
            continue

        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if stripped.startswith('- '):
            item = stripped[2:].strip()
            if ': ' in item:
                key, value = item.split(': ', 1)
                parsed_lines.append((indent, key.strip(), value.strip().strip('"').strip("'"), 'dict_in_list'))
            else:
                parsed_lines.append((indent, None, item.strip('"').strip("'"), 'list_item'))
        elif ': ' in line:
            key, value = line.split(': ', 1)
            value = value.strip().strip('"').strip("'")
            if value.startswith('[') and value.endswith(']'):
                # Inline list
                items = value[1:-1].split(',')
                items = [item.strip().strip('"').strip("'") for item in items if item.strip()]
                parsed_lines.append((indent, key.strip(), items, 'inline_list'))
            else:
                parsed_lines.append((indent, key.strip(), value, 'key_value'))

    # Build the structure
    stack = [(0, result, None)]  # (indent, object, key)

    i = 0
    while i < len(parsed_lines):
        indent, key, value, line_type = parsed_lines[i]

        # Pop stack to correct level
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        parent_indent, parent_obj, parent_key = stack[-1]

        if line_type == 'key_value':
            if not value:
                # Empty value - peek ahead to see if next is list or dict
                if i + 1 < len(parsed_lines):
                    next_indent, next_key, next_value, next_type = parsed_lines[i + 1]
                    if next_indent > indent:
                        if next_type in ('list_item', 'dict_in_list'):
                            # It's a list
                            if isinstance(parent_obj, dict):
                                if parent_key:
                                    if parent_key not in parent_obj:
                                        parent_obj[parent_key] = {}
                                    parent_obj[parent_key][key] = []
                                    stack.append((next_indent - 1, parent_obj[parent_key], key))
                                else:
                                    parent_obj[key] = []
                                    stack.append((next_indent - 1, parent_obj, key))
                        else:
                            # It's a dict
                            if isinstance(parent_obj, dict):
                                if parent_key:
                                    if parent_key not in parent_obj:
                                        parent_obj[parent_key] = {}
                                    parent_obj[parent_key][key] = {}
                                    stack.append((next_indent - 1, parent_obj[parent_key][key], None))
                                else:
                                    parent_obj[key] = {}
                                    stack.append((next_indent - 1, parent_obj[key], None))
                    else:
                        if isinstance(parent_obj, dict):
                            if parent_key and parent_key in parent_obj:
                                parent_obj[parent_key][key] = ""
                            else:
                                parent_obj[key] = ""
                else:
                    if isinstance(parent_obj, dict):
                        if parent_key and parent_key in parent_obj:
                            parent_obj[parent_key][key] = ""
                        else:
                            parent_obj[key] = ""
            else:
                # Try to parse as int
                try:
                    value = int(value)
                except ValueError:
                    pass
                if isinstance(parent_obj, dict):
                    if parent_key and parent_key in parent_obj and isinstance(parent_obj[parent_key], dict):
                        parent_obj[parent_key][key] = value
                    else:
                        parent_obj[key] = value

        elif line_type == 'inline_list':
            parent_obj[key] = value

        elif line_type == 'list_item':
            if parent_key and isinstance(parent_obj, dict):
                if parent_key not in parent_obj:
                    parent_obj[parent_key] = []
                parent_obj[parent_key].append(value)

        elif line_type == 'dict_in_list':
            if parent_key and isinstance(parent_obj, dict):
                if parent_key not in parent_obj:
                    parent_obj[parent_key] = []
                # Check if we need a new dict
                if not parent_obj[parent_key] or not isinstance(parent_obj[parent_key][-1], dict) or key in parent_obj[parent_key][-1]:
                    parent_obj[parent_key].append({})
                # Parse value as int if possible
                try:
                    value = int(value)
                except ValueError:
                    pass
                parent_obj[parent_key][-1][key] = value

        i += 1

    return result


def parse_requirement_file(file_path):
    """Parse a requirement markdown file and extract frontmatter."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Find frontmatter boundaries
    lines = content.split('\n')
    first_delimiter = None
    second_delimiter = None

    for i, line in enumerate(lines):
        if line.strip() == '---':
            if first_delimiter is None:
                first_delimiter = i
            elif second_delimiter is None:
                second_delimiter = i
                break

    if first_delimiter is None or second_delimiter is None:
        return None

    # Extract and parse frontmatter
    frontmatter_lines = lines[first_delimiter + 1:second_delimiter]
    frontmatter_text = '\n'.join(frontmatter_lines)

    frontmatter = parse_simple_yaml(frontmatter_text)

    if not frontmatter or 'id' not in frontmatter:
        return None

    return (frontmatter['id'], frontmatter)


def generate_traceability_matrix(requirements_data):
    """Generate traceability matrix in markdown."""
    lines = []
    lines.append("# Traceability Matrix")
    lines.append("")
    lines.append("## Requirements → Parameters")
    lines.append("")
    lines.append("| Requirement | Title | Parameters |")
    lines.append("|-------------|-------|------------|")

    for req_id, frontmatter in requirements_data:
        title = frontmatter.get("title", "")
        params = []
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            if "parameters" in frontmatter["references"]:
                params = frontmatter["references"]["parameters"]

        params_str = ", ".join([f"`{p}`" for p in params]) if params else "-"
        lines.append(f"| {req_id} | {title} | {params_str} |")

    lines.append("")
    lines.append("## Requirements → Requirements")
    lines.append("")
    lines.append("| Requirement | Version | Title | Parent Requirements (Version) |")
    lines.append("|-------------|---------|-------|-------------------------------|")

    for req_id, frontmatter in requirements_data:
        title = frontmatter.get("title", "")
        version = frontmatter.get("version", "-")
        reqs = []
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            if "requirements" in frontmatter["references"]:
                req_refs = frontmatter["references"]["requirements"]
                for ref in req_refs:
                    if isinstance(ref, str):
                        reqs.append(ref)
                    elif isinstance(ref, dict) and "id" in ref:
                        if "version" in ref:
                            reqs.append(f"{ref['id']} (v{ref['version']})")
                        else:
                            reqs.append(ref["id"])

        reqs_str = ", ".join(reqs) if reqs else "-"
        lines.append(f"| {req_id} | {version} | {title} | {reqs_str} |")

    lines.append("")
    lines.append("## Requirements → Tests")
    lines.append("")
    lines.append("| Requirement | Title | Tests |")
    lines.append("|-------------|-------|-------|")

    for req_id, frontmatter in requirements_data:
        title = frontmatter.get("title", "")
        tests = []
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            if "tests" in frontmatter["references"]:
                tests = frontmatter["references"]["tests"]

        tests_str = ", ".join([f"`{t}`" for t in tests]) if tests else "-"
        lines.append(f"| {req_id} | {title} | {tests_str} |")

    lines.append("")
    lines.append("## Requirements → Standards")
    lines.append("")
    lines.append("| Requirement | Title | Standards |")
    lines.append("|-------------|-------|-----------|")

    for req_id, frontmatter in requirements_data:
        title = frontmatter.get("title", "")
        standards = []
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            if "standards" in frontmatter["references"]:
                standards = frontmatter["references"]["standards"]

        standards_str = "<br>".join(standards) if standards else "-"
        lines.append(f"| {req_id} | {title} | {standards_str} |")

    return "\n".join(lines)


def generate_coverage_report(requirements_data):
    """Generate coverage report in markdown."""
    lines = []
    lines.append("# Traceability Coverage Report")
    lines.append("")

    total_reqs = len(requirements_data)
    reqs_with_params = 0
    reqs_with_tests = 0
    reqs_with_standards = 0

    for _, frontmatter in requirements_data:
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            refs = frontmatter["references"]
            if "parameters" in refs and refs["parameters"]:
                reqs_with_params += 1
            if "tests" in refs and refs["tests"]:
                reqs_with_tests += 1
            if "standards" in refs and refs["standards"]:
                reqs_with_standards += 1

    param_coverage = (reqs_with_params * 100) // total_reqs if total_reqs > 0 else 0
    test_coverage = (reqs_with_tests * 100) // total_reqs if total_reqs > 0 else 0
    standard_coverage = (reqs_with_standards * 100) // total_reqs if total_reqs > 0 else 0

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count | Coverage |")
    lines.append("|--------|-------|----------|")
    lines.append(f"| Total Requirements | {total_reqs} | 100% |")
    lines.append(f"| Requirements with Parameters | {reqs_with_params} | {param_coverage}% |")
    lines.append(f"| Requirements with Tests | {reqs_with_tests} | {test_coverage}% |")
    lines.append(f"| Requirements with Standards | {reqs_with_standards} | {standard_coverage}% |")
    lines.append("")

    # Requirements without parameter coverage
    lines.append("## Requirements without Parameter Coverage")
    lines.append("")
    missing_params = []
    for req_id, frontmatter in requirements_data:
        has_params = False
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            if "parameters" in frontmatter["references"] and frontmatter["references"]["parameters"]:
                has_params = True
        if not has_params:
            missing_params.append((req_id, frontmatter.get("title", "")))

    if missing_params:
        for req_id, title in missing_params:
            lines.append(f"- **{req_id}**: {title}")
    else:
        lines.append("*All requirements have parameter coverage*")

    lines.append("")

    # Requirements without test coverage
    lines.append("## Requirements without Test Coverage")
    lines.append("")
    missing_tests = []
    for req_id, frontmatter in requirements_data:
        has_tests = False
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            if "tests" in frontmatter["references"] and frontmatter["references"]["tests"]:
                has_tests = True
        if not has_tests:
            missing_tests.append((req_id, frontmatter.get("title", "")))

    if missing_tests:
        for req_id, title in missing_tests:
            lines.append(f"- **{req_id}**: {title}")
    else:
        lines.append("*All requirements have test coverage*")

    return "\n".join(lines)


def generate_change_impact(requirements_data):
    """Generate change impact analysis in markdown."""
    lines = []
    lines.append("# Change Impact Analysis")
    lines.append("")
    lines.append("This report identifies requirements that may need review due to parent requirement changes.")
    lines.append("")

    # Build version map
    req_versions = {}
    for req_id, frontmatter in requirements_data:
        if "version" in frontmatter:
            req_versions[req_id] = frontmatter["version"]

    # Find stale requirements
    stale_requirements = []
    for req_id, frontmatter in requirements_data:
        if "references" not in frontmatter or not isinstance(frontmatter["references"], dict):
            continue
        if "requirements" not in frontmatter["references"]:
            continue

        req_refs = frontmatter["references"]["requirements"]
        stale_parents = []

        for ref in req_refs:
            if isinstance(ref, dict) and "id" in ref and "version" in ref:
                parent_id = ref["id"]
                tracked_version = ref["version"]

                if parent_id in req_versions:
                    current_version = req_versions[parent_id]
                    if current_version != tracked_version:
                        stale_parents.append({
                            "id": parent_id,
                            "tracked": tracked_version,
                            "current": current_version,
                        })

        if stale_parents:
            stale_requirements.append({
                "id": req_id,
                "title": frontmatter.get("title", ""),
                "version": frontmatter.get("version", "-"),
                "stale_parents": stale_parents,
            })

    if stale_requirements:
        lines.append("## ⚠️ Requirements with Stale Parent References")
        lines.append("")
        lines.append("The following requirements track parent versions that have changed:")
        lines.append("")

        for req in stale_requirements:
            lines.append(f"### {req['id']} (v{req['version']})")
            lines.append("")
            lines.append(f"**Title**: {req['title']}")
            lines.append("")
            lines.append("**Stale Parent References**:")
            lines.append("")
            for parent in req["stale_parents"]:
                lines.append(f"- **{parent['id']}**: Tracking v{parent['tracked']}, but current version is v{parent['current']}")
            lines.append("")
            lines.append("**Action Required**: Review and update this requirement to align with parent changes, then update the parent version reference.")
            lines.append("")
    else:
        lines.append("## ✅ All Requirements Up-to-Date")
        lines.append("")
        lines.append("No requirements found with stale parent references. All tracked parent versions match current versions.")
        lines.append("")

    return "\n".join(lines)


def generate_compliance_report(requirements_data, standard_name):
    """Generate compliance report in markdown."""
    lines = []
    lines.append(f"# Compliance Report: {standard_name}")
    lines.append("")
    lines.append(f"This report summarizes compliance coverage for {standard_name}.")
    lines.append("")

    # Categorize requirements
    safety_reqs = []
    functional_reqs = []
    reqs_with_standard = []
    reqs_with_tests = []

    for req_id, frontmatter in requirements_data:
        req_type = frontmatter.get("type", "")

        if req_type == "safety":
            safety_reqs.append((req_id, frontmatter))
        elif req_type == "functional":
            functional_reqs.append((req_id, frontmatter))

        # Check standard reference
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            if "standards" in frontmatter["references"]:
                standards = frontmatter["references"]["standards"]
                for std in standards:
                    if standard_name.lower() in std.lower():
                        reqs_with_standard.append((req_id, frontmatter))
                        break

        # Check test coverage
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            if "tests" in frontmatter["references"] and frontmatter["references"]["tests"]:
                reqs_with_tests.append((req_id, frontmatter))

    total_reqs = len(requirements_data)
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count | Percentage |")
    lines.append("|--------|-------|------------|")
    lines.append(f"| Total Requirements | {total_reqs} | 100% |")
    lines.append(f"| Safety Requirements | {len(safety_reqs)} | {(len(safety_reqs) * 100) // total_reqs if total_reqs > 0 else 0}% |")
    lines.append(f"| Functional Requirements | {len(functional_reqs)} | {(len(functional_reqs) * 100) // total_reqs if total_reqs > 0 else 0}% |")
    lines.append(f"| Requirements Referencing {standard_name} | {len(reqs_with_standard)} | {(len(reqs_with_standard) * 100) // total_reqs if total_reqs > 0 else 0}% |")
    lines.append(f"| Requirements with Test Coverage | {len(reqs_with_tests)} | {(len(reqs_with_tests) * 100) // total_reqs if total_reqs > 0 else 0}% |")
    lines.append("")

    # Requirements by status
    status_counts = {}
    for _, frontmatter in requirements_data:
        status = frontmatter.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    lines.append("## Requirements by Status")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    for status in ["draft", "proposed", "approved", "implemented", "verified", "deprecated"]:
        count = status_counts.get(status, 0)
        if count > 0:
            lines.append(f"| {status.capitalize()} | {count} |")
    lines.append("")

    # Safety requirements detail
    if safety_reqs:
        lines.append("## Safety Requirements (ASIL Classification)")
        lines.append("")
        lines.append("| Requirement | Title | Priority | Status | Test Coverage | Standard Reference |")
        lines.append("|-------------|-------|----------|--------|---------------|-------------------|")

        for req_id, frontmatter in safety_reqs:
            title = frontmatter.get("title", "")
            priority = frontmatter.get("priority", "-")
            status = frontmatter.get("status", "-")

            has_tests = "✅"
            if "references" in frontmatter and isinstance(frontmatter["references"], dict):
                if "tests" in frontmatter["references"] and frontmatter["references"]["tests"]:
                    has_tests = "✅"
                else:
                    has_tests = "❌"
            else:
                has_tests = "❌"

            has_standard = "❌"
            if "references" in frontmatter and isinstance(frontmatter["references"], dict):
                if "standards" in frontmatter["references"]:
                    standards = frontmatter["references"]["standards"]
                    for std in standards:
                        if standard_name.lower() in std.lower():
                            has_standard = "✅"
                            break

            lines.append(f"| {req_id} | {title} | {priority} | {status} | {has_tests} | {has_standard} |")
        lines.append("")

    # Compliance gaps
    lines.append("## Compliance Gaps")
    lines.append("")

    # Safety requirements without test coverage
    safety_without_tests = []
    for req_id, frontmatter in safety_reqs:
        has_tests = False
        if "references" in frontmatter and isinstance(frontmatter["references"], dict):
            if "tests" in frontmatter["references"] and frontmatter["references"]["tests"]:
                has_tests = True
        if not has_tests:
            safety_without_tests.append((req_id, frontmatter.get("title", "")))

    if safety_without_tests:
        lines.append(f"### ⚠️ Safety Requirements without Test Coverage")
        lines.append("")
        for req_id, title in safety_without_tests:
            lines.append(f"- **{req_id}**: {title}")
        lines.append("")
    else:
        lines.append("### ✅ All Safety Requirements have Test Coverage")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 4:
        print("Usage: generate_report.py <report_type> <output_file> <input_files...> [--standard=NAME]")
        sys.exit(1)

    report_type = sys.argv[1]
    output_file = sys.argv[2]
    input_files = []
    standard = "ISO 26262"

    for arg in sys.argv[3:]:
        if arg.startswith("--standard="):
            standard = arg.split("=", 1)[1]
        else:
            input_files.append(arg)

    # Parse all requirement files
    requirements_data = []
    for file_path in input_files:
        parsed = parse_requirement_file(file_path)
        if parsed:
            requirements_data.append(parsed)

    # Generate report
    if report_type == "traceability":
        report = generate_traceability_matrix(requirements_data)
    elif report_type == "coverage":
        report = generate_coverage_report(requirements_data)
    elif report_type == "change_impact":
        report = generate_change_impact(requirements_data)
    elif report_type == "compliance":
        report = generate_compliance_report(requirements_data, standard)
    else:
        print(f"Unknown report type: {report_type}")
        sys.exit(1)

    # Write output
    with open(output_file, 'w') as f:
        f.write(report)
        f.write("\n")


if __name__ == "__main__":
    main()
