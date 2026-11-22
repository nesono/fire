#!/usr/bin/env python3
"""Tests for diagnostics that look at link targets on disk."""

from pathlib import Path

import pytest

from fire.lsp.diagnostic import Severity
from fire.lsp.document_parser import Position, Range
from fire.lsp.reference_diagnostics import ReferenceChecker
from fire.lsp.workspace import Workspace

_SUFFIXES = (".sysreq.md", ".swreq.md")


@pytest.fixture
def checker(tmp_path: Path) -> ReferenceChecker:
    (tmp_path / "params.yaml").write_text(
        "max_speed_v1:\n  value: 1\nmax_speed_v2:\n  value: 2\n"
    )
    (tmp_path / "other.sysreq.md").write_text(
        "## REQ-OTHER\n\nSIL: QM | Sec: false | Version: 3\n"
    )
    (tmp_path / "notes.md").write_text("# Notes\n")
    return ReferenceChecker(Workspace(tmp_path), _SUFFIXES)


def _param(version: int | str = 2, path: str = "/params.yaml", name: str = "max_speed"):
    return f"[@{name}]({path}?version={version}#{name})"


def _req(version: int = 3, path: str = "/other.sysreq.md", rid: str = "REQ-OTHER"):
    return f"[{rid}]({path}?version={version}#{rid})"


def _codes(checker, text: str) -> list[tuple[str, Severity]]:
    return [(d.code, d.severity) for d in checker.diagnose(text)]


class TestParameterReferences:
    def test_existing_parameter_version(self, checker):
        assert checker.diagnose(f"See {_param(2)}.") == []

    def test_missing_file(self, checker):
        (diag,) = checker.diagnose(f"See {_param(path='/nope.yaml')}.")
        assert diag.code == "FIRE012"
        assert diag.severity == Severity.ERROR
        assert diag.range == Range(Position(0, 17), Position(0, 47))

    def test_unknown_parameter(self, checker):
        (diag,) = checker.diagnose(f"See {_param(name='min_speed')}.")
        assert diag.code == "FIRE013"
        assert "min_speed" in diag.message

    def test_similar_name_is_not_a_match(self, checker):
        assert _codes(checker, f"{_param(name='speed')}") == [
            ("FIRE013", Severity.ERROR)
        ]

    def test_future_version_is_an_error(self, checker):
        assert _codes(checker, _param(3)) == [("FIRE014", Severity.ERROR)]

    def test_stale_version_is_a_warning(self, checker):
        assert _codes(checker, _param(1)) == [("FIRE015", Severity.WARNING)]

    def test_missing_version_query_is_left_to_syntax_rules(self, checker):
        assert checker.diagnose("[@max_speed](/params.yaml#max_speed)") == []


class TestRequirementReferences:
    def test_current_version(self, checker):
        assert checker.diagnose(f"See {_req(3)}.") == []

    def test_missing_file(self, checker):
        assert _codes(checker, _req(path="/nope.sysreq.md")) == [
            ("FIRE012", Severity.ERROR)
        ]

    def test_unknown_id(self, checker):
        (diag,) = checker.diagnose(_req(rid="REQ-MISSING"))
        assert (diag.code, diag.severity) == ("FIRE013", Severity.ERROR)

    def test_future_version_is_a_warning(self, checker):
        assert _codes(checker, _req(4)) == [("FIRE014", Severity.WARNING)]

    def test_stale_version_is_a_warning(self, checker):
        assert _codes(checker, _req(2)) == [("FIRE015", Severity.WARNING)]

    def test_plain_markdown_target_only_needs_to_exist(self, checker):
        assert checker.diagnose(_req(1, path="/notes.md")) == []

    def test_plain_markdown_target_that_is_missing(self, checker):
        assert _codes(checker, _req(1, path="/gone.md")) == [
            ("FIRE012", Severity.ERROR)
        ]

    def test_parent_links_are_checked(self, checker):
        text = f"SIL: QM | Sec: false | Version: 1 | Parent: {_req(2)}"
        assert [d.code for d in checker.diagnose(text)] == ["FIRE015"]


class TestSkippedLinks:
    @pytest.mark.parametrize(
        "link",
        [
            "[@max_speed](params.yaml?version=1#max_speed)",
            "[REQ-OTHER](other.sysreq.md?version=1#REQ-OTHER)",
            "[@config](<TODO(PARAM-789)>)",
            "[docs](https://example.com/x)",
        ],
    )
    def test_not_checked(self, checker, link):
        assert checker.diagnose(link) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
