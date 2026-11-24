#!/usr/bin/env python3
"""Tests for per-document analysis."""

import pytest

from lsprotocol import types as lsp

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


_LINK_DOC = "## R-1\n\nSIL: QM | Sec: false | Version: 1\n\n[@x](/p.yaml?version=1#x)\n"
_PARAMS = "y_v1:\n  value: 0\nx_v1:\n  value: 1\n"


class TestDefinition:
    def _workspace(self, tmp_path):
        (tmp_path / "MODULE.bazel").write_text("")
        (tmp_path / "p.yaml").write_text(_PARAMS)
        return (tmp_path / "a.sysreq.md").as_uri()

    def test_link_resolves_to_a_location(self, tmp_path):
        uri = self._workspace(tmp_path)
        location = _ANALYZER.definition(uri, _LINK_DOC, lsp.Position(4, 3))
        assert location.uri == (tmp_path / "p.yaml").as_uri()
        assert location.range.start == lsp.Position(2, 0)

    def test_unsaved_target_is_preferred(self, tmp_path):
        uri = self._workspace(tmp_path)
        overlay = {tmp_path / "p.yaml": "\n\n\nx_v1:\n"}
        location = _ANALYZER.definition(uri, _LINK_DOC, lsp.Position(4, 3), overlay)
        assert location.range.start == lsp.Position(3, 0)

    def test_cursor_position_is_converted_from_utf16(self, tmp_path):
        uri = self._workspace(tmp_path)
        text = _LINK_DOC.replace("[@x]", "😀 [@x]")
        assert _ANALYZER.definition(uri, text, lsp.Position(4, 4)) is not None
        assert _ANALYZER.definition(uri, text, lsp.Position(4, 1)) is None

    def test_cursor_off_a_link(self, tmp_path):
        uri = self._workspace(tmp_path)
        assert _ANALYZER.definition(uri, _LINK_DOC, lsp.Position(0, 1)) is None

    def test_other_document_types_are_ignored(self, tmp_path):
        self._workspace(tmp_path)
        uri = (tmp_path / "README.md").as_uri()
        assert _ANALYZER.definition(uri, _LINK_DOC, lsp.Position(4, 3)) is None

    def test_no_workspace_means_no_definition(self):
        uri = "file:///nowhere/a.sysreq.md"
        assert _ANALYZER.definition(uri, _LINK_DOC, lsp.Position(4, 3)) is None


class TestDocumentSymbols:
    def test_requirement_file(self):
        text = "## REQ-1\n\nSIL: QM | Sec: false | Version: 1\n"
        (symbol,) = _ANALYZER.document_symbols("file:///a/x.sysreq.md", text)
        assert symbol.name == "REQ-1"
        assert symbol.kind == lsp.SymbolKind.Key
        assert symbol.selection_range.start == lsp.Position(0, 3)

    def test_parameter_file(self):
        names = [
            s.name for s in _ANALYZER.document_symbols("file:///a/p.yaml", _PARAMS)
        ]
        assert names == ["y_v1", "x_v1"]

    def test_other_documents_have_no_symbols(self):
        assert _ANALYZER.document_symbols("file:///a/README.md", "## R-1\n") == []

    def test_columns_are_utf16(self):
        text = "## REQ-1\n\nSIL: QM | Sec: false | Version: 1\n\n😀 text\n"
        (symbol,) = _ANALYZER.document_symbols("file:///a/x.sysreq.md", text)
        assert symbol.range.end == lsp.Position(4, 7)


