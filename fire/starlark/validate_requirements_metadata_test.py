#!/usr/bin/env python3
"""Unit tests for requirement metadata validation using Pydantic models."""

import sys

import pytest
from pydantic import ValidationError

from fire.starlark.requirement_models import (
    RegulatoryRequirementMetadata,
    RequirementMetadata,
)
from fire.starlark.validate_cross_references import (
    parse_inline_metadata_for_requirement,
)


def test_valid_asil_a():
    """Test valid ASIL-A requirement."""
    metadata = RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=True, version=1)
    assert metadata.sil == "ASIL-A"
    assert metadata.id == "REQ-001"
    assert metadata.sec is True
    assert metadata.version == 1


def test_valid_asil_b():
    """Test valid ASIL-B requirement."""
    metadata = RequirementMetadata(id="REQ-002", sil="ASIL-B", sec=False, version=2)
    assert metadata.sil == "ASIL-B"


def test_valid_asil_c():
    """Test valid ASIL-C requirement."""
    metadata = RequirementMetadata(id="REQ-003", sil="ASIL-C", sec=True, version=1)
    assert metadata.sil == "ASIL-C"


def test_valid_asil_d():
    """Test valid ASIL-D requirement."""
    metadata = RequirementMetadata(id="REQ-004", sil="ASIL-D", sec=True, version=1)
    assert metadata.sil == "ASIL-D"


def test_valid_sil_1():
    """Test valid SIL-1 requirement."""
    metadata = RequirementMetadata(id="REQ-005", sil="SIL-1", sec=False, version=2)
    assert metadata.sil == "SIL-1"


def test_valid_sil_2():
    """Test valid SIL-2 requirement."""
    metadata = RequirementMetadata(id="REQ-006", sil="SIL-2", sec=True, version=1)
    assert metadata.sil == "SIL-2"


def test_valid_sil_3():
    """Test valid SIL-3 requirement."""
    metadata = RequirementMetadata(id="REQ-007", sil="SIL-3", sec=True, version=1)
    assert metadata.sil == "SIL-3"


def test_valid_sil_4():
    """Test valid SIL-4 requirement."""
    metadata = RequirementMetadata(id="REQ-008", sil="SIL-4", sec=True, version=1)
    assert metadata.sil == "SIL-4"


def test_valid_qm():
    """Test valid QM requirement."""
    metadata = RequirementMetadata(id="REQ-009", sil="QM", sec=True, version=1)
    assert metadata.sil == "QM"


def test_valid_dal_a():
    """Test valid DAL-A requirement."""
    metadata = RequirementMetadata(id="REQ-010", sil="DAL-A", sec=True, version=1)
    assert metadata.sil == "DAL-A"


def test_valid_dal_b():
    """Test valid DAL-B requirement."""
    metadata = RequirementMetadata(id="REQ-011", sil="DAL-B", sec=True, version=1)
    assert metadata.sil == "DAL-B"


def test_valid_dal_c():
    """Test valid DAL-C requirement."""
    metadata = RequirementMetadata(id="REQ-012", sil="DAL-C", sec=False, version=1)
    assert metadata.sil == "DAL-C"


def test_valid_dal_d():
    """Test valid DAL-D requirement."""
    metadata = RequirementMetadata(id="REQ-013", sil="DAL-D", sec=False, version=1)
    assert metadata.sil == "DAL-D"


def test_valid_dal_e():
    """Test valid DAL-E requirement."""
    metadata = RequirementMetadata(id="REQ-014", sil="DAL-E", sec=False, version=1)
    assert metadata.sil == "DAL-E"


def test_invalid_dal_f():
    """Test invalid DAL-F value (only A-E are valid)."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-015",
            sil="DAL-F",  # Invalid - DAL only goes to E
            sec=True,
            version=1,
        )
    errors = exc_info.value.errors()
    assert "sil" in str(errors)


def test_invalid_dal_lowercase():
    """Test lowercase DAL value is invalid."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-016",
            sil="dal-a",  # Should be uppercase
            sec=True,
            version=1,
        )
    errors = exc_info.value.errors()
    assert "sil" in str(errors)


