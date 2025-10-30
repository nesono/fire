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
    lines.append("| Requirement | Version | Title | Parent Requirements (Version) |")
    lines.append("|-------------|---------|-------|-------------------------------|")

    for req_id, frontmatter in requirements_data:
        title = frontmatter.get("title", "")
        version = frontmatter.get("version", "-")
        reqs = []
        if "references" in frontmatter and "requirements" in frontmatter["references"]:
            req_refs = frontmatter["references"]["requirements"]

            # Handle both string and dict formats
            for ref in req_refs:
                if type(ref) == "string":
                    reqs.append(ref)
                elif type(ref) == "dict" and "id" in ref:
                    # Include version if present
                    if "version" in ref:
                        reqs.append("{} (v{})".format(ref["id"], ref["version"]))
                    else:
                        reqs.append(ref["id"])

        reqs_str = ", ".join(reqs) if reqs else "-"
        lines.append("| {} | {} | {} | {} |".format(req_id, version, title, reqs_str))

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

def _generate_change_impact_report(requirements_data):
    """Generate a change impact analysis report.

    Identifies requirements that may be stale due to parent version changes.

    Args:
        requirements_data: List of (id, frontmatter) tuples

    Returns:
        Markdown string containing change impact analysis
    """
    lines = []
    lines.append("# Change Impact Analysis")
    lines.append("")
    lines.append("This report identifies requirements that may need review due to parent requirement changes.")
    lines.append("")

    # Build a map of requirement ID -> current version
    req_versions = {}
    for req_id, frontmatter in requirements_data:
        if "version" in frontmatter:
            req_versions[req_id] = frontmatter["version"]

    # Find requirements with stale parent references
    stale_requirements = []
    for req_id, frontmatter in requirements_data:
        if "references" not in frontmatter or "requirements" not in frontmatter["references"]:
            continue

        req_refs = frontmatter["references"]["requirements"]
        stale_parents = []

        for ref in req_refs:
            if type(ref) == "dict" and "id" in ref and "version" in ref:
                parent_id = ref["id"]
                tracked_version = ref["version"]

                # Check if parent exists and has a different version
                if parent_id in req_versions:
                    current_version = req_versions[parent_id]
                    if current_version != tracked_version:
                        stale_parents.append({
                            "current": current_version,
                            "id": parent_id,
                            "tracked": tracked_version,
                        })

        if stale_parents:
            stale_requirements.append({
                "id": req_id,
                "stale_parents": stale_parents,
                "title": frontmatter.get("title", ""),
                "version": frontmatter.get("version", "-"),
            })

    # Report stale requirements
    if stale_requirements:
        lines.append("## ⚠️ Requirements with Stale Parent References")
        lines.append("")
        lines.append("The following requirements track parent versions that have changed:")
        lines.append("")

        for req in stale_requirements:
            lines.append("### {} (v{})".format(req["id"], req["version"]))
            lines.append("")
            lines.append("**Title**: {}".format(req["title"]))
            lines.append("")
            lines.append("**Stale Parent References**:")
            lines.append("")
            for parent in req["stale_parents"]:
                lines.append("- **{}**: Tracking v{}, but current version is v{}".format(
                    parent["id"],
                    parent["tracked"],
                    parent["current"],
                ))
            lines.append("")
            lines.append("**Action Required**: Review and update this requirement to align with parent changes, then update the parent version reference.")
            lines.append("")
    else:
        lines.append("## ✅ All Requirements Up-to-Date")
        lines.append("")
        lines.append("No requirements found with stale parent references. All tracked parent versions match current versions.")
        lines.append("")

    return "\n".join(lines)

