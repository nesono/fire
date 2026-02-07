#!/usr/bin/env python3
"""Unit tests for requirement metadata validation using Pydantic models."""

import sys

import pytest
from pydantic import ValidationError

from fire.starlark.requirement_models import RequirementMetadata


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
        parent="[REQ-BASE](/path/to/file.md?version=1#REQ-BASE)",
    )
    assert metadata.parent is not None
    assert metadata.parent == "[REQ-BASE](/path/to/file.md?version=1#REQ-BASE)"


def test_parent_valid_without_version():
    """Test valid parent without version query param."""
    metadata = RequirementMetadata(
        id="REQ-001",
        sil="ASIL-A",
        sec=True,
        version=1,
        parent="[REQ-BASE](/path/to/file.md#REQ-BASE)",
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
            parent="[REQ-BASE](path/to/file.md)",  # Missing leading /
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
            parent="[REQ-BASE](../requirements/file.md)",
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
            parent="REQ-BASE",  # Not a markdown link
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
            parent="[REQ-BASE]",  # Missing URL part
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
        id="REQ-001", sil="ASIL-A", sec=True, version=1, parent="TODO(JIRA-789)"
    )
    assert metadata.parent == "TODO(JIRA-789)"


def test_parent_bare_todo_rejected():
    """Bare TODO is rejected for Parent."""
    with pytest.raises(ValidationError):
        RequirementMetadata(
            id="REQ-001", sil="ASIL-A", sec=True, version=1, parent="TODO"
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
        parent="TODO(SAFETY-3)",
    )
    assert metadata.sil == "TODO(SAFETY-1)"
    assert metadata.sec == "TODO(SAFETY-2)"
    assert metadata.parent == "TODO(SAFETY-3)"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