def test_invalid_sil_value():
    """Test invalid SIL value."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-E",  # Invalid
            sec=True,
            version=1,
        )
    errors = exc_info.value.errors()
    assert "sil" in str(errors)


def test_invalid_sil_lowercase():
    """Test lowercase SIL value is invalid."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="asil-a",  # Should be uppercase
            sec=True,
            version=1,
        )
    errors = exc_info.value.errors()
    assert "sil" in str(errors)


def test_missing_sil():
    """Test missing SIL field."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            # sil missing
            sec=True,
            version=1,
        )
    errors = exc_info.value.errors()
    assert any("sil" in str(e) for e in errors)


def test_sec_true():
    """Test sec field with true value."""
    metadata = RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=True, version=1)
    assert metadata.sec is True


def test_sec_false():
    """Test sec field with false value."""
    metadata = RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=False, version=1)
    assert metadata.sec is False


def test_invalid_sec_string():
    """Test sec field rejects string."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec="true",  # String instead of bool
            version=1,
        )
    errors = exc_info.value.errors()
    assert "sec" in str(errors)


def test_invalid_sec_integer():
    """Test sec field rejects integer."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=1,  # Integer instead of bool
            version=1,
        )
    errors = exc_info.value.errors()
    assert "sec" in str(errors)


def test_missing_sec():
    """Test missing sec field."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            # sec missing
            version=1,
        )
    errors = exc_info.value.errors()
    assert any("sec" in str(e) for e in errors)


def test_version_positive():
    """Test version must be positive."""
    metadata = RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=True, version=1)
    assert metadata.version == 1


def test_version_large():
    """Test large version number."""
    metadata = RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=True, version=999)
    assert metadata.version == 999


def test_version_zero_invalid():
    """Test version=0 is invalid."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=0,  # Invalid
        )
    errors = exc_info.value.errors()
    assert "version" in str(errors)
    assert "greater than or equal" in str(errors).lower()


def test_version_negative_invalid():
    """Test negative version is invalid."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=-1,  # Invalid
        )
    errors = exc_info.value.errors()
    assert "version" in str(errors)


def test_version_string_invalid():
    """Test version as string is invalid."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version="1",  # String instead of int
        )
    errors = exc_info.value.errors()
    assert "version" in str(errors)


def test_missing_version():
    """Test missing version field."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            # version missing
        )
    errors = exc_info.value.errors()
    assert any("version" in str(e) for e in errors)


def test_parent_optional():
    """Test parent field is optional."""
    metadata = RequirementMetadata(
        id="REQ-001",
        sil="ASIL-A",
        sec=True,
        version=1,
        # parent omitted
    )
    assert metadata.parent is None


def test_parent_valid_format():
    """Test valid parent markdown link."""
    metadata = RequirementMetadata(
        id="REQ-001",
        sil="ASIL-A",
        sec=True,
        version=1,
        parent=["[REQ-BASE](/path/to/file.md?version=1#REQ-BASE)"],
    )
    assert metadata.parent is not None
    assert metadata.parent == ["[REQ-BASE](/path/to/file.md?version=1#REQ-BASE)"]


def test_parent_valid_without_version():
    """Test valid parent without version query param."""
    metadata = RequirementMetadata(
        id="REQ-001",
        sil="ASIL-A",
        sec=True,
        version=1,
        parent=["[REQ-BASE](/path/to/file.md#REQ-BASE)"],
    )
    assert metadata.parent is not None


def test_parent_non_absolute_path():
    """Test parent with non-repository-relative path fails."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=1,
            parent=["[REQ-BASE](path/to/file.md)"],  # Missing leading /
        )
    errors = exc_info.value.errors()
    assert "parent" in str(errors)
    assert "repository-relative" in str(errors)


def test_parent_relative_with_dotdot():
    """Test parent with ../ relative path fails."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=1,
            parent=["[REQ-BASE](../requirements/file.md)"],
        )
    errors = exc_info.value.errors()
    assert "parent" in str(errors)
    assert "repository-relative" in str(errors)


