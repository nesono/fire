#!/usr/bin/env python3
"""Tests for quick fixes, applied end to end through the analyzer."""

import pytest

from lsprotocol import types as lsp

from fire.lsp.analysis import Analyzer
from fire.starlark.config_models import load_config

_ANALYZER = Analyzer(load_config())
_HEADER = "## REQ-A\n\nSIL: QM | Sec: false | Version: 1\n\n"
_PARAMS = "speed_v1:\n  value: 1\n  unit: m\n  description: d\nspeed_v2:\n  value: 2\n  unit: m\n  description: d\n"
_TARGET = "## REQ-B\n\nSIL: QM | Sec: false | Version: 4\n"


@pytest.fixture()
def doc(tmp_path):
    (tmp_path / "MODULE.bazel").write_text("")
    (tmp_path / "p.yaml").write_text(_PARAMS)
    (tmp_path / "t.sysreq.md").write_text(_TARGET)
    return tmp_path / "a.sysreq.md"


def _selection(line: int = 0, character: int = 0, end_line: int | None = None):
    end = lsp.Position(line if end_line is None else end_line, 10_000)
    return lsp.Range(lsp.Position(line, character), end)


def _whole(text: str) -> lsp.Range:
    lines = text.split("\n")
    return lsp.Range(lsp.Position(0, 0), lsp.Position(len(lines), 0))


def _utf16_offset(line: str, column: int) -> int:
    units = 0
    for index, char in enumerate(line):
        if units >= column:
            return index
        units += 2 if ord(char) > 0xFFFF else 1
    return len(line)


def _apply(text: str, edits: list[lsp.TextEdit]) -> str:
    lines = text.split("\n")
    for edit in sorted(
        edits,
        key=lambda e: (e.range.start.line, -e.range.start.character),
        reverse=True,
    ):
        line = lines[edit.range.start.line]
        start = _utf16_offset(line, edit.range.start.character)
        end = _utf16_offset(line, edit.range.end.character)
        lines[edit.range.start.line] = line[:start] + edit.new_text + line[end:]
    return "\n".join(lines)


def _fix(doc, text: str, title_start: str, selection: lsp.Range | None = None) -> str:
    uri = doc.as_uri()
    actions = _ANALYZER.code_actions(uri, text, selection or _whole(text))
    (action,) = [a for a in actions if a.title.startswith(title_start)]
    return _apply(text, action.edit.changes[uri])


def _codes(doc, text: str) -> list[str]:
    return [d.code for d in _ANALYZER.diagnose(doc.as_uri(), text)]


class TestStaleVersion:
    def test_bump_one_link(self, doc):
        text = _HEADER + "[@speed](/p.yaml?version=1#speed)\n"
        assert _codes(doc, text) == ["FIRE015"]
        fixed = _fix(doc, text, "Update link to version 2")
        assert fixed.endswith("[@speed](/p.yaml?version=2#speed)\n")
        assert _codes(doc, fixed) == []

    def test_bump_requirement_link(self, doc):
        text = _HEADER + "[REQ-B](/t.sysreq.md?version=2#REQ-B)\n"
        fixed = _fix(doc, text, "Update link to version 4")
        assert "?version=4#REQ-B" in fixed
        assert _codes(doc, fixed) == []

    def test_cursor_anywhere_on_the_line_is_enough(self, doc):
        text = _HEADER + "TODO fix this later\n"
        selection = _selection(4, 15)
        (action,) = _ANALYZER.code_actions(doc.as_uri(), text, selection)
        assert action.title == "Replace with TODO(KEY-1234)"

    def test_only_links_at_the_cursor_are_offered(self, doc):
        text = _HEADER + "[@speed](/p.yaml?version=1#speed)\n\nPlain.\n"
        assert _ANALYZER.code_actions(doc.as_uri(), text, _selection(7)) == []

    def test_bump_all_in_file(self, doc):
        link = "[@speed](/p.yaml?version=1#speed)"
        text = _HEADER + f"{link} and {link}\n[REQ-B](/t.sysreq.md?version=2#REQ-B)\n"
        fixed = _fix(doc, text, "Update all 3")
        assert _codes(doc, fixed) == []

    def test_reference_style_definition_is_updated(self, doc):
        text = _HEADER + "[@speed][1]\n\n[1]: /p.yaml?version=1#speed\n"
        fixed = _fix(doc, text, "Update link")
        assert fixed.endswith("[1]: /p.yaml?version=2#speed\n")
        assert _codes(doc, fixed) == []

    def test_columns_after_non_ascii_text_are_utf16(self, doc):
        text = _HEADER + "😀 [@speed](/p.yaml?version=1#speed)\n"
        fixed = _fix(doc, text, "Update link")
        assert "😀 [@speed](/p.yaml?version=2#speed)" in fixed

    def test_future_version_has_no_action(self, doc):
        text = _HEADER + "[@speed](/p.yaml?version=3#speed)\n"
        assert _ANALYZER.code_actions(doc.as_uri(), text, _whole(text)) == []


