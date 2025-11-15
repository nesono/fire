"""Unit tests for requirement validator."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":requirement_validator.bzl", "requirement_validator")

def _test_valid_requirement(ctx):
    """Test valid requirement document."""
    env = unittest.begin(ctx)

    content = """# System Requirements

## REQ-001

```yaml
sil: ASIL-D
sec: false
version: 1
```

**Maximum Vehicle Velocity**

The vehicle SHALL NOT exceed 55.0 m/s under any operating conditions.

Based on ISO 26262 safety analysis for ASIL-D classification.
"""

    err = requirement_validator.validate(content)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_minimal_valid_requirement(ctx):
    """Test minimal valid requirement (only required fields)."""
    env = unittest.begin(ctx)

    content = """## REQ-MIN-001

```yaml
sil: QM
sec: false
version: 1
```

**Minimal Requirement**

This is a minimal requirement with only required fields.
"""

    err = requirement_validator.validate(content)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_missing_yaml_block(ctx):
    """Test requirement without YAML block."""
    env = unittest.begin(ctx)

    content = """## REQ-001

**Some Requirement**

This requirement has no YAML block.
"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing YAML block should fail")
    asserts.true(env, "requirement" in err.lower(), "Should mention requirement problem")

    return unittest.end(env)

def _test_missing_required_yaml_fields(ctx):
    """Test missing required fields in YAML block."""
    env = unittest.begin(ctx)

    # Missing sil
    content = """## REQ-001

```yaml
sec: false
version: 1
```

**Test Requirement**

Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing sil should fail")

    # Missing sec
    content = """## REQ-001

```yaml
sil: QM
version: 1
```

**Test Requirement**

Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing sec should fail")

    # Missing version
    content = """## REQ-001

```yaml
sil: QM
sec: false
```

**Test Requirement**

Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing version should fail")

    return unittest.end(env)

def _test_invalid_requirement_id(ctx):
    """Test invalid requirement ID formats."""
    env = unittest.begin(ctx)

    # ID starting with number
    content = """## 123REQ

```yaml
sil: QM
sec: false
version: 1
```

**Test Requirement**

Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "ID starting with number should fail")

    # ID with invalid characters
    content = """## REQ@001

```yaml
sil: QM
sec: false
version: 1
```

**Test Requirement**

Body content here.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "ID with invalid characters should fail")

    return unittest.end(env)

def _test_empty_body(ctx):
    """Test requirement with empty body."""
    env = unittest.begin(ctx)

    content = """## REQ-001

```yaml
sil: QM
sec: false
version: 1
```

"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Empty body should fail")
    asserts.true(env, "description" in err.lower() or "requirement" in err.lower(), "Should mention description or requirement issue")

    return unittest.end(env)

def _test_too_short_body(ctx):
    """Test requirement with too short body."""
    env = unittest.begin(ctx)

    content = """## REQ-001

```yaml
sil: QM
sec: false
version: 1
```

**T**

x
"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Too short body should fail")
    asserts.true(env, "too short" in err, "Should mention too short")

    return unittest.end(env)

def _test_missing_title(ctx):
    """Test requirement with missing title."""
    env = unittest.begin(ctx)

    content = """## REQ-001

```yaml
sil: QM
sec: false
version: 1
```

Body content here without a title.
"""

    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Missing title should fail")
    asserts.true(env, "title" in err.lower(), "Should mention title")

    return unittest.end(env)

def _test_parse_yaml_block(ctx):
    """Test parsing YAML block values."""
    env = unittest.begin(ctx)

    content = """## REQ-001

```yaml
sil: ASIL-D
sec: true
version: 2
```

**Test Requirement**

Body content here.
"""

    yaml_data, _ = requirement_validator.parse_yaml_block(content)
    asserts.true(env, yaml_data != None, "Should parse YAML block")
    asserts.equals(env, "ASIL-D", yaml_data["sil"])
    asserts.equals(env, True, yaml_data["sec"])
    asserts.equals(env, 2, yaml_data["version"])

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
        content = """## {}

```yaml
sil: QM
sec: false
version: 1
```

**Test Requirement**

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
        content = """## REQ-001

```yaml
sil: {}
sec: false
version: 1
```

**Test Requirement**

Body content here with sufficient length for validation.
""".format(sil)

        err = requirement_validator.validate(content)
        asserts.equals(env, None, err, "SIL '{}' should be valid".format(sil))

    return unittest.end(env)

