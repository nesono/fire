#!/usr/bin/env python3
"""Tests for config-driven metadata field diagnostics."""

import pytest

from fire.lsp.diagnostics import diagnose_requirements
from fire.lsp.document_parser import Position, Range
from fire.starlark.config_models import load_config
from fire.starlark.dynamic_requirement_model import build_models_from_config

_MODELS = build_models_from_config(load_config())
_SYSREQ = _MODELS["sysreq"]
_REGREQ = _MODELS["regreq"]

_VALID = "## REQ-1\n\nSIL: QM | Sec: false | Version: 1\n"


def _diagnose(text: str, model=_SYSREQ):
    return diagnose_requirements(text, model)


class TestFieldDiagnostics:
    def test_valid_metadata_has_no_diagnostics(self):
        assert _diagnose(_VALID) == []

    def test_todo_placeholders_are_valid(self):
        text = "## REQ-1\n\nSIL: TODO(A-1) | Sec: TODO(B-2) | Version: 1\n"
        assert _diagnose(text) == []

    def test_invalid_enum_value_points_at_value(self):
        (diag,) = _diagnose("## REQ-1\n\nSIL: ASIL-Z | Sec: false | Version: 1\n")
        assert diag.code == "FIRE005"
        assert diag.range == Range(Position(2, 5), Position(2, 11))

    def test_invalid_bool_value(self):
        (diag,) = _diagnose("## REQ-1\n\nSIL: QM | Sec: yes | Version: 1\n")
        assert (diag.code, diag.range.start.character) == ("FIRE005", 15)

    @pytest.mark.parametrize("version", ["0", "abc", "1.5"])
    def test_invalid_version(self, version):
        text = f"## REQ-1\n\nSIL: QM | Sec: false | Version: {version}\n"
        (diag,) = _diagnose(text)
        assert diag.code == "FIRE005"
        assert diag.range.start.character == 32

    def test_missing_required_field_points_at_heading(self):
        (diag,) = _diagnose("## REQ-1\n\nSIL: QM | Version: 1\n")
        assert diag.code == "FIRE006"
        assert diag.range == Range(Position(0, 3), Position(0, 8))
        assert "sec" in diag.message

    def test_unknown_field_points_at_key(self):
        text = "## REQ-1\n\nSIL: QM | Sec: false | Version: 1 | Foo: bar\n"
        (diag,) = _diagnose(text)
        assert diag.code == "FIRE007"
        assert diag.range == Range(Position(2, 36), Position(2, 39))

    def test_parent_must_be_a_link(self):
        text = _VALID.rstrip() + " | Parent: REQ-0\n"
        (diag,) = _diagnose(text)
        assert diag.code == "FIRE008"
        assert diag.range.start.character == 44

    def test_each_invalid_parent_is_reported(self):
        text = "## R-1\n\nSIL: QM | Sec: false | Version: 1 |\nParent: a |\nParent: b\n"
        assert [d.range.start.line for d in _diagnose(text)] == [3, 4]

    def test_valid_parent_link_and_todo(self):
        parent = "Parent: [R-0](/a.sysreq.md?version=1#R-0) |\nParent: TODO(X-1)"
        text = f"## R-1\n\nSIL: QM | Sec: false | Version: 1 |\n{parent}\n"
        assert _diagnose(text) == []

    def test_regreq_requires_only_version(self):
        assert _diagnose("## REQ-1\n\nVersion: 1\n", _REGREQ) == []

    def test_no_model_skips_field_validation(self):
        assert diagnose_requirements("## REQ-1\n\nVersion: x\n") == []

    def test_invalid_id_skips_field_validation(self):
        codes = [d.code for d in _diagnose("## bad\n\nVersion: x\n")]
        assert codes == ["FIRE001"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
