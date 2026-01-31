#!/usr/bin/env python3
"""Unit tests for bare TODO scanner in validate_cross_references."""

import sys

import pytest

from fire.starlark.validate_cross_references import validate_no_bare_todos  # type: ignore


def test_bare_todo_in_prose_rejected():
    """Bare TODO in prose body is detected."""
    content = "## REQ-001\nSIL: ASIL-A | Sec: true | Version: 1\nTODO fix this later\n"
    errors = validate_no_bare_todos(content, "test.md")
    assert len(errors) == 1


def test_valid_todo_in_prose_accepted():
    """Properly formatted TODO in prose is accepted."""
    content = (
        "## REQ-001\nSIL: ASIL-A | Sec: true | Version: 1\n"
        "See TODO(JIRA-123) for details\n"
    )
    errors = validate_no_bare_todos(content, "test.md")
    assert len(errors) == 0


def test_todo_empty_parens_in_prose_rejected():
    """TODO() in prose is detected."""
    content = "Some text with TODO() here\n"
    errors = validate_no_bare_todos(content, "test.md")
    assert len(errors) == 1


def test_todo_bad_format_in_prose_rejected():
    """TODO(bad) in prose is detected."""
    content = "TODO(bad)\n"
    errors = validate_no_bare_todos(content, "test.md")
    assert len(errors) == 1


def test_multiple_todos_on_one_line():
    """Multiple TODOs on one line are each validated."""
    content = "TODO and TODO(JIRA-1) and TODO(bad)\n"
    errors = validate_no_bare_todos(content, "test.md")
    assert len(errors) == 2  # "TODO" and "TODO(bad)"


def test_no_todos_at_all():
    """File without any TODO markers passes."""
    content = "Just regular text\nNo special markers\n"
    errors = validate_no_bare_todos(content, "test.md")
    assert len(errors) == 0


def test_todo_in_metadata_field_accepted():
    """TODO(KEY-1234) in metadata line is accepted."""
    content = "## REQ-001\nSIL: TODO(JIRA-123) | Sec: true | Version: 1\n"
    errors = validate_no_bare_todos(content, "test.md")
    assert len(errors) == 0


def test_todo_lowercase_key_rejected():
    """TODO(jira-123) with lowercase key is rejected."""
    content = "See TODO(jira-123) for details\n"
    errors = validate_no_bare_todos(content, "test.md")
    assert len(errors) == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
