#!/usr/bin/env python3
"""Tests for inline metadata parsing."""

from fire.starlark.metadata_parsing import (
    extract_next_metadata_line,
    is_metadata_line,
    parse_metadata_fields,
)

_KNOWN_FIELDS = ["sil", "sec", "version", "parent"]


class TestIsMetadataLine:
    def test_pipe_separated_line(self):
        assert is_metadata_line("Sil: ASIL-D | Sec: false", _KNOWN_FIELDS)

    def test_single_known_field(self):
        assert is_metadata_line("Version: 1", _KNOWN_FIELDS)

    def test_heading_is_not_metadata(self):
        assert not is_metadata_line("# Heading: foo", _KNOWN_FIELDS)

    def test_unknown_field_without_pipe(self):
        assert not is_metadata_line("Author: Jane", _KNOWN_FIELDS)

    def test_blank_line(self):
        assert not is_metadata_line("", _KNOWN_FIELDS)


class TestExtractNextMetadataLine:
    def test_single_metadata_line_after_heading(self):
        lines = [
            "## REQ-1",
            "Sil: ASIL-D | Sec: false | Version: 1",
            "",
            "Body",
        ]
        assert (
            extract_next_metadata_line(lines, 0)
            == "Sil: ASIL-D | Sec: false | Version: 1"
        )

    def test_continuation_via_trailing_pipe(self):
        lines = [
            "## REQ-1",
            "Sil: ASIL-D |",
            "Sec: false | Version: 1",
            "",
        ]
        assert (
            extract_next_metadata_line(lines, 0)
            == "Sil: ASIL-D | Sec: false | Version: 1"
        )

    def test_no_metadata_line_returns_none(self):
        lines = ["## REQ-1", "Body without metadata"]
        assert extract_next_metadata_line(lines, 0) is None

    def test_default_known_fields(self):
        lines = ["## REQ-1", "Version: 2"]
        assert extract_next_metadata_line(lines, 0) == "Version: 2"

    def test_custom_known_fields(self):
        lines = ["## REQ-1", "Author: Jane"]
        assert (
            extract_next_metadata_line(lines, 0, known_fields=["author"])
            == "Author: Jane"
        )


class TestParseMetadataFields:
    def test_parses_basic_fields(self):
        result = parse_metadata_fields("Sil: ASIL-D | Version: 1", "REQ-1")
        assert result == {"id": "REQ-1", "sil": "ASIL-D", "version": 1}

    def test_parses_boolean_lowercase(self):
        result = parse_metadata_fields("Sec: false", "REQ-1")
        assert result == {"id": "REQ-1", "sec": False}

    def test_aggregates_parent_into_list(self):
        result = parse_metadata_fields(
            "Parent: [REQ-A](/a.md) | Parent: [REQ-B](/b.md)",
            "REQ-1",
        )
        assert result["parent"] == ["[REQ-A](/a.md)", "[REQ-B](/b.md)"]

    def test_single_parent_still_in_list(self):
        result = parse_metadata_fields("Parent: [REQ-A](/a.md)", "REQ-1")
        assert result["parent"] == ["[REQ-A](/a.md)"]

    def test_empty_fields_are_skipped(self):
        result = parse_metadata_fields("Sil: ASIL-D | | Version: 1", "REQ-1")
        assert result == {"id": "REQ-1", "sil": "ASIL-D", "version": 1}

    def test_int_string_remains_string_if_not_pure_digits(self):
        result = parse_metadata_fields("Sil: ASIL-1", "REQ-1")
        assert result == {"id": "REQ-1", "sil": "ASIL-1"}
