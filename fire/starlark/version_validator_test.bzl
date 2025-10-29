"""Unit tests for version_validator.bzl (simple integer versioning)."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":version_validator.bzl", "version_validator")

def _test_validate_version_valid(ctx):
    env = unittest.begin(ctx)
    asserts.equals(env, None, version_validator.validate_version(1))
    asserts.equals(env, None, version_validator.validate_version(2))
    asserts.equals(env, None, version_validator.validate_version(100))
    return unittest.end(env)

def _test_validate_version_invalid(ctx):
    env = unittest.begin(ctx)
    asserts.true(env, version_validator.validate_version(0) != None)
    asserts.true(env, version_validator.validate_version(-1) != None)
    asserts.true(env, version_validator.validate_version("1") != None)
    return unittest.end(env)

def _test_simple_version_in_frontmatter(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-TEST-001",
        "version": 1,
    }
    asserts.equals(env, None, version_validator.validate(frontmatter))
    return unittest.end(env)

def _test_invalid_version_type(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-TEST-001",
        "version": "1.0.0",  # String not allowed
    }
    result = version_validator.validate(frontmatter)
    asserts.true(env, result != None)
    asserts.true(env, "must be an integer" in result)
    return unittest.end(env)

def _test_requirement_reference_string_format(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-TEST-001",
        "references": {
            "requirements": ["REQ-PARENT-001"],  # Old string format
        },
    }
    asserts.equals(env, None, version_validator.validate(frontmatter))
    return unittest.end(env)

def _test_requirement_reference_dict_format(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-TEST-001",
        "references": {
            "requirements": [
                {"id": "REQ-PARENT-001", "version": 2},  # New dict format with version
            ],
        },
    }
    asserts.equals(env, None, version_validator.validate(frontmatter))
    return unittest.end(env)

def _test_requirement_reference_mixed_formats(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-TEST-001",
        "references": {
            "requirements": [
                "REQ-PARENT-001",  # String format
                {"id": "REQ-PARENT-002", "version": 3},  # Dict format
            ],
        },
    }
    asserts.equals(env, None, version_validator.validate(frontmatter))
    return unittest.end(env)

def _test_requirement_reference_dict_without_version(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-TEST-001",
        "references": {
            "requirements": [
                {"id": "REQ-PARENT-001"},  # Dict without version is OK
            ],
        },
    }
    asserts.equals(env, None, version_validator.validate(frontmatter))
    return unittest.end(env)

def _test_requirement_reference_missing_id(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-TEST-001",
        "references": {
            "requirements": [
                {"version": 2},  # Missing 'id' field
            ],
        },
    }
    result = version_validator.validate(frontmatter)
    asserts.true(env, result != None)
    asserts.true(env, "must have 'id' field" in result)
    return unittest.end(env)

def _test_requirement_reference_invalid_version(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-TEST-001",
        "references": {
            "requirements": [
                {"id": "REQ-PARENT-001", "version": 0},  # Invalid version
            ],
        },
    }
    result = version_validator.validate(frontmatter)
    asserts.true(env, result != None)
    asserts.true(env, "positive integer" in result)
    return unittest.end(env)

def _test_complete_example(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-BRK-001",
        "references": {
            "parameters": ["maximum_vehicle_velocity"],
            "requirements": [
                {"id": "REQ-VEL-001", "version": 2},
                {"id": "REQ-TEMP-001", "version": 1},
            ],
        },
        "title": "Braking System",
        "version": 3,
    }
    asserts.equals(env, None, version_validator.validate(frontmatter))
    return unittest.end(env)

def _test_no_version_fields(ctx):
    env = unittest.begin(ctx)
    frontmatter = {
        "id": "REQ-TEST-001",
        "status": "draft",
        "title": "Test",
        "type": "functional",
    }
    asserts.equals(env, None, version_validator.validate(frontmatter))
    return unittest.end(env)

validate_version_valid_test = unittest.make(_test_validate_version_valid)
validate_version_invalid_test = unittest.make(_test_validate_version_invalid)
simple_version_in_frontmatter_test = unittest.make(_test_simple_version_in_frontmatter)
invalid_version_type_test = unittest.make(_test_invalid_version_type)
requirement_reference_string_format_test = unittest.make(_test_requirement_reference_string_format)
requirement_reference_dict_format_test = unittest.make(_test_requirement_reference_dict_format)
requirement_reference_mixed_formats_test = unittest.make(_test_requirement_reference_mixed_formats)
requirement_reference_dict_without_version_test = unittest.make(_test_requirement_reference_dict_without_version)
requirement_reference_missing_id_test = unittest.make(_test_requirement_reference_missing_id)
requirement_reference_invalid_version_test = unittest.make(_test_requirement_reference_invalid_version)
complete_example_test = unittest.make(_test_complete_example)
no_version_fields_test = unittest.make(_test_no_version_fields)

def version_validator_test_suite(name):
    """Create test suite for version_validator."""
    unittest.suite(
        name,
        validate_version_valid_test,
        validate_version_invalid_test,
        simple_version_in_frontmatter_test,
        invalid_version_type_test,
        requirement_reference_string_format_test,
        requirement_reference_dict_format_test,
        requirement_reference_mixed_formats_test,
        requirement_reference_dict_without_version_test,
        requirement_reference_missing_id_test,
        requirement_reference_invalid_version_test,
        complete_example_test,
        no_version_fields_test,
    )
