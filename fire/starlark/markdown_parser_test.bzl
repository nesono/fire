"""Unit tests for markdown parser."""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load(":markdown_parser.bzl", "markdown_parser")

def _test_parse_requirement_references(ctx):
    """Test parsing requirement references."""
    env = unittest.begin(ctx)

    body = """
## Description
This requirement relates to [REQ-BRK-001](REQ-BRK-001.md) and
also references [REQ-VEL-001](REQ-VEL-001.md).
"""

    refs = markdown_parser.parse_references(body)
    asserts.equals(env, [("REQ-BRK-001", "REQ-BRK-001.md"), ("REQ-VEL-001", "REQ-VEL-001.md")], refs["requirements"])
    asserts.equals(env, [], refs["parameters"])
    asserts.equals(env, [], refs["tests"])

    return unittest.end(env)

def _test_parse_parameter_references(ctx):
    """Test parsing parameter references."""
    env = unittest.begin(ctx)

    body = """
## Description
Uses parameter [@maximum_vehicle_velocity](../vehicle_params.bzl#maximum_vehicle_velocity)
and [@wheel_count](../vehicle_params.bzl#wheel_count).
"""

    refs = markdown_parser.parse_references(body)
    asserts.equals(env, [("maximum_vehicle_velocity", "../vehicle_params.bzl#maximum_vehicle_velocity"), ("wheel_count", "../vehicle_params.bzl#wheel_count")], refs["parameters"])
    asserts.equals(env, [], refs["requirements"])
    asserts.equals(env, [], refs["tests"])

    return unittest.end(env)

def _test_parse_test_references(ctx):
    """Test parsing test references."""
    env = unittest.begin(ctx)

    body = """
## Verification
Verified by [vehicle_params_test](//examples:vehicle_params_test).
"""

    refs = markdown_parser.parse_references(body)
    asserts.equals(env, [("vehicle_params_test", "//examples:vehicle_params_test")], refs["tests"])
    asserts.equals(env, [], refs["parameters"])
    asserts.equals(env, [], refs["requirements"])

    return unittest.end(env)

def _test_parse_mixed_references(ctx):
    """Test parsing mixed reference types."""
    env = unittest.begin(ctx)

    body = """
## Description
This requirement uses [@max_velocity](../params.bzl#max_velocity)
and relates to [REQ-001](REQ-001.md).

## Verification
Tested by [my_test](//examples:my_test).

## External
See [ISO 26262](https://example.com/iso26262) for details.
"""

    refs = markdown_parser.parse_references(body)
    asserts.equals(env, [("max_velocity", "../params.bzl#max_velocity")], refs["parameters"])
    asserts.equals(env, [("REQ-001", "REQ-001.md")], refs["requirements"])
    asserts.equals(env, [("my_test", "//examples:my_test")], refs["tests"])
    asserts.true(env, len(refs["external"]) == 1)

    return unittest.end(env)

def _test_parse_no_references(ctx):
    """Test parsing body with no references."""
    env = unittest.begin(ctx)

    body = """
## Description
This is a plain requirement with no links.
Just regular text.
"""

    refs = markdown_parser.parse_references(body)
    asserts.equals(env, [], refs["parameters"])
    asserts.equals(env, [], refs["requirements"])
    asserts.equals(env, [], refs["tests"])
    asserts.equals(env, [], refs["external"])

    return unittest.end(env)

def _test_parse_empty_body(ctx):
    """Test parsing empty body."""
    env = unittest.begin(ctx)

    refs = markdown_parser.parse_references("")
    asserts.equals(env, [], refs["parameters"])
    asserts.equals(env, [], refs["requirements"])
    asserts.equals(env, [], refs["tests"])

    return unittest.end(env)

def _test_validate_matching_references(ctx):
    """Test validation when markdown refs match frontmatter."""
    env = unittest.begin(ctx)

    body = """
Uses [@max_velocity](../params.bzl#max_velocity) and relates to [REQ-001](REQ-001.md).
Tested by [my_test](//examples:my_test).
"""

    frontmatter_refs = {
        "parameters": ["../params.bzl#max_velocity"],
        "requirements": [{"path": "REQ-001.md", "version": 1}],
        "tests": ["//examples:my_test"],
    }

    err = markdown_parser.validate_references(body, frontmatter_refs)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_validate_missing_parameter_in_frontmatter(ctx):
    """Test validation when parameter is in body but not frontmatter."""
    env = unittest.begin(ctx)

    body = "Uses [@max_velocity](../params.bzl#max_velocity)."

    frontmatter_refs = {
        "parameters": [],  # Empty!
    }

    err = markdown_parser.validate_references(body, frontmatter_refs)
    asserts.true(env, err != None)
    asserts.true(env, "../params.bzl#max_velocity" in err)
    asserts.true(env, "not declared in frontmatter" in err)

    return unittest.end(env)