class TestWorkspaceSymbols:
    def _workspace(self, tmp_path):
        (tmp_path / "MODULE.bazel").write_text("")
        (tmp_path / "reqs").mkdir()
        (tmp_path / "reqs" / "a.sysreq.md").write_text("## REQ-BRK-1\n\n## REQ-VEL-1\n")
        (tmp_path / "params.yaml").write_text("max_speed_v1:\n  value: 1\n")
        return tmp_path

    def _names(self, symbols):
        return [s.name for s in symbols]

    def test_query_across_requirements_and_parameters(self, tmp_path):
        root = self._workspace(tmp_path)
        assert self._names(_ANALYZER.workspace_symbols("brk", [root])) == ["REQ-BRK-1"]
        assert self._names(_ANALYZER.workspace_symbols("speed", [root])) == [
            "max_speed_v1"
        ]

    def test_symbol_shape(self, tmp_path):
        root = self._workspace(tmp_path)
        (symbol,) = _ANALYZER.workspace_symbols("vel", [root])
        assert symbol.kind == lsp.SymbolKind.Key
        assert symbol.container_name == "reqs/a.sysreq.md"
        assert symbol.location.uri == (root / "reqs" / "a.sysreq.md").as_uri()
        assert symbol.location.range.start == lsp.Position(2, 3)

    def test_root_is_found_from_a_file_inside_the_workspace(self, tmp_path):
        root = self._workspace(tmp_path)
        start = root / "reqs" / "a.sysreq.md"
        assert self._names(_ANALYZER.workspace_symbols("brk", [start])) == ["REQ-BRK-1"]

    def test_folder_without_a_marker_is_its_own_root(self, tmp_path):
        (tmp_path / "x.sysreq.md").write_text("## REQ-X\n")
        assert self._names(_ANALYZER.workspace_symbols("", [tmp_path])) == ["REQ-X"]

    def test_the_same_workspace_is_not_listed_twice(self, tmp_path):
        root = self._workspace(tmp_path)
        starts = [root, root / "reqs" / "a.sysreq.md"]
        assert self._names(_ANALYZER.workspace_symbols("brk", starts)) == ["REQ-BRK-1"]

    def test_unsaved_documents_are_searchable(self, tmp_path):
        root = self._workspace(tmp_path)
        overlay = {root / "new.sysreq.md": "## REQ-NEW-1\n"}
        assert self._names(_ANALYZER.workspace_symbols("new", [root], overlay)) == [
            "REQ-NEW-1"
        ]

    def test_no_workspace_means_no_symbols(self):
        assert _ANALYZER.workspace_symbols("x", []) == []


_REQS = "## REQ-A\n\nSIL: QM | Sec: false | Version: 3\n"
_LINKER = (
    "## REQ-B\n\nSIL: QM | Sec: false | Version: 1\n\n"
    "See [REQ-A](/reqs.sysreq.md?version=3#REQ-A) and [@x](/p.yaml?version=2#x).\n"
)


class TestReferences:
    def _workspace(self, tmp_path):
        (tmp_path / "MODULE.bazel").write_text("")
        (tmp_path / "reqs.sysreq.md").write_text(_REQS)
        (tmp_path / "linker.sysreq.md").write_text(_LINKER)
        (tmp_path / "p.yaml").write_text("x_v1:\n  value: 1\nx_v2:\n  value: 2\n")
        return tmp_path

    def _refs(self, root, name, text, line, character, declaration=False, overlay=None):
        uri = (root / name).as_uri()
        position = lsp.Position(line, character)
        return _ANALYZER.references(uri, text, position, declaration, overlay)

    def test_from_a_requirement_heading(self, tmp_path):
        root = self._workspace(tmp_path)
        (location,) = self._refs(root, "reqs.sysreq.md", _REQS, 0, 5)
        assert location.uri == (root / "linker.sysreq.md").as_uri()
        assert location.range == lsp.Range(lsp.Position(4, 4), lsp.Position(4, 44))

    def test_from_a_parameter_key(self, tmp_path):
        root = self._workspace(tmp_path)
        text = (root / "p.yaml").read_text()
        (location,) = self._refs(root, "p.yaml", text, 2, 1)
        assert location.uri == (root / "linker.sysreq.md").as_uri()
        assert location.range.start == lsp.Position(4, 49)

    def test_from_a_link(self, tmp_path):
        root = self._workspace(tmp_path)
        (location,) = self._refs(root, "linker.sysreq.md", _LINKER, 4, 10)
        assert location.uri == (root / "linker.sysreq.md").as_uri()

    def test_declaration_comes_first_when_requested(self, tmp_path):
        root = self._workspace(tmp_path)
        first, second = self._refs(root, "reqs.sysreq.md", _REQS, 0, 5, True)
        assert first.uri == (root / "reqs.sysreq.md").as_uri()
        assert first.range == lsp.Range(lsp.Position(0, 3), lsp.Position(0, 8))
        assert second.uri == (root / "linker.sysreq.md").as_uri()

    def test_parameter_declaration_is_the_key_at_the_cursor_version(self, tmp_path):
        root = self._workspace(tmp_path)
        text = (root / "p.yaml").read_text()
        first, _ = self._refs(root, "p.yaml", text, 2, 1, True)
        assert first.range.start == lsp.Position(2, 0)

    def test_unsaved_documents_count(self, tmp_path):
        root = self._workspace(tmp_path)
        extra = "[REQ-A](/reqs.sysreq.md?version=3#REQ-A)\n"
        overlay = {root / "new.sysreq.md": extra}
        refs = self._refs(root, "reqs.sysreq.md", _REQS, 0, 5, overlay=overlay)
        assert {r.uri for r in refs} == {
            (root / "linker.sysreq.md").as_uri(),
            (root / "new.sysreq.md").as_uri(),
        }

    def test_unsaved_edit_removes_a_reference(self, tmp_path):
        root = self._workspace(tmp_path)
        overlay = {root / "linker.sysreq.md": "no links any more\n"}
        assert self._refs(root, "reqs.sysreq.md", _REQS, 0, 5, overlay=overlay) == []

    def test_cursor_on_plain_text(self, tmp_path):
        root = self._workspace(tmp_path)
        assert self._refs(root, "reqs.sysreq.md", _REQS, 2, 1) == []

    def test_other_documents_have_no_references(self, tmp_path):
        root = self._workspace(tmp_path)
        assert self._refs(root, "README.md", _REQS, 0, 5) == []

    def test_no_workspace(self):
        uri = "file:///nowhere/a.sysreq.md"
        assert _ANALYZER.references(uri, _REQS, lsp.Position(0, 5), False) == []


