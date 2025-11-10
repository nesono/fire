"""Unit tests for software requirements parser and validator."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":swreq_parser.bzl", "swreq_parser")
load(":swreq_validator.bzl", "swreq_validator")

# ============================================================================
# Parser Tests
# ============================================================================

def _test_parse_valid_swreq(ctx):
    """Test parsing valid software requirements document."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
system_function: sys_eng/software_architecture/hzm.sysarch.md
---

# Software Requirements: Hazard Zone

## REQ_HZM_HZ

- **ID**: REQ_HZM_HZ
- **Parent**: sys_eng/sysreq/hzm.sysreq.md#ATS_867
- **SIL**: SIL-2
- **Sec**: true
- **Description**: The HZM hazard_zone component shall output a no-steering sector.

---

## REQ_HZM_NOT_HZ

- **ID**: REQ_HZM_NOT_HZ
- **Parent**: sys_eng/sysreq/hzm.sysreq.md#ATS_871
- **SIL**: SIL-2
- **Sec**: true
- **Description**: The HZM hazard_zone component shall output a not-hazard-zone as a list of polygons.

---
"""

    frontmatter, requirements = swreq_parser.parse(content)

    # Check frontmatter (only system_function is relevant now)
    asserts.equals(env, "sys_eng/software_architecture/hzm.sysarch.md", frontmatter["system_function"])

    # Check requirements
    asserts.equals(env, 2, len(requirements))

    # Check first requirement
    req1 = requirements[0]
    asserts.equals(env, "REQ_HZM_HZ", req1["id"])
    asserts.equals(env, "sys_eng/sysreq/hzm.sysreq.md#ATS_867", req1["parent"])
    asserts.equals(env, "SIL-2", req1["sil"])
    asserts.equals(env, True, req1["sec"])
    asserts.true(env, "no-steering sector" in req1["description"])

    # Check second requirement
    req2 = requirements[1]
    asserts.equals(env, "REQ_HZM_NOT_HZ", req2["id"])
    asserts.equals(env, "sys_eng/sysreq/hzm.sysreq.md#ATS_871", req2["parent"])

    return unittest.end(env)

def _test_parse_multiline_description(ctx):
    """Test parsing requirement with multi-line description."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
- **Description**: This is a very long description that spans
  multiple lines and should be properly concatenated into a single
  description field by the parser.

---
"""

    _, requirements = swreq_parser.parse(content)

    asserts.equals(env, 1, len(requirements))
    req = requirements[0]
    asserts.true(env, "multiple lines" in req["description"])
    asserts.true(env, "concatenated" in req["description"])

    return unittest.end(env)

def _test_parse_sil_none(ctx):
    """Test parsing requirement with SIL: None."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: None
- **Sec**: false
- **Description**: This requirement has no SIL level assigned.

---
"""

    _, requirements = swreq_parser.parse(content)

    asserts.equals(env, 1, len(requirements))
    req = requirements[0]
    asserts.equals(env, None, req["sil"])
    asserts.equals(env, False, req["sec"])

    return unittest.end(env)

# ============================================================================
# Validator Tests - Valid Cases
# ============================================================================

def _test_validate_valid_swreq(ctx):
    """Test validation of valid software requirements document."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_HZM_HZ

- **ID**: REQ_HZM_HZ
- **Parent**: sys_eng/sysreq/hzm.md#ATS_867
- **SIL**: SIL-2
- **Sec**: true
- **Description**: The component shall output a hazard zone sector.

---
"""

    err = swreq_validator.validate(content)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_validate_multiple_requirements(ctx):
    """Test validation with multiple requirements."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: ASIL-D
- **Sec**: true
- **Description**: First requirement description with sufficient length.

---

## REQ_TEST_002

- **ID**: REQ_TEST_002
- **Parent**: sysreq.md#SYS_002
- **SIL**: ASIL-C
- **Sec**: false
- **Description**: Second requirement description with sufficient length.

---

## REQ_TEST_003

- **ID**: REQ_TEST_003
- **Parent**: sysreq.md#SYS_003
- **SIL**: ASIL-D
- **Sec**: true
- **Description**: Third requirement description with sufficient length.

---
"""

    err = swreq_validator.validate(content)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_validate_internal_references(ctx):
    """Test validation with internal requirement references."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_PRIMARY

- **ID**: REQ_TEST_PRIMARY
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
- **Description**: This requirement references REQ_TEST_SECONDARY in its description.

---

## REQ_TEST_SECONDARY

- **ID**: REQ_TEST_SECONDARY
- **Parent**: sysreq.md#SYS_002
- **SIL**: SIL-2
- **Sec**: false
- **Description**: This is the secondary requirement being referenced.

