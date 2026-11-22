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


class TestReferenceChecks:
    def test_links_are_checked_inside_a_workspace(self, tmp_path):
        (tmp_path / "MODULE.bazel").write_text("")
        uri = (tmp_path / "a.sysreq.md").as_uri()
        text = "## R-1\n\nSIL: QM | Sec: false | Version: 1\n\n[@x](/gone.yaml?version=1#x)\n"
        assert [d.code for d in _ANALYZER.diagnose(uri, text)] == ["FIRE012"]

    def test_unsaved_target_in_overlay_satisfies_the_link(self, tmp_path):
        (tmp_path / "MODULE.bazel").write_text("")
        doc = tmp_path / "a.sysreq.md"
        text = (
            "## R-1\n\nSIL: QM | Sec: false | Version: 1\n\n[@x](/p.yaml?version=1#x)\n"
        )
        overlay = {tmp_path / "p.yaml": "x_v1:\n  value: 1\n"}
        assert _ANALYZER.diagnose(doc.as_uri(), text, overlay) == []

    def test_overlay_wins_over_disk(self, tmp_path):
        (tmp_path / "MODULE.bazel").write_text("")
        (tmp_path / "p.yaml").write_text("x_v1:\n  value: 1\n")
        doc = tmp_path / "a.sysreq.md"
        text = (
            "## R-1\n\nSIL: QM | Sec: false | Version: 1\n\n[@x](/p.yaml?version=1#x)\n"
        )
        overlay = {tmp_path / "p.yaml": "y_v1:\n  value: 1\n"}
        codes = [d.code for d in _ANALYZER.diagnose(doc.as_uri(), text, overlay)]
        assert codes == ["FIRE013"]

    def test_links_are_not_resolved_without_a_workspace(self):
        text = "## R-1\n\nSIL: QM | Sec: false | Version: 1\n\n[@x](/gone.yaml?version=1#x)\n"
        assert _ANALYZER.diagnose("file:///nowhere/a.sysreq.md", text) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
