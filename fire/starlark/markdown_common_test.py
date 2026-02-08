"""Tests for fire/starlark/markdown_common.py"""

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
        assert refs == []  # Underscores not allowed, only hyphens

    def test_requirement_must_end_with_md(self):
        text = "[REQ-001](design.txt)"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == []

    def test_requirement_with_path(self):
        text = "[REQ-001](path/to/design.md)"
        refs = markdown_common.extract_requirement_references(text)
        assert refs == [("REQ-001", "path/to/design.md")]
