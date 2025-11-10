"""Unit tests for requirement validator."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":requirement_validator.bzl", "requirement_validator")

def _test_valid_requirement(ctx):
    """Test valid requirement document."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-001
title: Maximum Vehicle Velocity
type: functional
status: approved
priority: high
owner: safety-team
tags: [velocity, safety]
---

# REQ-001: Maximum Vehicle Velocity

## Description
The vehicle SHALL NOT exceed 55.0 m/s under any operating conditions.

## Rationale
Based on ISO 26262 safety analysis for ASIL-D classification.
"""

    err = requirement_validator.validate(content)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_minimal_valid_requirement(ctx):
    """Test minimal valid requirement (only required fields)."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-MIN-001
title: Minimal Requirement
type: functional
status: draft
---

This is a minimal requirement with only required fields.
"""

    err = requirement_validator.validate(content)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_missing_frontmatter(ctx):
    """Test requirement without frontmatter."""
    env = unittest.begin(ctx)

    content = """# Some Requirement

This requirement has no frontmatter.
"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing frontmatter should fail")
    asserts.true(env, "must have frontmatter" in err, "Should mention frontmatter")

    return unittest.end(env)

def _test_missing_required_fields(ctx):
    """Test missing required fields in frontmatter."""
    env = unittest.begin(ctx)

    # Missing id
    content = """---
title: Test
type: functional
status: draft
---
Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing id should fail")

    # Missing title
    content = """---
id: REQ-001
type: functional
status: draft
---
Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing title should fail")

    # Missing type
    content = """---
id: REQ-001
title: Test
status: draft
---
Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing type should fail")

    # Missing status
    content = """---
id: REQ-001
title: Test
type: functional
---
Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing status should fail")

    return unittest.end(env)

def _test_invalid_requirement_id(ctx):
    """Test invalid requirement ID formats."""
    env = unittest.begin(ctx)

    # Empty ID
    content = """---
id:
title: Test
type: functional
status: draft
---
Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Empty ID should fail")

    # ID starting with number
    content = """---
id: 123REQ
title: Test
type: functional
status: draft
---
Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "ID starting with number should fail")

    # ID with invalid characters
    content = """---
id: REQ@001
title: Test
type: functional
status: draft
---
Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "ID with invalid characters should fail")

    return unittest.end(env)

def _test_invalid_requirement_type(ctx):
    """Test invalid requirement type."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-001
title: Test
type: invalid-type
status: draft
---
Body content here.
"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Invalid type should fail")
    asserts.true(env, "invalid requirement type" in err, "Should mention invalid type")

    return unittest.end(env)

def _test_valid_requirement_types(ctx):
    """Test all valid requirement types."""
    env = unittest.begin(ctx)

    types = [
        "functional",
        "non-functional",
        "safety",
        "interface",
        "constraint",
        "performance",
    ]

    for req_type in types:
        content = """---
id: REQ-001
title: Test
type: {}
status: draft
---
Body content here.
""".format(req_type)

        err = requirement_validator.validate(content)
        asserts.equals(env, None, err, "Type '{}' should be valid".format(req_type))

    return unittest.end(env)

def _test_invalid_requirement_status(ctx):
    """Test invalid requirement status."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-001
title: Test
type: functional
status: invalid-status
---
Body content here.
"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Invalid status should fail")
    asserts.true(env, "invalid requirement status" in err, "Should mention invalid status")

    return unittest.end(env)

def _test_valid_requirement_statuses(ctx):
    """Test all valid requirement statuses."""
    env = unittest.begin(ctx)

    statuses = [
        "draft",
        "proposed",
        "approved",
        "implemented",
        "verified",
        "deprecated",
    ]

    for status in statuses:
        content = """---
id: REQ-001
title: Test
type: functional
status: {}
---
Body content here.
""".format(status)

        err = requirement_validator.validate(content)
        asserts.equals(env, None, err, "Status '{}' should be valid".format(status))

    return unittest.end(env)

def _test_invalid_priority(ctx):
    """Test invalid priority value."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-001
