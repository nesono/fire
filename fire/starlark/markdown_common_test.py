"""Tests for fire/starlark/markdown_common.py"""

import sys

import pytest

from fire.starlark import markdown_common


class TestExtractMarkdownLinks:
    """Tests for extract_markdown_links function."""

    def test_single_link(self):
        text = "Check [this link](http://example.com) out"
        links = markdown_common.extract_markdown_links(text)
        assert links == [("this link", "http://example.com")]

    def test_multiple_links(self):
        text = "[First](url1) and [Second](url2)"
        links = markdown_common.extract_markdown_links(text)
        assert links == [("First", "url1"), ("Second", "url2")]

    def test_no_links(self):
        text = "No links here"
        links = markdown_common.extract_markdown_links(text)
        assert links == []

    def test_link_with_special_chars(self):
        text = "[Link!@#](http://example.com/path?query=1#anchor)"
        links = markdown_common.extract_markdown_links(text)
        assert links == [("Link!@#", "http://example.com/path?query=1#anchor")]


class TestExtractParamReferences:
    """Tests for extract_param_references function."""

    def test_single_param_reference(self):
        text = "The [@velocity](params.yaml) parameter"
        refs = markdown_common.extract_param_references(text)
        assert refs == [("velocity", "params.yaml")]

    def test_multiple_param_references(self):
        text = "[@velocity](p1.yaml) and [@acceleration](p2.yaml)"
        refs = markdown_common.extract_param_references(text)
        assert refs == [("velocity", "p1.yaml"), ("acceleration", "p2.yaml")]

    def test_param_with_version_query(self):
        text = "[@max_speed](params.yaml?version=2)"
        refs = markdown_common.extract_param_references(text)
        assert refs == [("max_speed", "params.yaml?version=2")]

    def test_no_param_references(self):
        text = "No parameter references"
        refs = markdown_common.extract_param_references(text)
        assert refs == []

    def test_param_with_underscores(self):
        text = "[@max_vehicle_velocity](params.yaml)"
        refs = markdown_common.extract_param_references(text)
        assert refs == [("max_vehicle_velocity", "params.yaml")]

    def test_param_with_numbers(self):
        text = "[@param123](file.yaml)"
        refs = markdown_common.extract_param_references(text)
        assert refs == [("param123", "file.yaml")]

    def test_param_cannot_start_with_number(self):
        text = "[@123param](file.yaml)"
        refs = markdown_common.extract_param_references(text)
        assert refs == []


class TestExtractRequirementReferences:
    """Tests for extract_requirement_references function."""

    def test_single_requirement_reference(self):
        text = "See [REQ-001](design.md) for details"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == [("REQ-001", "design.md")]

    def test_multiple_requirement_references(self):
        text = "[REQ-001](d1.md) and [REQ-ABC-123](d2.md)"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == [("REQ-001", "d1.md"), ("REQ-ABC-123", "d2.md")]

    def test_requirement_with_anchor(self):
        text = "[REQ-001](design.md#section)"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == [("REQ-001", "design.md#section")]

    def test_no_requirement_references(self):
        text = "No requirements here"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == []

    def test_lowercase_not_matched(self):
        text = "[req-001](design.md)"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == []

    def test_requirement_with_underscores(self):
        text = "[REQ_SYS_001](design.md)"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == [("REQ_SYS_001", "design.md")]  # Underscores are allowed

    def test_requirement_must_end_with_md(self):
        text = "[REQ-001](design.txt)"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == []

    def test_requirement_with_path(self):
        text = "[REQ-001](path/to/design.md)"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == [("REQ-001", "path/to/design.md")]


class TestExtractLinkDefinitions:
    """Tests for extract_link_definitions function."""

    def test_single_numbered_definition(self):
        text = "[1]: http://example.com"
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {"1": "http://example.com"}

    def test_single_named_definition(self):
        text = "[ref]: /path/to/file.md"
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {"ref": "/path/to/file.md"}

    def test_multiple_definitions(self):
        text = "[1]: http://example.com\n[2]: /path/file.md"
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {"1": "http://example.com", "2": "/path/file.md"}

    def test_empty_text(self):
        text = ""
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {}

    def test_no_definitions(self):
        text = "Just some text with [inline](link.md) but no definitions"
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {}

    def test_definition_with_extra_whitespace(self):
        text = "[1]:   http://example.com   "
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {"1": "http://example.com"}

    def test_duplicate_labels_last_wins(self):
        text = "[1]: first.md\n[1]: second.md"
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {"1": "second.md"}

    def test_complex_url_with_query_and_anchor(self):
        text = "[ref]: /path/file.md?version=2#section"
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {"ref": "/path/file.md?version=2#section"}

    def test_definition_must_be_at_line_start(self):
        text = "    [1]: http://example.com"
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {}

    def test_mixed_content(self):
        text = """Some text here
[1]: http://example.com
More text
[ref]: /path/file.md
Even more text"""
        defs = markdown_common.extract_link_definitions(text)
        assert defs == {"1": "http://example.com", "ref": "/path/file.md"}


class TestExtractReferenceStyleLinks:
    """Tests for extract_reference_style_links function."""

    def test_explicit_reference(self):
        text = "See [this link][1] for details"
        links = markdown_common.extract_reference_style_links(text)
        assert ("this link", "1") in links

    def test_implicit_reference(self):
        text = "See [REQ-001][] for details"
        links = markdown_common.extract_reference_style_links(text)
        assert ("REQ-001", "REQ-001") in links

    def test_shortcut_reference(self):
        text = "See [REQ-001] for details"
        links = markdown_common.extract_reference_style_links(text)
        assert ("REQ-001", "REQ-001") in links

    def test_multiple_mixed_references(self):
        text = "[First][1] and [Second][] and [Third]"
        links = markdown_common.extract_reference_style_links(text)
        assert ("First", "1") in links
        assert ("Second", "Second") in links
        assert ("Third", "Third") in links

    def test_no_reference_style_links(self):
        text = "Just [inline](url.md) links here"
        links = markdown_common.extract_reference_style_links(text)
        assert links == []

    def test_does_not_match_inline_links(self):
        text = "[Text](http://example.com)"
        links = markdown_common.extract_reference_style_links(text)
        assert links == []

    def test_does_not_match_link_definitions(self):
        text = "[1]: http://example.com"
        links = markdown_common.extract_reference_style_links(text)
        assert links == []

    def test_parameter_reference_format(self):
        text = "See [@velocity][1] parameter"
        links = markdown_common.extract_reference_style_links(text)
        assert ("@velocity", "1") in links

    def test_mixed_with_inline_links(self):
        text = "[Ref][1] and [Inline](url.md) and [Short]"
        links = markdown_common.extract_reference_style_links(text)
        assert ("Ref", "1") in links
        assert ("Short", "Short") in links
        assert not any(link_text == "Inline" for link_text, _ in links)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