def _test_invalid_sil_values(ctx):
    """Test invalid SIL values."""
    env = unittest.begin(ctx)

    # Invalid SIL value
    content = """## REQ-001

```yaml
sil: INVALID-X
sec: false
version: 1
```

**Test Requirement**

Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Invalid SIL should fail")
    asserts.true(env, "invalid" in err.lower() or "sil" in err.lower(), "Should mention SIL issue")

    return unittest.end(env)

def _test_valid_sec_values(ctx):
    """Test valid sec (security-related) values."""
    env = unittest.begin(ctx)

    # sec: true
    content = """## REQ-001

```yaml
sil: QM
sec: true
version: 1
```

**Test Requirement**

Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.equals(env, None, err, "sec: true should be valid")

    # sec: false
    content = """## REQ-002

```yaml
sil: QM
sec: false
version: 1
```

**Test Requirement**

Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.equals(env, None, err, "sec: false should be valid")

    return unittest.end(env)

def _test_invalid_sec_values(ctx):
    """Test invalid sec values."""
    env = unittest.begin(ctx)

    # Non-boolean value (string)
    content = """## REQ-001

```yaml
sil: QM
sec: "yes"
version: 1
```

**Test Requirement**

Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "String sec value should fail")
    asserts.true(env, "boolean" in err.lower() or "sec" in err.lower(), "Should mention boolean or sec")

    return unittest.end(env)

def _test_invalid_version_values(ctx):
    """Test invalid version values."""
    env = unittest.begin(ctx)

    # Negative version
    content = """## REQ-001

```yaml
sil: QM
sec: false
version: -1
```

**Test Requirement**

Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Negative version should fail")

    # Zero version
    content = """## REQ-002

```yaml
sil: QM
sec: false
version: 0
```

**Test Requirement**

Body content here with sufficient length for validation.
"""
    err = requirement_validator.validate(content)
    asserts.true(env, err != None, "Zero version should fail")

    return unittest.end(env)

def _test_valid_version_values(ctx):
    """Test valid version values."""
    env = unittest.begin(ctx)

    valid_versions = [1, 2, 10, 100]

    for ver in valid_versions:
        content = """## REQ-001

```yaml
sil: QM
sec: false
version: {}
```

**Test Requirement**

Body content here with sufficient length for validation.
""".format(ver)

        err = requirement_validator.validate(content)
        asserts.equals(env, None, err, "Version '{}' should be valid".format(ver))

    return unittest.end(env)

def _test_sil_and_sec_combined(ctx):
    """Test requirement with both high SIL and security flag."""
    env = unittest.begin(ctx)

    content = """## REQ-SEC-001

```yaml
sil: ASIL-D
sec: true
version: 1
```

**Security Critical Requirement**

This is a safety-critical requirement that also has security implications.
"""
    err = requirement_validator.validate(content)
    asserts.equals(env, None, err, "Requirement with both SIL and sec should be valid")

    return unittest.end(env)

# Test suite
valid_requirement_test = unittest.make(_test_valid_requirement)
minimal_valid_requirement_test = unittest.make(_test_minimal_valid_requirement)
missing_yaml_block_test = unittest.make(_test_missing_yaml_block)
missing_required_yaml_fields_test = unittest.make(_test_missing_required_yaml_fields)
invalid_requirement_id_test = unittest.make(_test_invalid_requirement_id)
empty_body_test = unittest.make(_test_empty_body)
too_short_body_test = unittest.make(_test_too_short_body)
missing_title_test = unittest.make(_test_missing_title)
parse_yaml_block_test = unittest.make(_test_parse_yaml_block)
valid_id_formats_test = unittest.make(_test_valid_id_formats)
valid_sil_values_test = unittest.make(_test_valid_sil_values)
invalid_sil_values_test = unittest.make(_test_invalid_sil_values)
valid_sec_values_test = unittest.make(_test_valid_sec_values)
invalid_sec_values_test = unittest.make(_test_invalid_sec_values)
invalid_version_values_test = unittest.make(_test_invalid_version_values)
valid_version_values_test = unittest.make(_test_valid_version_values)
sil_and_sec_combined_test = unittest.make(_test_sil_and_sec_combined)

def requirement_validator_test_suite(name):
    """Create test suite for requirement_validator."""
    unittest.suite(
        name,
        valid_requirement_test,
        minimal_valid_requirement_test,
        missing_yaml_block_test,
        missing_required_yaml_fields_test,
        invalid_requirement_id_test,
        empty_body_test,
        too_short_body_test,
        missing_title_test,
        parse_yaml_block_test,
        valid_id_formats_test,
        valid_sil_values_test,
        invalid_sil_values_test,
        valid_sec_values_test,
        invalid_sec_values_test,
        invalid_version_values_test,
        valid_version_values_test,
        sil_and_sec_combined_test,
    )