def _test_validate_missing_requirement_in_frontmatter(ctx):
    """Test validation when requirement is in body but not frontmatter."""
    env = unittest.begin(ctx)

    body = "Relates to [REQ-001](REQ-001.md)."

    frontmatter_refs = {
        "requirements": [{"path": "REQ-002.md", "version": 1}],  # Different requirement
    }

    err = markdown_parser.validate_references(body, frontmatter_refs)
    asserts.true(env, err != None)
    asserts.true(env, "REQ-001.md" in err)
    asserts.true(env, "not declared in frontmatter" in err)

    return unittest.end(env)

def _test_validate_missing_test_in_frontmatter(ctx):
    """Test validation when test is in body but not frontmatter."""
    env = unittest.begin(ctx)

    body = "Tested by [my_test](//examples:my_test)."

    frontmatter_refs = {
        "tests": [],  # Empty!
    }

    err = markdown_parser.validate_references(body, frontmatter_refs)
    asserts.true(env, err != None)
    asserts.true(env, "//examples:my_test" in err)
    asserts.true(env, "not declared in frontmatter" in err)

    return unittest.end(env)

def _test_validate_no_frontmatter_with_body_refs(ctx):
    """Test validation when body has refs but no frontmatter."""
    env = unittest.begin(ctx)

    body = "Uses [@param](file.bzl)."

    err = markdown_parser.validate_references(body, None)
    asserts.true(env, err != None)
    asserts.true(env, "no references section" in err)

    return unittest.end(env)

def _test_validate_no_body_refs(ctx):
    """Test validation when body has no refs (should pass if frontmatter also empty)."""
    env = unittest.begin(ctx)

    body = "Plain text with no links."

    frontmatter_refs = {
        "parameters": [],
    }

    err = markdown_parser.validate_references(body, frontmatter_refs)
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_validate_empty_body(ctx):
    """Test validation with empty body."""
    env = unittest.begin(ctx)

    err = markdown_parser.validate_references("", {"parameters": []})
    asserts.equals(env, None, err)

    return unittest.end(env)

def _test_parse_requirement_with_path(ctx):
    """Test parsing requirement ref with path."""
    env = unittest.begin(ctx)

    body = "See [REQ-001](requirements/safety/REQ-001.md)."

    refs = markdown_parser.parse_references(body)
    asserts.equals(env, [("REQ-001", "requirements/safety/REQ-001.md")], refs["requirements"])

    return unittest.end(env)

def _test_parse_multiple_refs_same_line(ctx):
    """Test parsing multiple refs on same line."""
    env = unittest.begin(ctx)

    body = "Uses [@p1](f.bzl#p1) and [@p2](f.bzl#p2) and [REQ-1](REQ-1.md)."

    refs = markdown_parser.parse_references(body)
    asserts.equals(env, [("p1", "f.bzl#p1"), ("p2", "f.bzl#p2")], refs["parameters"])
    asserts.equals(env, [("REQ-1", "REQ-1.md")], refs["requirements"])

    return unittest.end(env)

# Test suite
parse_requirement_references_test = unittest.make(_test_parse_requirement_references)
parse_parameter_references_test = unittest.make(_test_parse_parameter_references)
parse_test_references_test = unittest.make(_test_parse_test_references)
parse_mixed_references_test = unittest.make(_test_parse_mixed_references)
parse_no_references_test = unittest.make(_test_parse_no_references)
parse_empty_body_test = unittest.make(_test_parse_empty_body)
validate_matching_references_test = unittest.make(_test_validate_matching_references)
validate_missing_parameter_in_frontmatter_test = unittest.make(_test_validate_missing_parameter_in_frontmatter)
validate_missing_requirement_in_frontmatter_test = unittest.make(_test_validate_missing_requirement_in_frontmatter)
validate_missing_test_in_frontmatter_test = unittest.make(_test_validate_missing_test_in_frontmatter)
validate_no_frontmatter_with_body_refs_test = unittest.make(_test_validate_no_frontmatter_with_body_refs)
validate_no_body_refs_test = unittest.make(_test_validate_no_body_refs)
validate_empty_body_test = unittest.make(_test_validate_empty_body)
parse_requirement_with_path_test = unittest.make(_test_parse_requirement_with_path)
parse_multiple_refs_same_line_test = unittest.make(_test_parse_multiple_refs_same_line)

def markdown_parser_test_suite(name):
    """Create test suite for markdown_parser."""
    unittest.suite(
        name,
        parse_requirement_references_test,
        parse_parameter_references_test,
        parse_test_references_test,
        parse_mixed_references_test,
        parse_no_references_test,
        parse_empty_body_test,
        validate_matching_references_test,
        validate_missing_parameter_in_frontmatter_test,
        validate_missing_requirement_in_frontmatter_test,
        validate_missing_test_in_frontmatter_test,
        validate_no_frontmatter_with_body_refs_test,
        validate_no_body_refs_test,
        validate_empty_body_test,
        parse_requirement_with_path_test,
        parse_multiple_refs_same_line_test,
    )
