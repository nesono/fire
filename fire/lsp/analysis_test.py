#!/usr/bin/env python3
"""Tests for per-document analysis."""

import pytest

from fire.lsp.analysis import Analyzer
from fire.starlark.config_models import load_config

_ANALYZER = Analyzer(load_config())
_BAD_SIL = "## REQ-1\n\nSIL: ASIL-Z | Sec: false | Version: 1\n"


class TestAnalyzer:
    def test_sysreq_is_validated_against_its_model(self):
        (diag,) = _ANALYZER.diagnose("file:///repo/a.sysreq.md", _BAD_SIL)
        assert diag.code == "FIRE005"

    def test_regreq_uses_the_regreq_model(self):
        text = "## REQ-1\n\nVersion: 1\n"
        assert _ANALYZER.diagnose("file:///repo/a.regreq.md", text) == []

    def test_unknown_suffix_is_ignored(self):
        assert _ANALYZER.diagnose("file:///repo/README.md", _BAD_SIL) == []

    def test_uri_with_escaped_characters(self):
        uri = "file:///repo/my%20dir/a.sysreq.md"
        assert len(_ANALYZER.diagnose(uri, _BAD_SIL)) == 1

    def test_columns_are_converted_to_utf16(self):
        text = "## REQ-1\n\nSIL: ASIL-Z | Sec: false | Version: 1\n😀 TODO\n"
        diags = _ANALYZER.diagnose("file:///a.sysreq.md", text)
        todo = [d for d in diags if d.code == "FIRE004"][0]
        assert todo.range.start.character == 3


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
