"""Unit tests for reference validator."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":reference_validator.bzl", "reference_validator")

def _test_no_references(ctx):
    """Test requirement with no references."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "status": "draft",
        "title": "Test",
        "type": "functional",
    }

    err = reference_validator.validate(frontmatter)
    asserts.equals(env, None, err, "No references should be valid")

    return unittest.end(env)

def _test_valid_parameter_references(ctx):
    """Test valid parameter references."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "references": {
            "parameters": [
                "maximum_vehicle_velocity",
                "wheel_count",
                "braking_distance_table",
            ],
        },
        "status": "draft",
        "title": "Test",
        "type": "functional",
    }

    err = reference_validator.validate(frontmatter)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_invalid_parameter_reference(ctx):
    """Test invalid parameter reference format."""
    env = unittest.begin(ctx)

    # Parameter starting with number
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "parameters": ["123invalid"],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Parameter starting with number should fail")

    # Parameter with invalid characters
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "parameters": ["param-with-dash"],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Parameter with dash should fail")

    # Empty parameter reference
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "parameters": [""],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Empty parameter reference should fail")

    return unittest.end(env)

def _test_valid_requirement_references(ctx):
    """Test valid requirement references."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "references": {
            "requirements": [
                "REQ-002",
                "REQ-VEL-001",
                "REQ_BRAKE_001",
            ],
        },
    }

    err = reference_validator.validate(frontmatter)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_invalid_requirement_reference(ctx):
    """Test invalid requirement reference format."""
    env = unittest.begin(ctx)

    # Requirement starting with number
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "requirements": ["123REQ"],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Requirement starting with number should fail")

    # Empty requirement reference
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "requirements": [""],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Empty requirement reference should fail")

    return unittest.end(env)

def _test_valid_test_references(ctx):
    """Test valid test references (Bazel labels)."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "references": {
            "tests": [
                "//examples:vehicle_params_test",
                "//tests/unit:velocity_test",
                ":local_test",
            ],
        },
    }

    err = reference_validator.validate(frontmatter)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_invalid_test_reference(ctx):
    """Test invalid test reference format."""
    env = unittest.begin(ctx)

    # Test not starting with // or :
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "tests": ["examples:test"],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Test not starting with // or : should fail")

    # Test without :
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "tests": ["//examples"],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Test without target name should fail")

    # Empty test reference
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "tests": [""],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Empty test reference should fail")

    return unittest.end(env)

def _test_valid_standard_references(ctx):
    """Test valid standard references."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "references": {
            "standards": [
                "ISO 26262:2018, Part 3, Section 7",
                "UN ECE R13-H",
                "MISRA C:2012",
            ],
        },
    }

    err = reference_validator.validate(frontmatter)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_invalid_standard_reference(ctx):
    """Test invalid standard reference format."""
    env = unittest.begin(ctx)

    # Too short
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "standards": ["ab"],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Too short standard reference should fail")

    # Empty
    frontmatter = {
        "id": "REQ-001",
        "references": {
            "standards": [""],
        },
    }
    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Empty standard reference should fail")

    return unittest.end(env)

def _test_multiple_reference_types(ctx):
    """Test requirement with multiple reference types."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-VEL-001",
        "references": {
            "parameters": ["maximum_vehicle_velocity"],
            "requirements": ["REQ-BRK-001"],
            "standards": ["ISO 26262:2018"],
            "tests": ["//examples:vehicle_params_test"],
        },
    }

    err = reference_validator.validate(frontmatter)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_invalid_reference_type(ctx):
    """Test invalid reference type."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "references": {
            "invalid_type": ["something"],
        },
    }

    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Invalid reference type should fail")
    asserts.true(env, "invalid reference type" in err, "Should mention invalid reference type")

    return unittest.end(env)

def _test_references_not_list(ctx):
    """Test references that are not lists."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "references": {
            "parameters": "not_a_list",
        },
    }

    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Non-list references should fail")
    asserts.true(env, "must be a list" in err, "Should mention list requirement")

    return unittest.end(env)

def _test_references_not_dict(ctx):
    """Test references that are not a dictionary."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "references": ["not", "a", "dict"],
    }

    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Non-dict references should fail")
    asserts.true(env, "must be a dictionary" in err, "Should mention dictionary requirement")

    return unittest.end(env)

def _test_reference_not_string(ctx):
    """Test reference items that are not strings."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "references": {
            "parameters": [123],
        },
    }

    err = reference_validator.validate(frontmatter)
    asserts.true(env, err != None, "Non-string reference should fail")
    asserts.true(env, "must be a string" in err, "Should mention string requirement")

    return unittest.end(env)

def _test_empty_reference_lists(ctx):
    """Test empty reference lists (should be valid)."""
    env = unittest.begin(ctx)

    frontmatter = {
        "id": "REQ-001",
        "references": {
            "parameters": [],
            "requirements": [],
        },
    }

    err = reference_validator.validate(frontmatter)
    asserts.equals(env, None, err, "Empty reference lists should be valid")

    return unittest.end(env)

# Test suite
no_references_test = unittest.make(_test_no_references)
valid_parameter_references_test = unittest.make(_test_valid_parameter_references)
invalid_parameter_reference_test = unittest.make(_test_invalid_parameter_reference)
valid_requirement_references_test = unittest.make(_test_valid_requirement_references)
invalid_requirement_reference_test = unittest.make(_test_invalid_requirement_reference)
valid_test_references_test = unittest.make(_test_valid_test_references)
invalid_test_reference_test = unittest.make(_test_invalid_test_reference)
valid_standard_references_test = unittest.make(_test_valid_standard_references)
invalid_standard_reference_test = unittest.make(_test_invalid_standard_reference)
multiple_reference_types_test = unittest.make(_test_multiple_reference_types)
invalid_reference_type_test = unittest.make(_test_invalid_reference_type)
references_not_list_test = unittest.make(_test_references_not_list)
references_not_dict_test = unittest.make(_test_references_not_dict)
reference_not_string_test = unittest.make(_test_reference_not_string)
empty_reference_lists_test = unittest.make(_test_empty_reference_lists)

def reference_validator_test_suite(name):
    """Create test suite for reference_validator."""
    unittest.suite(
        name,
        no_references_test,
        valid_parameter_references_test,
        invalid_parameter_reference_test,
        valid_requirement_references_test,
        invalid_requirement_reference_test,
        valid_test_references_test,
        invalid_test_reference_test,
        valid_standard_references_test,
        invalid_standard_reference_test,
        multiple_reference_types_test,
        invalid_reference_type_test,
        references_not_list_test,
        references_not_dict_test,
        reference_not_string_test,
        empty_reference_lists_test,
    )