def test_parent_invalid_format_no_brackets():
    """Test parent with invalid markdown format fails."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=1,
            parent=["REQ-BASE"],  # Not a markdown link
        )
    errors = exc_info.value.errors()
    assert "parent" in str(errors)
    assert "markdown link" in str(errors)


def test_parent_invalid_format_missing_url():
    """Test parent with missing URL fails."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=1,
            parent=["[REQ-BASE]"],  # Missing URL part
        )
    errors = exc_info.value.errors()
    assert "parent" in str(errors)
    assert "markdown link" in str(errors)


def test_id_valid_pattern():
    """Test valid ID patterns."""
    # Test various valid ID formats
    valid_ids = ["REQ-001", "REQ_001", "SYS-REQ-100", "TEST_CASE_A"]
    for req_id in valid_ids:
        metadata = RequirementMetadata(id=req_id, sil="ASIL-A", sec=True, version=1)
        assert metadata.id == req_id


def test_id_invalid_lowercase():
    """Test ID with lowercase fails."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="req-001",  # Lowercase
            sil="ASIL-A",
            sec=True,
            version=1,
        )
    errors = exc_info.value.errors()
    assert "id" in str(errors)


def test_id_invalid_starts_with_digit():
    """Test ID starting with digit fails."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="001-REQ",  # Starts with digit
            sil="ASIL-A",
            sec=True,
            version=1,
        )
    errors = exc_info.value.errors()
    assert "id" in str(errors)


def test_extra_field_forbidden():
    """Test extra fields are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=1,
            extra_field="not allowed",  # Extra field
        )
    errors = exc_info.value.errors()
    assert "extra" in str(errors).lower()


def test_multiple_errors():
    """Test multiple validation errors are reported."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="req-001",  # Invalid: lowercase
            sil="ASIL-E",  # Invalid: not in enum
            sec="true",  # Invalid: string instead of bool
            version=0,  # Invalid: must be >= 1
        )
    errors = exc_info.value.errors()
    # Should have multiple errors
    assert len(errors) >= 4


# --- TODO(KEY-1234) support for SIL field ---


def test_sil_valid_todo():
    """TODO(KEY-1234) is accepted for SIL field."""
    metadata = RequirementMetadata(
        id="REQ-001", sil="TODO(JIRA-123)", sec=True, version=1
    )
    assert metadata.sil == "TODO(JIRA-123)"


def test_sil_valid_todo_long_key():
    """TODO with multi-char key and large number."""
    metadata = RequirementMetadata(
        id="REQ-001", sil="TODO(SAFETY-99999)", sec=True, version=1
    )
    assert metadata.sil == "TODO(SAFETY-99999)"


def test_sil_bare_todo_rejected():
    """Bare TODO without parens is rejected for SIL."""
    with pytest.raises(ValidationError):
        RequirementMetadata(id="REQ-001", sil="TODO", sec=True, version=1)


def test_sil_todo_empty_parens_rejected():
    """TODO() is rejected for SIL."""
    with pytest.raises(ValidationError):
        RequirementMetadata(id="REQ-001", sil="TODO()", sec=True, version=1)


def test_sil_todo_lowercase_key_rejected():
    """TODO(jira-123) with lowercase key is rejected."""
    with pytest.raises(ValidationError):
        RequirementMetadata(id="REQ-001", sil="TODO(jira-123)", sec=True, version=1)


def test_sil_todo_no_number_rejected():
    """TODO(JIRA) without ticket number is rejected."""
    with pytest.raises(ValidationError):
        RequirementMetadata(id="REQ-001", sil="TODO(JIRA)", sec=True, version=1)


# --- TODO(KEY-1234) support for Sec field ---


def test_sec_valid_todo():
    """TODO(KEY-1234) is accepted for Sec field."""
    metadata = RequirementMetadata(
        id="REQ-001", sil="ASIL-A", sec="TODO(JIRA-456)", version=1
    )
    assert metadata.sec == "TODO(JIRA-456)"