title: Test
type: functional
status: draft
priority: super-urgent
---
Body content here.
"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Invalid priority should fail")
    asserts.true(env, "invalid requirement priority" in err, "Should mention invalid priority")

    return unittest.end(env)

def _test_valid_priorities(ctx):
    """Test all valid priority values."""
    env = unittest.begin(ctx)

    priorities = ["low", "medium", "high", "critical"]

    for priority in priorities:
        content = """---
id: REQ-001
title: Test
type: functional
status: draft
priority: {}
---
Body content here.
""".format(priority)

        err = requirement_validator.validate(content)
        asserts.equals(env, None, err, "Priority '{}' should be valid".format(priority))

    return unittest.end(env)

def _test_empty_body(ctx):
    """Test requirement with empty body."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-001
title: Test
type: functional
status: draft
---

"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Empty body should fail")
    asserts.true(env, "empty body" in err, "Should mention empty body")

    return unittest.end(env)

def _test_too_short_body(ctx):
    """Test requirement with too short body."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-001
title: Test
type: functional
status: draft
---
Short
"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Too short body should fail")
    asserts.true(env, "too short" in err, "Should mention too short")

    return unittest.end(env)

def _test_empty_title(ctx):
    """Test requirement with empty title."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-001
title:
type: functional
status: draft
---
Body content here.
"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Empty title should fail")
    asserts.true(env, "title cannot be empty" in err, "Should mention empty title")

    return unittest.end(env)

def _test_parse_frontmatter_with_lists(ctx):
    """Test parsing frontmatter with list values."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-001
title: Test
type: functional
status: draft
tags: [safety, performance, critical]
---
Body content here.
"""

    frontmatter, _ = requirement_validator.parse_frontmatter(content)
    asserts.true(env, frontmatter != None, "Should parse frontmatter")
    asserts.equals(env, "REQ-001", frontmatter["id"])
    asserts.true(env, "tags" in frontmatter, "Should have tags field")
    asserts.equals(env, ["safety", "performance", "critical"], frontmatter["tags"])

    return unittest.end(env)

def _test_valid_id_formats(ctx):
    """Test various valid ID formats."""
    env = unittest.begin(ctx)

    valid_ids = [
        "REQ-001",
        "REQ_001",
        "Req-001",
        "_REQ-001",
        "SAFETY-REQ-001",
        "req_functional_001",
    ]

    for req_id in valid_ids:
        content = """---
id: {}
title: Test
type: functional
status: draft
---
Body content here with sufficient length for validation.
""".format(req_id)

        err = requirement_validator.validate(content)
        asserts.equals(env, None, err, "ID '{}' should be valid".format(req_id))

    return unittest.end(env)

def _test_valid_sil_values(ctx):
    """Test valid SIL (Safety Integrity Level) values."""
    env = unittest.begin(ctx)

    valid_sils = [
        "ASIL-A",
        "ASIL-B",
        "ASIL-C",
        "ASIL-D",
        "SIL-1",
        "SIL-2",
        "SIL-3",
        "SIL-4",
        "DAL-A",
        "DAL-B",
        "DAL-C",
        "DAL-D",
        "DAL-E",
        "QM",
    ]

    for sil in valid_sils:
        content = """---
id: REQ-001
title: Test
type: safety
status: approved
sil: {}
---
Body content here with sufficient length for validation.
""".format(sil)

        err = requirement_validator.validate(content)
        asserts.equals(env, None, err, "SIL '{}' should be valid".format(sil))

    return unittest.end(env)

def _test_invalid_sil_values(ctx):
    """Test invalid SIL values."""
    env = unittest.begin(ctx)

    # Whitespace-only SIL
    content = """---
