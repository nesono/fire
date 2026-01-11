#!/usr/bin/env python3
"""Unit tests for requirement metadata validation using Pydantic models."""

import unittest

from pydantic import ValidationError

from fire.starlark.requirement_models import RequirementMetadata


class TestRequirementMetadata(unittest.TestCase):
    """Test cases for RequirementMetadata Pydantic model."""

    def test_valid_asil_a(self):
        """Test valid ASIL-A requirement."""
        metadata = RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=True, version=1)
        self.assertEqual(metadata.sil, "ASIL-A")
        self.assertEqual(metadata.id, "REQ-001")
        self.assertTrue(metadata.sec)
        self.assertEqual(metadata.version, 1)

    def test_valid_asil_b(self):
        """Test valid ASIL-B requirement."""
        metadata = RequirementMetadata(id="REQ-002", sil="ASIL-B", sec=False, version=2)
        self.assertEqual(metadata.sil, "ASIL-B")

    def test_valid_asil_c(self):
        """Test valid ASIL-C requirement."""
        metadata = RequirementMetadata(id="REQ-003", sil="ASIL-C", sec=True, version=1)
        self.assertEqual(metadata.sil, "ASIL-C")

    def test_valid_asil_d(self):
        """Test valid ASIL-D requirement."""
        metadata = RequirementMetadata(id="REQ-004", sil="ASIL-D", sec=True, version=1)
        self.assertEqual(metadata.sil, "ASIL-D")

    def test_valid_sil_1(self):
        """Test valid SIL-1 requirement."""
        metadata = RequirementMetadata(id="REQ-005", sil="SIL-1", sec=False, version=2)
        self.assertEqual(metadata.sil, "SIL-1")

    def test_valid_sil_2(self):
        """Test valid SIL-2 requirement."""
        metadata = RequirementMetadata(id="REQ-006", sil="SIL-2", sec=True, version=1)
        self.assertEqual(metadata.sil, "SIL-2")

    def test_valid_sil_3(self):
        """Test valid SIL-3 requirement."""
        metadata = RequirementMetadata(id="REQ-007", sil="SIL-3", sec=True, version=1)
        self.assertEqual(metadata.sil, "SIL-3")

    def test_valid_sil_4(self):
        """Test valid SIL-4 requirement."""
        metadata = RequirementMetadata(id="REQ-008", sil="SIL-4", sec=True, version=1)
        self.assertEqual(metadata.sil, "SIL-4")

    def test_valid_qm(self):
        """Test valid QM requirement."""
        metadata = RequirementMetadata(id="REQ-009", sil="QM", sec=True, version=1)
        self.assertEqual(metadata.sil, "QM")

    def test_invalid_sil_value(self):
        """Test invalid SIL value."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-E",  # Invalid
                sec=True,
                version=1,
            )
        errors = cm.exception.errors()
        self.assertIn("sil", str(errors))

    def test_invalid_sil_lowercase(self):
        """Test lowercase SIL value is invalid."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="asil-a",  # Should be uppercase
                sec=True,
                version=1,
            )
        errors = cm.exception.errors()
        self.assertIn("sil", str(errors))

    def test_missing_sil(self):
        """Test missing SIL field."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                # sil missing
                sec=True,
                version=1,
            )
        errors = cm.exception.errors()
        self.assertTrue(any("sil" in str(e) for e in errors))

    def test_sec_true(self):
        """Test sec field with true value."""
        metadata = RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=True, version=1)
        self.assertTrue(metadata.sec)

    def test_sec_false(self):
        """Test sec field with false value."""
        metadata = RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=False, version=1)
        self.assertFalse(metadata.sec)

    def test_invalid_sec_string(self):
        """Test sec field rejects string."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec="true",  # String instead of bool
                version=1,
            )
        errors = cm.exception.errors()
        self.assertIn("sec", str(errors))

    def test_invalid_sec_integer(self):
        """Test sec field rejects integer."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=1,  # Integer instead of bool
                version=1,
            )
        errors = cm.exception.errors()
        self.assertIn("sec", str(errors))

    def test_missing_sec(self):
        """Test missing sec field."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                # sec missing
                version=1,
            )
        errors = cm.exception.errors()
        self.assertTrue(any("sec" in str(e) for e in errors))

    def test_version_positive(self):
        """Test version must be positive."""
        metadata = RequirementMetadata(id="REQ-001", sil="ASIL-A", sec=True, version=1)
        self.assertEqual(metadata.version, 1)

    def test_version_large(self):
        """Test large version number."""
        metadata = RequirementMetadata(
            id="REQ-001", sil="ASIL-A", sec=True, version=999
        )
        self.assertEqual(metadata.version, 999)

    def test_version_zero_invalid(self):
        """Test version=0 is invalid."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=True,
                version=0,  # Invalid
            )
        errors = cm.exception.errors()
        self.assertIn("version", str(errors))
        self.assertIn("greater than or equal", str(errors).lower())

    def test_version_negative_invalid(self):
        """Test negative version is invalid."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=True,
                version=-1,  # Invalid
            )
        errors = cm.exception.errors()
        self.assertIn("version", str(errors))

    def test_version_string_invalid(self):
        """Test version as string is invalid."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=True,
                version="1",  # String instead of int
            )
        errors = cm.exception.errors()
        self.assertIn("version", str(errors))

    def test_missing_version(self):
        """Test missing version field."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=True,
                # version missing
            )
        errors = cm.exception.errors()
        self.assertTrue(any("version" in str(e) for e in errors))

    def test_parent_optional(self):
        """Test parent field is optional."""
        metadata = RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=1,
            # parent omitted
        )
        self.assertIsNone(metadata.parent)

    def test_parent_valid_format(self):
        """Test valid parent markdown link."""
        metadata = RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=1,
            parent="[REQ-BASE](/path/to/file.md?version=1#REQ-BASE)",
        )
        self.assertIsNotNone(metadata.parent)
        self.assertEqual(
            metadata.parent, "[REQ-BASE](/path/to/file.md?version=1#REQ-BASE)"
        )

    def test_parent_valid_without_version(self):
        """Test valid parent without version query param."""
        metadata = RequirementMetadata(
            id="REQ-001",
            sil="ASIL-A",
            sec=True,
            version=1,
            parent="[REQ-BASE](/path/to/file.md#REQ-BASE)",
        )
        self.assertIsNotNone(metadata.parent)

    def test_parent_non_absolute_path(self):
        """Test parent with non-repository-relative path fails."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=True,
                version=1,
                parent="[REQ-BASE](path/to/file.md)",  # Missing leading /
            )
        errors = cm.exception.errors()
        self.assertIn("parent", str(errors))
        self.assertIn("repository-relative", str(errors))

    def test_parent_relative_with_dotdot(self):
        """Test parent with ../ relative path fails."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=True,
                version=1,
                parent="[REQ-BASE](../requirements/file.md)",
            )
        errors = cm.exception.errors()
        self.assertIn("parent", str(errors))
        self.assertIn("repository-relative", str(errors))

    def test_parent_invalid_format_no_brackets(self):
        """Test parent with invalid markdown format fails."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=True,
                version=1,
                parent="REQ-BASE",  # Not a markdown link
            )
        errors = cm.exception.errors()
        self.assertIn("parent", str(errors))
        self.assertIn("markdown link", str(errors))

    def test_parent_invalid_format_missing_url(self):
        """Test parent with missing URL fails."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=True,
                version=1,
                parent="[REQ-BASE]",  # Missing URL part
            )
        errors = cm.exception.errors()
        self.assertIn("parent", str(errors))
        self.assertIn("markdown link", str(errors))

    def test_id_valid_pattern(self):
        """Test valid ID patterns."""
        # Test various valid ID formats
        valid_ids = ["REQ-001", "REQ_001", "SYS-REQ-100", "TEST_CASE_A"]
        for req_id in valid_ids:
            metadata = RequirementMetadata(id=req_id, sil="ASIL-A", sec=True, version=1)
            self.assertEqual(metadata.id, req_id)

    def test_id_invalid_lowercase(self):
        """Test ID with lowercase fails."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="req-001",  # Lowercase
                sil="ASIL-A",
                sec=True,
                version=1,
            )
        errors = cm.exception.errors()
        self.assertIn("id", str(errors))

    def test_id_invalid_starts_with_digit(self):
        """Test ID starting with digit fails."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="001-REQ",  # Starts with digit
                sil="ASIL-A",
                sec=True,
                version=1,
            )
        errors = cm.exception.errors()
        self.assertIn("id", str(errors))

    def test_extra_field_forbidden(self):
        """Test extra fields are rejected."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="REQ-001",
                sil="ASIL-A",
                sec=True,
                version=1,
                extra_field="not allowed",  # Extra field
            )
        errors = cm.exception.errors()
        self.assertIn("extra", str(errors).lower())

    def test_multiple_errors(self):
        """Test multiple validation errors are reported."""
        with self.assertRaises(ValidationError) as cm:
            RequirementMetadata(
                id="req-001",  # Invalid: lowercase
                sil="ASIL-E",  # Invalid: not in enum
                sec="true",  # Invalid: string instead of bool
                version=0,  # Invalid: must be >= 1
            )
        errors = cm.exception.errors()
        # Should have multiple errors
        self.assertGreaterEqual(len(errors), 4)


if __name__ == "__main__":
    unittest.main()