def test_sec_bare_todo_rejected():
    """Bare TODO is rejected for Sec."""
    with pytest.raises(ValidationError):
        RequirementMetadata(id="REQ-001", sil="ASIL-A", sec="TODO", version=1)


def test_sec_string_true_still_rejected():
    """String 'true' is still rejected for Sec (strict bool)."""
    with pytest.raises(ValidationError):
        RequirementMetadata(id="REQ-001", sil="ASIL-A", sec="true", version=1)


def test_sec_int_still_rejected():
    """Integer 1 is still rejected for Sec (strict bool)."""
    with pytest.raises(ValidationError):
        RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=1, version=1)


# --- TODO(KEY-1234) support for Parent field ---


def test_parent_valid_todo():
    """TODO(KEY-1234) is accepted for Parent field."""
    metadata = RequirementMetadata(
        id="REQ-001", sil="ASIL-A", sec=True, version=1, parent=["TODO(JIRA-789)"]
    )
    assert metadata.parent == ["TODO(JIRA-789)"]


def test_parent_bare_todo_rejected():
    """Bare TODO is rejected for Parent."""
    with pytest.raises(ValidationError):
        RequirementMetadata(
            id="REQ-001", sil="ASIL-A", sec=True, version=1, parent=["TODO"]
        )


# --- Version does NOT support TODO ---


def test_version_todo_rejected():
    """TODO is NOT allowed for Version field."""
    with pytest.raises(ValidationError):
        RequirementMetadata(
            id="REQ-001", sil="ASIL-A", sec=True, version="TODO(JIRA-123)"
        )


# --- Multiple TODO fields at once ---


def test_all_todo_fields():
    """All TODO-able fields can be TODO simultaneously."""
    metadata = RequirementMetadata(
        id="REQ-001",
        sil="TODO(SAFETY-1)",
        sec="TODO(SAFETY-2)",
        version=1,
        parent=["TODO(SAFETY-3)"],
    )
    assert metadata.sil == "TODO(SAFETY-1)"
    assert metadata.sec == "TODO(SAFETY-2)"
    assert metadata.parent == ["TODO(SAFETY-3)"]


# --- Multi-parent support tests ---


def test_parent_multiple_valid():
    """Test multiple parent entries."""
    metadata = RequirementMetadata(
        id="REQ-001",
        sil="ASIL-D",
        sec=True,
        version=1,
        parent=[
            "[REQ-A](/path1.md?version=1#REQ-A)",
            "[REQ-B](/path2.md?version=2#REQ-B)",
        ],
    )
    assert len(metadata.parent) == 2
    assert metadata.parent[0] == "[REQ-A](/path1.md?version=1#REQ-A)"
    assert metadata.parent[1] == "[REQ-B](/path2.md?version=2#REQ-B)"


def test_parent_multiple_three_parents():
    """Test three parent entries."""
    metadata = RequirementMetadata(
        id="REQ-001",
        sil="ASIL-D",
        sec=True,
        version=1,
        parent=[
            "[REQ-A](/path1.md?version=1#REQ-A)",
            "[REQ-B](/path2.md?version=2#REQ-B)",
            "[REQ-C](/path3.md?version=3#REQ-C)",
        ],
    )
    assert len(metadata.parent) == 3


def test_parent_mixed_markdown_and_todo():
    """Test mixed markdown links and TODO placeholders."""
    metadata = RequirementMetadata(
        id="REQ-001",
        sil="ASIL-D",
        sec=True,
        version=1,
        parent=["[REQ-A](/path.md#REQ-A)", "TODO(JIRA-123)"],
    )
    assert len(metadata.parent) == 2
    assert metadata.parent[0] == "[REQ-A](/path.md#REQ-A)"
    assert metadata.parent[1] == "TODO(JIRA-123)"