id: REQ-001
title: Test
type: safety
status: approved
sil: "   "
---
Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Whitespace-only SIL should fail")
    asserts.true(env, "SIL cannot be whitespace only" in err, "Should mention whitespace")

    return unittest.end(env)

def _test_valid_security_related(ctx):
    """Test valid security_related values."""
    env = unittest.begin(ctx)

    # security_related: true
    content = """---
id: REQ-001
title: Test
type: functional
status: approved
security_related: true
---
Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.equals(env, None, err, "security_related: true should be valid")

    # security_related: false
    content = """---
id: REQ-002
title: Test
type: functional
status: approved
security_related: false
---
Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.equals(env, None, err, "security_related: false should be valid")

    return unittest.end(env)

def _test_invalid_security_related(ctx):
    """Test invalid security_related values."""
    env = unittest.begin(ctx)

    # Non-boolean value (string)
    content = """---
id: REQ-001
title: Test
type: functional
status: approved
security_related: "yes"
---
Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "String security_related should fail")
    asserts.true(env, "must be a boolean" in err, "Should mention boolean requirement")

    return unittest.end(env)

def _test_sil_and_security_combined(ctx):
    """Test requirement with both SIL and security_related."""
    env = unittest.begin(ctx)

    content = """---
id: REQ-SEC-001
title: Security Critical Requirement
type: safety
status: approved
sil: ASIL-D
security_related: true
priority: critical
---
This is a safety-critical requirement that also has security implications.
"""
    err = requirement_validator.validate(content)
    asserts.equals(env, None, err, "Requirement with both SIL and security_related should be valid")

    return unittest.end(env)

# Test suite
valid_requirement_test = unittest.make(_test_valid_requirement)
minimal_valid_requirement_test = unittest.make(_test_minimal_valid_requirement)
missing_frontmatter_test = unittest.make(_test_missing_frontmatter)
missing_required_fields_test = unittest.make(_test_missing_required_fields)
invalid_requirement_id_test = unittest.make(_test_invalid_requirement_id)
invalid_requirement_type_test = unittest.make(_test_invalid_requirement_type)
valid_requirement_types_test = unittest.make(_test_valid_requirement_types)
invalid_requirement_status_test = unittest.make(_test_invalid_requirement_status)
valid_requirement_statuses_test = unittest.make(_test_valid_requirement_statuses)
invalid_priority_test = unittest.make(_test_invalid_priority)
valid_priorities_test = unittest.make(_test_valid_priorities)
empty_body_test = unittest.make(_test_empty_body)
too_short_body_test = unittest.make(_test_too_short_body)
empty_title_test = unittest.make(_test_empty_title)
parse_frontmatter_with_lists_test = unittest.make(_test_parse_frontmatter_with_lists)
valid_id_formats_test = unittest.make(_test_valid_id_formats)
valid_sil_values_test = unittest.make(_test_valid_sil_values)
invalid_sil_values_test = unittest.make(_test_invalid_sil_values)
valid_security_related_test = unittest.make(_test_valid_security_related)
invalid_security_related_test = unittest.make(_test_invalid_security_related)
sil_and_security_combined_test = unittest.make(_test_sil_and_security_combined)

def requirement_validator_test_suite(name):
    """Create test suite for requirement_validator."""
    unittest.suite(
        name,
        valid_requirement_test,
        minimal_valid_requirement_test,
        missing_frontmatter_test,
        missing_required_fields_test,
        invalid_requirement_id_test,
        invalid_requirement_type_test,
        valid_requirement_types_test,
        invalid_requirement_status_test,
        valid_requirement_statuses_test,
        invalid_priority_test,
        valid_priorities_test,
        empty_body_test,
        too_short_body_test,
        empty_title_test,
        parse_frontmatter_with_lists_test,
        valid_id_formats_test,
        valid_sil_values_test,
        invalid_sil_values_test,
        valid_security_related_test,
        invalid_security_related_test,
        sil_and_security_combined_test,
    )
