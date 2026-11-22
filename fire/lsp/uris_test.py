#!/usr/bin/env python3
"""Tests for converting document URIs to file paths."""

from pathlib import Path

import pytest

from fire.lsp.uris import uri_to_path


def test_file_uri():
    assert uri_to_path("file:///repo/a.sysreq.md") == Path("/repo/a.sysreq.md")


def test_percent_escapes_are_decoded():
    assert uri_to_path("file:///my%20dir/a.md") == Path("/my dir/a.md")


@pytest.mark.parametrize("uri", ["untitled:Untitled-1", "https://example.com/a.md"])
def test_non_file_uris_have_no_path(uri):
    assert uri_to_path(uri) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
