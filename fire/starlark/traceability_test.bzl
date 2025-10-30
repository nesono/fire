"""Unit tests for traceability.bzl (reporting and compliance)."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":traceability.bzl", "traceability")

def _test_traceability_matrix_with_versions(ctx):
    env = unittest.begin(ctx)

    # Test data with version tracking
    requirements_data = [
        ("REQ-VEL-001", {
            "references": {
                "parameters": ["max_velocity"],
                "requirements": ["REQ-BRK-001"],
            },
            "title": "Maximum Velocity",
            "version": 2,
        }),
        ("REQ-BRK-001", {
            "references": {
                "requirements": [
                    {"id": "REQ-VEL-001", "version": 2},
                ],
            },
            "title": "Braking Distance",
            "version": 1,
        }),
    ]

    result = traceability.generate_matrix_markdown(requirements_data)

    # Should include version column
    asserts.true(env, "| Requirement | Version |" in result)
    asserts.true(env, "| REQ-VEL-001 | 2 |" in result)
    asserts.true(env, "| REQ-BRK-001 | 1 |" in result)

    # Should show parent version tracking
    asserts.true(env, "REQ-VEL-001 (v2)" in result)

    return unittest.end(env)

def _test_traceability_matrix_without_versions(ctx):
    env = unittest.begin(ctx)

    # Test data without version tracking
    requirements_data = [
        ("REQ-TEST-001", {
            "references": {
                "parameters": ["test_param"],
            },
            "title": "Test Requirement",
        }),
    ]

    result = traceability.generate_matrix_markdown(requirements_data)

    # Should handle missing version gracefully
    asserts.true(env, "| REQ-TEST-001 | - |" in result)

    return unittest.end(env)

def _test_change_impact_no_stale_refs(ctx):
    env = unittest.begin(ctx)

    # Test data where versions match
    requirements_data = [
        ("REQ-PARENT-001", {
            "title": "Parent",
            "version": 2,
        }),
        ("REQ-CHILD-001", {
            "references": {
                "requirements": [
                    {"id": "REQ-PARENT-001", "version": 2},
                ],
            },
            "title": "Child",
            "version": 1,
        }),
    ]

    result = traceability.generate_change_impact_markdown(requirements_data)

    # Should show no stale requirements
    asserts.true(env, "All Requirements Up-to-Date" in result)
    asserts.true(env, "No requirements found with stale parent references" in result)

    return unittest.end(env)

def _test_change_impact_with_stale_refs(ctx):
    env = unittest.begin(ctx)

    # Test data where child tracks old parent version
    requirements_data = [
        ("REQ-PARENT-001", {
            "title": "Parent",
            "version": 3,  # Parent is now at v3
        }),
        ("REQ-CHILD-001", {
            "references": {
                "requirements": [
                    {"id": "REQ-PARENT-001", "version": 2},  # But child still tracks v2
                ],
            },
            "title": "Child",
            "version": 1,
        }),
    ]

    result = traceability.generate_change_impact_markdown(requirements_data)

    # Should identify stale requirement
    asserts.true(env, "Requirements with Stale Parent References" in result)
    asserts.true(env, "REQ-CHILD-001" in result)
    asserts.true(env, "Tracking v2, but current version is v3" in result)

    return unittest.end(env)

def _test_change_impact_multiple_stale_parents(ctx):
    env = unittest.begin(ctx)

    # Test data with multiple stale parent references
    requirements_data = [
        ("REQ-PARENT-001", {"title": "Parent 1", "version": 3}),
        ("REQ-PARENT-002", {"title": "Parent 2", "version": 5}),
        ("REQ-CHILD-001", {
            "references": {
                "requirements": [
                    {"id": "REQ-PARENT-001", "version": 2},
                    {"id": "REQ-PARENT-002", "version": 4},
                ],
            },
            "title": "Child",
            "version": 1,
        }),
    ]

    result = traceability.generate_change_impact_markdown(requirements_data)

    # Should identify both stale references
    asserts.true(env, "REQ-PARENT-001" in result)
    asserts.true(env, "v2" in result and "v3" in result)
    asserts.true(env, "REQ-PARENT-002" in result)
    asserts.true(env, "v4" in result and "v5" in result)

    return unittest.end(env)

def _test_change_impact_string_format_refs(ctx):
    env = unittest.begin(ctx)

    # Test data with string format (no version tracking)
    requirements_data = [
        ("REQ-PARENT-001", {"title": "Parent", "version": 2}),
        ("REQ-CHILD-001", {
            "references": {
                "requirements": ["REQ-PARENT-001"],  # String format, no version
            },
            "title": "Child",
        }),
    ]

    result = traceability.generate_change_impact_markdown(requirements_data)

    # Should not flag string-format refs as stale
    asserts.true(env, "All Requirements Up-to-Date" in result)

    return unittest.end(env)

def _test_compliance_report_iso26262(ctx):
    env = unittest.begin(ctx)

    # Test data with safety requirements
    requirements_data = [
        ("REQ-SAFETY-001", {
            "priority": "critical",
            "references": {
                "standards": ["ISO 26262:2018, Part 3"],
                "tests": ["//tests:emergency_stop_test"],
            },
            "status": "verified",
            "title": "Emergency Stop",
            "type": "safety",
        }),
        ("REQ-FUNC-001", {
            "status": "implemented",
            "title": "Feature X",
            "type": "functional",
        }),
    ]

    result = traceability.generate_compliance_markdown(requirements_data, "ISO 26262")

    # Should generate compliance report
    asserts.true(env, "Compliance Report: ISO 26262" in result)
    asserts.true(env, "Safety Requirements" in result)
    asserts.true(env, "REQ-SAFETY-001" in result)

    return unittest.end(env)

def _test_compliance_report_safety_gaps(ctx):
    env = unittest.begin(ctx)

    # Test data with safety requirements missing coverage
    requirements_data = [
        ("REQ-SAFETY-001", {
            "priority": "critical",
            "references": {
                "standards": ["ISO 26262:2018"],
            },
            "status": "approved",
            "title": "Safety without tests",
            "type": "safety",
        }),
        ("REQ-SAFETY-002", {
            "references": {
                "tests": ["//tests:test"],
            },
            "status": "approved",
            "title": "Safety without standard",
            "type": "safety",
        }),
    ]

    result = traceability.generate_compliance_markdown(requirements_data, "ISO 26262")

    # Should identify gaps
    asserts.true(env, "Safety Requirements without Test Coverage" in result)
    asserts.true(env, "REQ-SAFETY-001" in result)
    asserts.true(env, "Safety Requirements without ISO 26262 Reference" in result)
    asserts.true(env, "REQ-SAFETY-002" in result)

    return unittest.end(env)

def _test_compliance_report_status_distribution(ctx):
    env = unittest.begin(ctx)

    # Test data with various statuses
    requirements_data = [
        ("REQ-001", {"status": "draft", "title": "R1", "type": "functional"}),
        ("REQ-002", {"status": "approved", "title": "R2", "type": "functional"}),
        ("REQ-003", {"status": "verified", "title": "R3", "type": "functional"}),
        ("REQ-004", {"status": "approved", "title": "R4", "type": "functional"}),
    ]

    result = traceability.generate_compliance_markdown(requirements_data, "ISO 26262")

    # Should show status distribution
    asserts.true(env, "Requirements by Status" in result)
    asserts.true(env, "Draft | 1" in result)
    asserts.true(env, "Approved | 2" in result)
    asserts.true(env, "Verified | 1" in result)

    return unittest.end(env)

def _test_coverage_report_basic(ctx):
    env = unittest.begin(ctx)

    # Test data
    requirements_data = [
        ("REQ-001", {
            "references": {
                "parameters": ["param1"],
                "tests": ["//test:test1"],
            },
            "title": "Test 1",
        }),
        ("REQ-002", {
            "references": {},
            "title": "Test 2",
        }),
    ]

    result = traceability.generate_coverage_markdown(requirements_data)

    # Should generate coverage report
    asserts.true(env, "Traceability Coverage Report" in result)
    asserts.true(env, "Total Requirements | 2 | 100%" in result)
    asserts.true(env, "Requirements with Parameters | 1 | 50%" in result)
    asserts.true(env, "Requirements with Tests | 1 | 50%" in result)

    return unittest.end(env)

traceability_matrix_with_versions_test = unittest.make(_test_traceability_matrix_with_versions)
traceability_matrix_without_versions_test = unittest.make(_test_traceability_matrix_without_versions)
change_impact_no_stale_refs_test = unittest.make(_test_change_impact_no_stale_refs)
change_impact_with_stale_refs_test = unittest.make(_test_change_impact_with_stale_refs)
change_impact_multiple_stale_parents_test = unittest.make(_test_change_impact_multiple_stale_parents)
change_impact_string_format_refs_test = unittest.make(_test_change_impact_string_format_refs)
compliance_report_iso26262_test = unittest.make(_test_compliance_report_iso26262)
compliance_report_safety_gaps_test = unittest.make(_test_compliance_report_safety_gaps)
compliance_report_status_distribution_test = unittest.make(_test_compliance_report_status_distribution)
coverage_report_basic_test = unittest.make(_test_coverage_report_basic)

def traceability_test_suite(name):
    """Create test suite for traceability."""
    unittest.suite(
        name,
        traceability_matrix_with_versions_test,
        traceability_matrix_without_versions_test,
        change_impact_no_stale_refs_test,
        change_impact_with_stale_refs_test,
        change_impact_multiple_stale_parents_test,
        change_impact_string_format_refs_test,
        compliance_report_iso26262_test,
        compliance_report_safety_gaps_test,
        compliance_report_status_distribution_test,
        coverage_report_basic_test,
    )