def test_parent_invalid_format_in_list():
    """Test that invalid format in any parent entry fails validation."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-D",
            sec=True,
            version=1,
            parent=[
                "[REQ-A](/path.md#REQ-A)",
                "not-a-markdown-link",  # Invalid
            ],
        )
    assert "parent must be a markdown link" in str(exc_info.value)


def test_parent_invalid_relative_path_in_list():
    """Test that relative path in any parent entry fails validation."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementMetadata(
            id="REQ-001",
            sil="ASIL-D",
            sec=True,
            version=1,
            parent=[
                "[REQ-A](/path.md#REQ-A)",
                "[REQ-B](relative/path.md#REQ-B)",  # Invalid - relative path
            ],
        )
    assert "repository-relative" in str(exc_info.value)


def test_parent_empty_list():
    """Test empty parent list is treated as None."""
    metadata = RequirementMetadata(
        id="REQ-001",
        sil="ASIL-D",
        sec=True,
        version=1,
        parent=[],
    )
    # Empty list is allowed
    assert metadata.parent == []


# --- Multi-line parsing tests ---


def test_parse_multiline_two_parents():
    """Test parsing multi-line metadata with two parents."""
    content = """
## REQ-001
SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-A](/p1.md#REQ-A) |
Parent: [REQ-B](/p2.md#REQ-B)

Body text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(content, "REQ-001")
    assert error is None
    assert metadata is not None
    assert len(metadata.parent) == 2
    assert metadata.parent[0] == "[REQ-A](/p1.md#REQ-A)"
    assert metadata.parent[1] == "[REQ-B](/p2.md#REQ-B)"


def test_parse_multiline_three_parents():
    """Test parsing multi-line metadata with three parents."""
    content = """
