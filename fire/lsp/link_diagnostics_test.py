#!/usr/bin/env python3
"""Tests for syntactic link diagnostics."""

import pytest

from fire.lsp.diagnostic import Severity
from fire.lsp.diagnostics import diagnose_requirements
from fire.lsp.document_parser import Position, Range

_HEAD = "## REQ-1\n\nSIL: QM | Sec: false | Version: 1\n\n"
_PARAM = "[@max_speed](/p.yaml?version=1#max_speed)"
_REQ = "[REQ-2](/a.sysreq.md?version=1#REQ-2)"


def _diagnose(body: str):
    return diagnose_requirements(_HEAD + body + "\n")


class TestValidLinks:
    @pytest.mark.parametrize(
        "link",
        [
            _PARAM,
            _REQ,
            "[@max_speed](/p.yaml?version=1)",
            "[docs](https://example.com/page)",
            "[see](/README.md)",
            "[@config](<TODO(PARAM-789)>)",
        ],
    )
    def test_no_diagnostics(self, link):
        assert _diagnose(f"See {link}.") == []


class TestRepositoryRelativePaths:
    def test_relative_parameter_path(self):
        (diag,) = _diagnose("See [@max_speed](p.yaml?version=1#max_speed).")
        assert diag.code == "FIRE009"
        assert diag.severity == Severity.ERROR
        assert diag.range == Range(Position(4, 17), Position(4, 43))

    def test_relative_requirement_path(self):
        (diag,) = _diagnose("See [REQ-2](a.sysreq.md?version=1#REQ-2).")
        assert diag.code == "FIRE009"

    def test_parent_path_is_reported_once_by_the_field_rule(self):
        body = "[REQ-0](a.sysreq.md?version=1#REQ-0)"
        text = f"## R-1\n\nSIL: QM | Sec: false | Version: 1 | Parent: {body}\n"
        assert [d.code for d in diagnose_requirements(text)] == []


class TestVersionQuery:
    def test_parameter_without_version_is_an_error(self):
        (diag,) = _diagnose("See [@max_speed](/p.yaml#max_speed).")
        assert (diag.code, diag.severity) == ("FIRE010", Severity.ERROR)

    def test_requirement_without_version_is_a_warning(self):
        (diag,) = _diagnose("See [REQ-2](/a.sysreq.md#REQ-2).")
        assert (diag.code, diag.severity) == ("FIRE010", Severity.WARNING)

    def test_parent_without_version_is_a_warning(self):
        text = "## R-1\n\nSIL: QM | Sec: false | Version: 1 | Parent: [R-0](/a.sysreq.md#R-0)\n"
        assert [d.code for d in diagnose_requirements(text)] == ["FIRE010"]


class TestParameterAnchor:
    def test_text_must_match_anchor(self):
        (diag,) = _diagnose("See [@max_speed](/p.yaml?version=1#min_speed).")
        assert diag.code == "FIRE011"
        assert diag.range == Range(Position(4, 5), Position(4, 15))
        assert "min_speed" in diag.message


def _lines(body: str):
    return diagnose_requirements(_HEAD + body)


class TestReferenceStyleLinks:
    def test_valid_reference_style_links_have_no_diagnostics(self):
        body = "See [@max_speed][p] and [REQ-2][r].\n\n[p]: /params.yaml?version=1#max_speed\n[r]: /a.sysreq.md?version=1#REQ-2\n"
        assert _lines(body) == []

    def test_undefined_label_on_a_parameter_reference(self):
        (diag,) = _lines("See [@max_speed][nope].\n")
        assert (diag.code, diag.severity) == ("FIRE016", Severity.ERROR)
        assert diag.range == Range(Position(4, 17), Position(4, 21))
        assert "nope" in diag.message

    def test_undefined_label_on_a_requirement_reference(self):
        assert [d.code for d in _lines("See [REQ-2][nope].\n")] == ["FIRE016"]

    def test_implicit_label_without_definition(self):
        assert [d.code for d in _lines("See [REQ-2][].\n")] == ["FIRE016"]

    def test_plain_brackets_in_prose_are_not_flagged(self):
        assert _lines("Use array[i][j] and matrix[0][1] here.\n") == []

    def test_definition_problems_are_reported_at_the_definition(self):
        body = "See [@max_speed][p].\n\n[p]: params.yaml?version=1#max_speed\n"
        (diag,) = _lines(body)
        assert diag.code == "FIRE009"
        assert diag.range.start.line == 6

    def test_parameter_definition_without_version(self):
        body = "See [@max_speed][p].\n\n[p]: /params.yaml#max_speed\n"
        (diag,) = _lines(body)
        assert (diag.code, diag.severity) == ("FIRE010", Severity.ERROR)
        assert diag.range.start.line == 6

    def test_a_definition_shared_by_several_usages_is_reported_once(self):
        body = (
            "[@max_speed][p] and again [@max_speed][p]\n\n[p]: /params.yaml#max_speed\n"
        )
        assert [d.code for d in _lines(body)] == ["FIRE010"]

    def test_text_and_anchor_must_still_match(self):
        body = "See [@max_speed][p].\n\n[p]: /params.yaml?version=1#min_speed\n"
        (diag,) = _lines(body)
        assert diag.code == "FIRE011"
        assert diag.range.start.line == 4


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