def _generate_compliance_report(requirements_data, standard_name = "ISO 26262"):
    """Generate a compliance report for a specific standard.

    Args:
        requirements_data: List of (id, frontmatter) tuples
        standard_name: Name of the standard to check compliance against

    Returns:
        Markdown string containing compliance report
    """
    lines = []
    lines.append("# Compliance Report: {}".format(standard_name))
    lines.append("")
    lines.append("This report summarizes compliance coverage for {}.".format(standard_name))
    lines.append("")

    # Categorize requirements
    safety_reqs = []
    functional_reqs = []
    other_reqs = []
    reqs_with_standard = []
    reqs_with_tests = []

    for req_id, frontmatter in requirements_data:
        req_type = frontmatter.get("type", "")
        status = frontmatter.get("status", "")
        priority = frontmatter.get("priority", "")

        # Categorize by type
        if req_type == "safety":
            safety_reqs.append((req_id, frontmatter))
        elif req_type == "functional":
            functional_reqs.append((req_id, frontmatter))
        else:
            other_reqs.append((req_id, frontmatter))

        # Check standard reference
        if "references" in frontmatter and "standards" in frontmatter["references"]:
            standards = frontmatter["references"]["standards"]
            for std in standards:
                if standard_name.lower() in std.lower():
                    reqs_with_standard.append((req_id, frontmatter))
                    break

        # Check test coverage
        if "references" in frontmatter and "tests" in frontmatter["references"]:
            if frontmatter["references"]["tests"]:
                reqs_with_tests.append((req_id, frontmatter))

    # Summary statistics
    total_reqs = len(requirements_data)
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count | Percentage |")
    lines.append("|--------|-------|------------|")
    lines.append("| Total Requirements | {} | 100% |".format(total_reqs))
    lines.append("| Safety Requirements | {} | {}% |".format(
        len(safety_reqs),
        (len(safety_reqs) * 100) // total_reqs if total_reqs > 0 else 0,
    ))
    lines.append("| Functional Requirements | {} | {}% |".format(
        len(functional_reqs),
        (len(functional_reqs) * 100) // total_reqs if total_reqs > 0 else 0,
    ))
    lines.append("| Requirements Referencing {} | {} | {}% |".format(
        standard_name,
        len(reqs_with_standard),
        (len(reqs_with_standard) * 100) // total_reqs if total_reqs > 0 else 0,
    ))
    lines.append("| Requirements with Test Coverage | {} | {}% |".format(
        len(reqs_with_tests),
        (len(reqs_with_tests) * 100) // total_reqs if total_reqs > 0 else 0,
    ))
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
            lines.append("| {} | {} |".format(status.capitalize(), count))
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

            # Check test coverage
            has_tests = "✅" if "references" in frontmatter and "tests" in frontmatter.get("references", {}) and frontmatter["references"]["tests"] else "❌"

            # Check standard reference
            has_standard = "✅"
            if "references" in frontmatter and "standards" in frontmatter["references"]:
                standards = frontmatter["references"]["standards"]
                found = False
                for std in standards:
                    if standard_name.lower() in std.lower():
                        found = True
                        break
                has_standard = "✅" if found else "❌"
            else:
                has_standard = "❌"

            lines.append("| {} | {} | {} | {} | {} | {} |".format(
                req_id,
                title,
                priority,
                status,
                has_tests,
                has_standard,
            ))
        lines.append("")

    # Compliance gaps
    lines.append("## Compliance Gaps")
    lines.append("")

    # Safety requirements without test coverage
    safety_without_tests = []
    for req_id, frontmatter in safety_reqs:
        has_tests = "references" in frontmatter and "tests" in frontmatter.get("references", {}) and frontmatter["references"]["tests"]
        if not has_tests:
            safety_without_tests.append((req_id, frontmatter.get("title", "")))

    if safety_without_tests:
        lines.append("### ⚠️ Safety Requirements without Test Coverage")
        lines.append("")
        for req_id, title in safety_without_tests:
            lines.append("- **{}**: {}".format(req_id, title))
        lines.append("")
    else:
        lines.append("### ✅ All Safety Requirements have Test Coverage")
        lines.append("")

    # Safety requirements without standard reference
    safety_without_standard = []
    for req_id, frontmatter in safety_reqs:
        has_standard = False
        if "references" in frontmatter and "standards" in frontmatter["references"]:
            standards = frontmatter["references"]["standards"]
            for std in standards:
                if standard_name.lower() in std.lower():
                    has_standard = True
                    break
        if not has_standard:
            safety_without_standard.append((req_id, frontmatter.get("title", "")))

    if safety_without_standard:
        lines.append("### ⚠️ Safety Requirements without {} Reference".format(standard_name))
        lines.append("")
        for req_id, title in safety_without_standard:
            lines.append("- **{}**: {}".format(req_id, title))
        lines.append("")
    else:
        lines.append("### ✅ All Safety Requirements reference {}".format(standard_name))
        lines.append("")

    # Requirements not yet verified
    unverified = []
    for req_id, frontmatter in requirements_data:
        status = frontmatter.get("status", "")
        if status not in ["verified", "deprecated"]:
            unverified.append((req_id, frontmatter.get("title", ""), status))

    if unverified:
        lines.append("### Requirements Not Yet Verified")
        lines.append("")
        lines.append("| Requirement | Title | Current Status |")
        lines.append("|-------------|-------|----------------|")
        for req_id, title, status in unverified:
            lines.append("| {} | {} | {} |".format(req_id, title, status))
        lines.append("")

    return "\n".join(lines)

# Export functions
traceability = struct(
    generate_matrix_markdown = _generate_traceability_matrix_markdown,
    generate_coverage_markdown = _generate_coverage_report_markdown,
    generate_change_impact_markdown = _generate_change_impact_report,
    generate_compliance_markdown = _generate_compliance_report,
)