class TestMissingVersion:
    def test_parameter_link(self, doc):
        text = _HEADER + "[@speed](/p.yaml#speed)\n"
        assert "FIRE010" in _codes(doc, text)
        fixed = _fix(doc, text, "Add ?version=2")
        assert fixed.endswith("[@speed](/p.yaml?version=2#speed)\n")
        assert _codes(doc, fixed) == []

    def test_requirement_link_without_anchor_query(self, doc):
        text = _HEADER + "[REQ-B](/t.sysreq.md#REQ-B)\n"
        fixed = _fix(doc, text, "Add ?version=4")
        assert fixed.endswith("[REQ-B](/t.sysreq.md?version=4#REQ-B)\n")

    def test_unresolvable_target_has_no_action(self, doc):
        text = _HEADER + "[@speed](/gone.yaml#speed)\n"
        assert _ANALYZER.code_actions(doc.as_uri(), text, _whole(text)) == []


class TestBareTodo:
    def test_replaced_with_template(self, doc):
        text = _HEADER + "TODO fix this\n"
        assert "FIRE004" in _codes(doc, text)
        fixed = _fix(doc, text, "Replace with TODO(KEY-1234)")
        assert "TODO(KEY-1234) fix this" in fixed
        assert _codes(doc, fixed) == []


class TestMetadata:
    def test_missing_metadata_line_gets_a_skeleton(self, doc):
        text = "## REQ-A\n\nJust text.\n"
        assert _codes(doc, text) == ["FIRE003"]
        fixed = _fix(doc, text, "Insert metadata line")
        assert fixed.startswith(
            "## REQ-A\n\nSIL: TODO(KEY-1234) | Sec: TODO(KEY-1234) | Version: 1\n"
        )
        assert _codes(doc, fixed) == []

    def test_missing_required_field_is_added_to_the_metadata_line(self, doc):
        text = "## REQ-A\n\nSIL: QM | Version: 1\n"
        assert _codes(doc, text) == ["FIRE006"]
        fixed = _fix(doc, text, "Add Sec: TODO(KEY-1234)")
        assert "SIL: QM | Version: 1 | Sec: TODO(KEY-1234)\n" in fixed
        assert _codes(doc, fixed) == []

    def test_missing_version_is_added_as_one(self, doc):
        text = "## REQ-A\n\nSIL: QM | Sec: false\n"
        fixed = _fix(doc, text, "Add Version: 1")
        assert "Sec: false | Version: 1\n" in fixed
        assert _codes(doc, fixed) == []

    def test_invalid_enum_value_offers_the_valid_ones(self, doc):
        text = "## REQ-A\n\nSIL: ASIL-Z | Sec: false | Version: 1\n"
        assert _codes(doc, text) == ["FIRE005"]
        fixed = _fix(doc, text, "Change SIL to QM")
        assert "SIL: QM | Sec" in fixed
        assert _codes(doc, fixed) == []

    def test_every_enum_value_is_offered(self, doc):
        text = "## REQ-A\n\nSIL: ASIL-Z | Sec: false | Version: 1\n"
        actions = _ANALYZER.code_actions(doc.as_uri(), text, _whole(text))
        titles = {a.title for a in actions}
        assert {"Change SIL to ASIL-A", "Change SIL to PL-e"} <= titles

    def test_quoted_bool_is_replaced(self, doc):
        text = '## REQ-A\n\nSIL: QM | Sec: "true" | Version: 1\n'
        fixed = _fix(doc, text, "Change Sec to true")
        assert "Sec: true | Version" in fixed
        assert _codes(doc, fixed) == []

    def test_invalid_version_has_no_value_to_offer(self, doc):
        text = "## REQ-A\n\nSIL: QM | Sec: false | Version: 0\n"
        assert _ANALYZER.code_actions(doc.as_uri(), text, _whole(text)) == []

    def test_regreq_skeleton_uses_its_own_required_fields(self, tmp_path):
        (tmp_path / "MODULE.bazel").write_text("")
        path = tmp_path / "a.regreq.md"
        text = "## REQ-A\n\nText.\n"
        actions = _ANALYZER.code_actions(path.as_uri(), text, _whole(text))
        (edit,) = actions[0].edit.changes[path.as_uri()]
        assert edit.new_text == "\n\nVersion: 1"


class TestIgnoredDocuments:
    def test_unknown_suffix(self, tmp_path):
        uri = (tmp_path / "README.md").as_uri()
        assert _ANALYZER.code_actions(uri, "TODO x\n", _whole("TODO x\n")) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
