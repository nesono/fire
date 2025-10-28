"""Traceability analysis and matrix generation."""

def _generate_traceability_matrix_markdown(requirements_data):
    """Generate a traceability matrix in Markdown format.

    Args:
        requirements_data: List of (id, frontmatter) tuples

    Returns:
        Markdown string containing traceability matrix
    """
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
        if "references" in frontmatter and "parameters" in frontmatter["references"]:
            params = frontmatter["references"]["parameters"]

        params_str = ", ".join(["`{}`".format(p) for p in params]) if params else "-"
        lines.append("| {} | {} | {} |".format(req_id, title, params_str))

    lines.append("")
    lines.append("## Requirements → Requirements")
    lines.append("")
    lines.append("| Requirement | Title | Related Requirements |")
    lines.append("|-------------|-------|----------------------|")

    for req_id, frontmatter in requirements_data:
        title = frontmatter.get("title", "")
        reqs = []
        if "references" in frontmatter and "requirements" in frontmatter["references"]:
            reqs = frontmatter["references"]["requirements"]

        reqs_str = ", ".join(reqs) if reqs else "-"
        lines.append("| {} | {} | {} |".format(req_id, title, reqs_str))

    lines.append("")
    lines.append("## Requirements → Tests")
    lines.append("")
    lines.append("| Requirement | Title | Tests |")
    lines.append("|-------------|-------|-------|")

    for req_id, frontmatter in requirements_data:
        title = frontmatter.get("title", "")
        tests = []
        if "references" in frontmatter and "tests" in frontmatter["references"]:
            tests = frontmatter["references"]["tests"]

        tests_str = ", ".join(["`{}`".format(t) for t in tests]) if tests else "-"
        lines.append("| {} | {} | {} |".format(req_id, title, tests_str))

    lines.append("")
    lines.append("## Requirements → Standards")
    lines.append("")
    lines.append("| Requirement | Title | Standards |")
    lines.append("|-------------|-------|-----------|")

    for req_id, frontmatter in requirements_data:
        title = frontmatter.get("title", "")
        standards = []
        if "references" in frontmatter and "standards" in frontmatter["references"]:
            standards = frontmatter["references"]["standards"]

        standards_str = "<br>".join(standards) if standards else "-"
        lines.append("| {} | {} | {} |".format(req_id, title, standards_str))

    return "\n".join(lines)

def _generate_coverage_report_markdown(requirements_data):
    """Generate a coverage report in Markdown format.

    Args:
        requirements_data: List of (id, frontmatter) tuples

    Returns:
        Markdown string containing coverage report
    """
    lines = []
    lines.append("# Traceability Coverage Report")
    lines.append("")

    # Count coverages
    total_reqs = len(requirements_data)
    reqs_with_params = 0
    reqs_with_tests = 0
    reqs_with_standards = 0

    for _, frontmatter in requirements_data:
        if "references" in frontmatter:
            refs = frontmatter["references"]
            if "parameters" in refs and refs["parameters"]:
                reqs_with_params += 1
            if "tests" in refs and refs["tests"]:
                reqs_with_tests += 1
            if "standards" in refs and refs["standards"]:
                reqs_with_standards += 1

    # Calculate percentages
    param_coverage = (reqs_with_params * 100) // total_reqs if total_reqs > 0 else 0
    test_coverage = (reqs_with_tests * 100) // total_reqs if total_reqs > 0 else 0
    standard_coverage = (reqs_with_standards * 100) // total_reqs if total_reqs > 0 else 0

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count | Coverage |")
    lines.append("|--------|-------|----------|")
    lines.append("| Total Requirements | {} | 100% |".format(total_reqs))
    lines.append("| Requirements with Parameters | {} | {}% |".format(reqs_with_params, param_coverage))
    lines.append("| Requirements with Tests | {} | {}% |".format(reqs_with_tests, test_coverage))
    lines.append("| Requirements with Standards | {} | {}% |".format(reqs_with_standards, standard_coverage))
    lines.append("")

    # Requirements without parameter coverage
    lines.append("## Requirements without Parameter Coverage")
    lines.append("")
    missing_params = []
    for req_id, frontmatter in requirements_data:
        has_params = False
        if "references" in frontmatter and "parameters" in frontmatter["references"]:
            if frontmatter["references"]["parameters"]:
                has_params = True
        if not has_params:
            missing_params.append((req_id, frontmatter.get("title", "")))

    if missing_params:
        for req_id, title in missing_params:
            lines.append("- **{}**: {}".format(req_id, title))
    else:
        lines.append("*All requirements have parameter coverage*")

    lines.append("")

    # Requirements without test coverage
    lines.append("## Requirements without Test Coverage")
    lines.append("")
    missing_tests = []
    for req_id, frontmatter in requirements_data:
        has_tests = False
        if "references" in frontmatter and "tests" in frontmatter["references"]:
            if frontmatter["references"]["tests"]:
                has_tests = True
        if not has_tests:
            missing_tests.append((req_id, frontmatter.get("title", "")))

    if missing_tests:
        for req_id, title in missing_tests:
            lines.append("- **{}**: {}".format(req_id, title))
    else:
        lines.append("*All requirements have test coverage*")

    return "\n".join(lines)

# Export functions
traceability = struct(
    generate_matrix_markdown = _generate_traceability_matrix_markdown,
    generate_coverage_markdown = _generate_coverage_report_markdown,
)