---
"""

    err = swreq_validator.validate(content)
    asserts.equals(env, None, err)

    return unittest.end(env)

# ============================================================================
# Validator Tests - Invalid Cases
# ============================================================================

def _test_validate_missing_frontmatter(ctx):
    """Test validation succeeds without frontmatter (frontmatter now optional)."""
    env = unittest.begin(ctx)

    content = """# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
- **Description**: This requirement has no frontmatter.
"""

    err = swreq_validator.validate(content)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_validate_missing_required_frontmatter_field(ctx):
    """Test validation succeeds with empty frontmatter (frontmatter now optional)."""
    env = unittest.begin(ctx)

    # Empty frontmatter is now valid - component, version, sil, security_related are redundant
    content = """---
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
- **Description**: Valid requirement description.
"""

    err = swreq_validator.validate(content)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_validate_invalid_requirement_id_format(ctx):
    """Test validation fails with invalid requirement ID format."""
    env = unittest.begin(ctx)

    # Lowercase in ID (doesn't start with REQ_)
    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## req_test_001

- **ID**: req_test_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
- **Description**: This has invalid ID format (lowercase).
"""

    err = swreq_validator.validate(content)
    asserts.true(env, err != None)
    asserts.true(env, "REQ_" in err)

    return unittest.end(env)

def _test_validate_missing_req_prefix(ctx):
    """Test validation fails when ID doesn't start with REQ_."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## TEST_001

- **ID**: TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
- **Description**: This ID doesn't start with REQ_.
"""

    err = swreq_validator.validate(content)
    asserts.true(env, err != None)
    asserts.true(env, "REQ_" in err)

    return unittest.end(env)

def _test_validate_invalid_parent_reference(ctx):
    """Test validation fails with invalid parent reference format."""
    env = unittest.begin(ctx)

    # Missing anchor
    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md
- **SIL**: SIL-2
- **Sec**: true
- **Description**: Parent reference missing anchor.
"""

    err = swreq_validator.validate(content)
    asserts.true(env, err != None)
    asserts.true(env, "anchor" in err)

    return unittest.end(env)

def _test_validate_duplicate_requirement_ids(ctx):
    """Test validation fails with duplicate requirement IDs."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
- **Description**: First requirement with this ID.

---

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_002
- **SIL**: SIL-2
- **Sec**: true
- **Description**: Duplicate requirement with same ID.
"""

    err = swreq_validator.validate(content)
    asserts.true(env, err != None)
    asserts.true(env, "duplicate" in err)

    return unittest.end(env)

def _test_validate_missing_requirement_field(ctx):
    """Test validation fails with missing required field in requirement."""
    env = unittest.begin(ctx)

    # Missing Description field
    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
"""

    err = swreq_validator.validate(content)
    asserts.true(env, err != None)
    asserts.true(env, "description" in err.lower())

    return unittest.end(env)

def _test_validate_short_description(ctx):
    """Test validation fails with too short description."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
- **Description**: Short.
"""

    err = swreq_validator.validate(content)
    asserts.true(env, err != None)
    asserts.true(env, "too short" in err)

    return unittest.end(env)

def _test_validate_invalid_internal_reference(ctx):
    """Test validation fails when description references non-existent requirement."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: true
- **Description**: This requirement references REQ_NONEXISTENT which does not exist.
"""

    err = swreq_validator.validate(content)
    asserts.true(env, err != None)
    asserts.true(env, "REQ_NONEXISTENT" in err)
    asserts.true(env, "unknown requirement" in err)

    return unittest.end(env)

def _test_validate_empty_document(ctx):
    """Test validation fails with no requirements."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

No requirements defined.
"""

    err = swreq_validator.validate(content)
    asserts.true(env, err != None)
    asserts.true(env, "at least one requirement" in err)

    return unittest.end(env)

def _test_validate_invalid_sec_type(ctx):
    """Test validation fails when Sec is not boolean."""
    env = unittest.begin(ctx)

    content = """---
# component field removed - redundant
# version field removed - redundant
# sil field removed - redundant
# security_related field removed - redundant
---

# Software Requirements

## REQ_TEST_001

- **ID**: REQ_TEST_001
- **Parent**: sysreq.md#SYS_001
- **SIL**: SIL-2
- **Sec**: yes
- **Description**: Sec field should be boolean not string.
"""

    err = swreq_validator.validate(content)
    asserts.true(env, err != None)
    asserts.true(env, "boolean" in err.lower())

    return unittest.end(env)

# ============================================================================
# Validator Tests - ID Format
# ============================================================================

def _test_validate_id_format_valid(ctx):
    """Test valid software requirement ID formats."""
    env = unittest.begin(ctx)

    valid_ids = [
        "REQ_HZM_HZ",
        "REQ_TEST_001",
        "REQ_COMPONENT_FEATURE_001",
        "REQ_A_B_C_D",
        "REQ_123_456",
    ]

    for req_id in valid_ids:
        err = swreq_validator.validate_requirement_id(req_id)
        asserts.equals(env, None, err, "ID '{}' should be valid".format(req_id))

    return unittest.end(env)