_MISSING_UNIT = "max_speed_v1:\n  value: 30.0\n  description: Maximum speed\n"


class TestParameterFiles:
    def test_missing_unit_is_reported(self):
        (diag,) = _ANALYZER.diagnose("file:///a/params.yaml", _MISSING_UNIT)
        assert diag.code == "FIRE018"
        assert diag.severity == lsp.DiagnosticSeverity.Error
        assert diag.range.start == lsp.Position(0, 0)
        assert "unit" in diag.message

    def test_syntax_error_is_reported(self):
        (diag,) = _ANALYZER.diagnose("file:///a/params.yaml", "a_v1:\n  value: [1, 2\n")
        assert diag.code == "FIRE017"

    def test_valid_parameter_file(self):
        text = "a_v1:\n  value: 1\n  unit: m\n  description: d\n"
        assert _ANALYZER.diagnose("file:///a/params.yaml", text) == []

    def test_other_yaml_files_are_ignored(self):
        text = "name: ci\non: push\njobs: {}\n"
        assert _ANALYZER.diagnose("file:///a/.github/ci.yaml", text) == []

    def test_columns_are_utf16(self):
        line = 'a_v1: {value: "😀", unit: m, description: d, extra: 1}'
        (diag,) = _ANALYZER.diagnose("file:///a/params.yaml", line + "\n")
        assert diag.range.start.character == line.index("extra") + 1

    def test_yaml_documents_do_not_need_a_workspace(self, tmp_path):
        uri = (tmp_path / "params.yaml").as_uri()
        assert [d.code for d in _ANALYZER.diagnose(uri, _MISSING_UNIT)] == ["FIRE018"]


class TestCompletions:
    _URI = "file:///a/x.sysreq.md"

    def _items(self, marked: str, uri: str = _URI):
        before, _, after = marked.partition("§")
        line = before.count("\n")
        # LSP columns count UTF-16 units
        character = len(before[before.rfind("\n") + 1 :].encode("utf-16-le")) // 2
        return _ANALYZER.completions(uri, before + after, lsp.Position(line, character))

    def test_metadata_keys_with_a_text_edit(self):
        items = self._items("## R-1\n\nSI§\n")
        sil = items[0]
        assert (sil.label, sil.kind) == ("SIL", lsp.CompletionItemKind.Property)
        assert sil.text_edit.new_text == "SIL: "
        assert sil.text_edit.range == lsp.Range(lsp.Position(2, 0), lsp.Position(2, 2))
        assert sil.insert_text_format == lsp.InsertTextFormat.PlainText
        assert sil.detail == "required"

    def test_enum_values_and_the_todo_snippet(self):
        items = self._items("## R-1\n\nSIL: §\n")
        assert items[0].label == "ASIL-A"
        todo = items[-1]
        assert todo.insert_text_format == lsp.InsertTextFormat.Snippet
        assert todo.text_edit.new_text.startswith("TODO(")

    def test_range_columns_are_utf16(self):
        items = self._items("## R-1\n\nSIL: 😀 | §\n")
        # the emoji is one code point but two UTF-16 units
        assert items[0].text_edit.range.start.character == len("SIL: 😀 | ") + 1

    def test_document_type_decides_the_fields(self):
        items = self._items("## R-1\n\n§\n", "file:///a/x.regreq.md")
        assert [i.detail for i in items][0] == "required"
        assert items[0].label == "Version"

    def test_other_documents_get_no_completions(self):
        assert self._items("## R-1\n\n§\n", "file:///a/README.md") == []

    def test_outside_the_metadata_line(self):
        assert (
            self._items("## R-1\n\nSIL: QM | Sec: false | Version: 1\n\nText §\n") == []
        )