## REQ-001
SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-A](/p1.md#REQ-A) |
Parent: [REQ-B](/p2.md#REQ-B) |
Parent: [REQ-C](/p3.md#REQ-C)

Body text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(content, "REQ-001")
    assert error is None
    assert metadata is not None
    assert len(metadata.parent) == 3


def test_parse_backward_compatible_single_parent():
    """Test that old single-line format still works."""
    content = """
## REQ-001
SIL: ASIL-D | Sec: false | Version: 1 | Parent: [REQ-A](/p.md#REQ-A)

Text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(content, "REQ-001")
    assert error is None
    assert metadata is not None
    assert metadata.parent == ["[REQ-A](/p.md#REQ-A)"]  # Converted to list


def test_parse_single_line_no_parent():
    """Test single-line metadata without parent field."""
    content = """
## REQ-001
SIL: ASIL-D | Sec: false | Version: 1

Text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(content, "REQ-001")
    assert error is None
    assert metadata is not None
    assert metadata.parent is None


def test_parse_multiline_with_trailing_pipe_on_last_line():
    """Test that trailing pipe on last line is optional."""
    content = """
## REQ-001
SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-A](/p1.md#REQ-A) |
Parent: [REQ-B](/p2.md#REQ-B) |

Body text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(content, "REQ-001")
    assert error is None
    assert metadata is not None
    assert len(metadata.parent) == 2


def test_parse_multiline_mixed_todo_and_markdown():
    """Test parsing mixed TODO and markdown link parents."""
    content = """
## REQ-001
SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-A](/p1.md#REQ-A) |
Parent: TODO(JIRA-123)

Body text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(content, "REQ-001")
    assert error is None
    assert metadata is not None
    assert len(metadata.parent) == 2
    assert metadata.parent[0] == "[REQ-A](/p1.md#REQ-A)"
    assert metadata.parent[1] == "TODO(JIRA-123)"


def test_parse_multiline_empty_line_breaks_continuation():
    """Test that empty line breaks multi-line continuation."""
    content = """
## REQ-001
SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-A](/p1.md#REQ-A) |

Parent: [REQ-B](/p2.md#REQ-B)

Body text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(content, "REQ-001")
    assert error is None
    assert metadata is not None
    # Empty line breaks continuation, so only first parent is parsed
    assert len(metadata.parent) == 1
    assert metadata.parent[0] == "[REQ-A](/p1.md#REQ-A)"


def test_parse_multiline_missing_trailing_pipe_stops_continuation():
    """Test that missing trailing pipe stops continuation."""
    content = """
## REQ-001
SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-A](/p1.md#REQ-A)
Parent: [REQ-B](/p2.md#REQ-B)

Body text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(content, "REQ-001")
    assert error is None
    assert metadata is not None
    # Missing trailing pipe on first Parent line stops continuation
    assert len(metadata.parent) == 1
    assert metadata.parent[0] == "[REQ-A](/p1.md#REQ-A)"


# --- Regulatory requirement metadata tests ---


def test_regulatory_version_only():
    """Regulatory requirements need only version."""
    metadata = RegulatoryRequirementMetadata(id="REQ-REG-001", version=1)
    assert metadata.version == 1
    assert metadata.sil is None
    assert metadata.sec is None


def test_regulatory_with_sil():
    """Regulatory requirements may optionally include sil."""
    metadata = RegulatoryRequirementMetadata(id="REQ-REG-002", sil="ASIL-B", version=1)
    assert metadata.sil == "ASIL-B"
    assert metadata.sec is None


def test_regulatory_with_sec():
    """Regulatory requirements may optionally include sec."""
    metadata = RegulatoryRequirementMetadata(id="REQ-REG-003", sec=True, version=1)
    assert metadata.sil is None
    assert metadata.sec is True


def test_regulatory_with_all_fields():
    """Regulatory requirements accept all fields."""
    metadata = RegulatoryRequirementMetadata(
        id="REQ-REG-004", sil="SIL-2", sec=False, version=3
    )
    assert metadata.sil == "SIL-2"
    assert metadata.sec is False
    assert metadata.version == 3


def test_regulatory_version_still_required():
    """Version is still mandatory for regulatory requirements."""
    with pytest.raises(ValidationError):
        RegulatoryRequirementMetadata(id="REQ-REG-005")


def test_regulatory_invalid_sil_rejected():
    """Invalid sil values are still rejected when provided."""
    with pytest.raises(ValidationError):
        RegulatoryRequirementMetadata(id="REQ-REG-006", sil="INVALID", version=1)


def test_regulatory_invalid_sec_rejected():
    """Invalid sec values are still rejected when provided."""
    with pytest.raises(ValidationError):
        RegulatoryRequirementMetadata(id="REQ-REG-007", sec="true", version=1)


def test_regulatory_todo_sil():
    """TODO(KEY-1234) is accepted for optional sil on regreq."""
    metadata = RegulatoryRequirementMetadata(
        id="REQ-REG-009", sil="TODO(JIRA-100)", version=1
    )
    assert metadata.sil == "TODO(JIRA-100)"


def test_regulatory_parent_optional():
    """Parent is optional for regulatory requirements."""
    metadata = RegulatoryRequirementMetadata(
        id="REQ-REG-008",
        version=1,
        parent=["[REQ-A](/path.md#REQ-A)"],
    )
    assert len(metadata.parent) == 1


def test_parse_regulatory_version_only():
    """Test parsing regreq metadata with only version."""
    content = """
## REQ-REG-001
Version: 1

Some regulatory text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(
        content, "REQ-REG-001", RegulatoryRequirementMetadata
    )
    assert error is None
    assert metadata is not None
    assert metadata.version == 1
    assert metadata.sil is None
    assert metadata.sec is None


def test_parse_regulatory_with_sil_and_sec():
    """Test parsing regreq metadata with optional sil and sec."""
    content = """
## REQ-REG-002
SIL: ASIL-B | Sec: false | Version: 2

Some regulatory text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(
        content, "REQ-REG-002", RegulatoryRequirementMetadata
    )
    assert error is None
    assert metadata is not None
    assert metadata.sil == "ASIL-B"
    assert metadata.sec is False
    assert metadata.version == 2


def test_parse_sysreq_still_requires_sil_sec():
    """Parsing with RequirementMetadata still requires sil and sec."""
    content = """
## REQ-001
Version: 1

Some text.
---
"""
    metadata, error = parse_inline_metadata_for_requirement(
        content, "REQ-001", RequirementMetadata
    )
    assert metadata is None
    assert error is not None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
