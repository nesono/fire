#!/usr/bin/env python3
"""Unit tests for requirement metadata validation using Pydantic models."""

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