class TestLinkCompletions:
    def _workspace(self, tmp_path):
        (tmp_path / "MODULE.bazel").write_text("")
        (tmp_path / "reqs.sysreq.md").write_text("## REQ-A\n\nVersion: 3\n")
        (tmp_path / "params.yaml").write_text(
            "max_speed_v1:\n  value: 1\nmax_speed_v2:\n  value: 2\n"
        )
        return tmp_path

    def _items(self, root, marked: str, overlay=None):
        before, _, after = marked.partition("§")
        line = before.count("\n")
        character = len(before[before.rfind("\n") + 1 :].encode("utf-16-le")) // 2
        uri = (root / "doc.sysreq.md").as_uri()
        position = lsp.Position(line, character)
        return _ANALYZER.completions(uri, before + after, position, overlay)

    def test_workspace_files_after_the_opening_parenthesis(self, tmp_path):
        root = self._workspace(tmp_path)
        items = self._items(root, "See [@max_speed](§")
        assert [i.label for i in items] == ["/params.yaml", "/reqs.sysreq.md"]
        assert items[0].kind == lsp.CompletionItemKind.File

    def test_unsaved_files_are_offered(self, tmp_path):
        root = self._workspace(tmp_path)
        overlay = {root / "draft.sysreq.md": "## REQ-D\n\nVersion: 1\n"}
        labels = [i.label for i in self._items(root, "[x](§", overlay)]
        assert "/draft.sysreq.md" in labels

    def test_versions_of_a_parameter(self, tmp_path):
        root = self._workspace(tmp_path)
        items = self._items(root, "[@max_speed](/params.yaml?version=§")
        assert [i.label for i in items] == ["2", "1"]

    def test_unsaved_target_decides_the_version(self, tmp_path):
        root = self._workspace(tmp_path)
        overlay = {root / "reqs.sysreq.md": "## REQ-A\n\nVersion: 9\n"}
        items = self._items(root, "[REQ-A](/reqs.sysreq.md?version=§", overlay)
        assert [i.label for i in items] == ["9"]

    def test_anchors_of_a_requirement_file(self, tmp_path):
        root = self._workspace(tmp_path)
        items = self._items(root, "[x](/reqs.sysreq.md?version=3#§")
        assert [i.label for i in items] == ["REQ-A"]

    def test_columns_are_utf16(self, tmp_path):
        root = self._workspace(tmp_path)
        items = self._items(root, "😀 [x](/re§")
        start = items[0].text_edit.range.start.character
        assert start == len("😀 [x](") + 1

    def test_without_a_workspace_only_metadata_is_completed(self):
        uri = "file:///nowhere/a.sysreq.md"
        items = _ANALYZER.completions(uri, "[x](/", lsp.Position(0, 5))
        assert items == []


class TestLinkInsertion:
    def _workspace(self, tmp_path):
        (tmp_path / "MODULE.bazel").write_text("")
        (tmp_path / "reqs.sysreq.md").write_text("## REQ-A\n\nVersion: 3\n")
        (tmp_path / "params.yaml").write_text(
            "max_speed_v1:\n  value: 1\nmax_speed_v2:\n  value: 2\n"
        )
        return tmp_path

    def _items(self, root, marked: str, overlay=None):
        before, _, after = marked.partition("§")
        line = before.count("\n")
        character = len(before[before.rfind("\n") + 1 :].encode("utf-16-le")) // 2
        uri = (root / "doc.sysreq.md").as_uri()
        return _ANALYZER.completions(
            uri, before + after, lsp.Position(line, character), overlay
        )

    def test_parameter_link_is_inserted(self, tmp_path):
        root = self._workspace(tmp_path)
        (item,) = self._items(root, "See [@ma§")
        assert item.label == "@max_speed"
        assert (
            item.text_edit.new_text == "[@max_speed](/params.yaml?version=2#max_speed)"
        )
        assert item.filter_text == "[@max_speed"

    def test_requirement_link_is_inserted(self, tmp_path):
        root = self._workspace(tmp_path)
        (item,) = self._items(root, "See [REQ§")
        assert item.text_edit.new_text == "[REQ-A](/reqs.sysreq.md?version=3#REQ-A)"

    def test_unsaved_documents_decide_the_version(self, tmp_path):
        root = self._workspace(tmp_path)
        overlay = {root / "reqs.sysreq.md": "## REQ-A\n\nVersion: 9\n"}
        (item,) = self._items(root, "[REQ§", overlay)
        assert "version=9" in item.text_edit.new_text

    def test_columns_are_utf16(self, tmp_path):
        root = self._workspace(tmp_path)
        (item,) = self._items(root, "😀 [@§")
        assert item.text_edit.range.start.character == len("😀 ") + 1

    def test_without_a_workspace_nothing_is_inserted(self):
        uri = "file:///nowhere/a.sysreq.md"
        assert _ANALYZER.completions(uri, "[@", lsp.Position(0, 2)) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