def _test_validate_id_format_invalid(ctx):
    """Test invalid software requirement ID formats."""
    env = unittest.begin(ctx)

    invalid_ids = [
        "req_hzm_hz",  # Lowercase
        "REQ-HZM-HZ",  # Hyphens instead of underscores
        "REQUIREMENT_HZM_HZ",  # Doesn't start with REQ_
        "REQ_hzm_hz",  # Contains lowercase
        "REQ_",  # Too short
        "",  # Empty
    ]

    for req_id in invalid_ids:
        err = swreq_validator.validate_requirement_id(req_id)
        asserts.true(env, err != None, "ID '{}' should be invalid".format(req_id))

    return unittest.end(env)

# ============================================================================
# Validator Tests - Parent Reference Format
# ============================================================================

def _test_validate_parent_reference_valid(ctx):
    """Test valid parent reference formats."""
    env = unittest.begin(ctx)

    valid_refs = [
        "sys_eng/sysreq/hzm.md#ATS_867",
        "path/to/requirement.md#REQ_001",
        "sysreq.md#ANCHOR",
    ]

    for ref in valid_refs:
        err = swreq_validator.validate_parent_reference(ref)
        asserts.equals(env, None, err, "Reference '{}' should be valid".format(ref))

    return unittest.end(env)

def _test_validate_parent_reference_invalid(ctx):
    """Test invalid parent reference formats."""
    env = unittest.begin(ctx)

    invalid_refs = [
        "sysreq.md",  # Missing anchor
        "#ANCHOR",  # Missing file path
        "sysreq.md#",  # Empty anchor
        "sysreq.txt#ANCHOR",  # Not .md file
        "",  # Empty
    ]

    for ref in invalid_refs:
        err = swreq_validator.validate_parent_reference(ref)
        asserts.true(env, err != None, "Reference '{}' should be invalid".format(ref))

    return unittest.end(env)

# ============================================================================
# Test Suite
# ============================================================================

parse_valid_swreq_test = unittest.make(_test_parse_valid_swreq)
parse_multiline_description_test = unittest.make(_test_parse_multiline_description)
parse_sil_none_test = unittest.make(_test_parse_sil_none)

validate_valid_swreq_test = unittest.make(_test_validate_valid_swreq)
validate_multiple_requirements_test = unittest.make(_test_validate_multiple_requirements)
validate_internal_references_test = unittest.make(_test_validate_internal_references)

validate_missing_frontmatter_test = unittest.make(_test_validate_missing_frontmatter)
validate_missing_required_frontmatter_field_test = unittest.make(_test_validate_missing_required_frontmatter_field)
validate_invalid_requirement_id_format_test = unittest.make(_test_validate_invalid_requirement_id_format)
validate_missing_req_prefix_test = unittest.make(_test_validate_missing_req_prefix)
validate_invalid_parent_reference_test = unittest.make(_test_validate_invalid_parent_reference)
validate_duplicate_requirement_ids_test = unittest.make(_test_validate_duplicate_requirement_ids)
validate_missing_requirement_field_test = unittest.make(_test_validate_missing_requirement_field)
validate_short_description_test = unittest.make(_test_validate_short_description)
validate_invalid_internal_reference_test = unittest.make(_test_validate_invalid_internal_reference)
validate_empty_document_test = unittest.make(_test_validate_empty_document)
validate_invalid_sec_type_test = unittest.make(_test_validate_invalid_sec_type)

validate_id_format_valid_test = unittest.make(_test_validate_id_format_valid)
validate_id_format_invalid_test = unittest.make(_test_validate_id_format_invalid)
validate_parent_reference_valid_test = unittest.make(_test_validate_parent_reference_valid)
validate_parent_reference_invalid_test = unittest.make(_test_validate_parent_reference_invalid)

def swreq_validator_test_suite(name):
    """Create test suite for swreq validator."""
    unittest.suite(
        name,
        # Parser tests
        parse_valid_swreq_test,
        parse_multiline_description_test,
        parse_sil_none_test,
        # Validator tests - valid cases
        validate_valid_swreq_test,
        validate_multiple_requirements_test,
        validate_internal_references_test,
        # Validator tests - invalid cases
        validate_missing_frontmatter_test,
        validate_missing_required_frontmatter_field_test,
        validate_invalid_requirement_id_format_test,
        validate_missing_req_prefix_test,
        validate_invalid_parent_reference_test,
        validate_duplicate_requirement_ids_test,
        validate_missing_requirement_field_test,
        validate_short_description_test,
        validate_invalid_internal_reference_test,
        validate_empty_document_test,
        validate_invalid_sec_type_test,
        # Format tests
        validate_id_format_valid_test,
        validate_id_format_invalid_test,
        validate_parent_reference_valid_test,
        validate_parent_reference_invalid_test,
    )
