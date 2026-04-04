#!/usr/bin/env python3
"""Tests for validate_release_readiness."""

import tempfile

import pytest

from fire.starlark import validate_release_readiness


def test_validate_ready_for_release():
    """Test validation passes when report indicates ready."""
    content = """# Release Readiness Report: Product

## Release Readiness Summary

**Status: READY FOR RELEASE**

✓ No issues found - all checks passed
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        result = validate_release_readiness.validate_release_readiness(f.name)

    assert result == 0


def test_validate_not_ready_for_release():
    """Test validation fails when report indicates not ready."""
    content = """# Release Readiness Report: Product

## Release Readiness Summary

**Status: NOT READY FOR RELEASE**

### Issues Found

- ⚠️  Missing implementation traces: **2** ([details](#missing-implementation-traces))
- ⚠️  Open TODOs: **1** ([details](#todo-inventory))
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        result = validate_release_readiness.validate_release_readiness(f.name)

    assert result == 1


def test_validate_malformed_report():
    """Test validation fails when report is malformed."""
    content = """# Some Random Document

This is not a release report.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        result = validate_release_readiness.validate_release_readiness(f.name)

    assert result == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
