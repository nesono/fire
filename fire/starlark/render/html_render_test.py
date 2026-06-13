#!/usr/bin/env python3
"""Tests for rendering the PDF render model to HTML via the default template."""

import pytest

from fire.starlark.render.document_model import build_render_document
from fire.starlark.render.html_render import render_html

_SYSREQ = """\
# Braking System Requirements

## REQ-BRK-001

Sil: ASIL-D | Sec: true | Version: 1

The brake shall engage within 100 ms.
"""


@pytest.fixture()
def document(default_config):
    return build_render_document(_SYSREQ, "brake.sysreq.md", default_config)


class TestStructure:
    def test_doctype_declaration(self, document):
        assert render_html(document).lstrip().startswith("<!DOCTYPE html>")

    def test_title_in_head(self, document):
        assert "<title>Braking System Requirements</title>" in render_html(document)

    def test_cover_shows_display_name(self, document):
        assert "System Requirement" in render_html(document)


class TestEntryContract:
    def test_entry_section_carries_doc_type(self, document):
        html = render_html(document)
        assert '<section class="fire-entry" data-doc-type="sysreq">' in html

    def test_entry_id_heading(self, document):
        assert '<h2 class="fire-entry__id">REQ-BRK-001</h2>' in render_html(document)

    def test_field_class_and_data_value(self, document):
        html = render_html(document)
        assert 'class="fire-field fire-field--sil"' in html
        assert 'data-value="ASIL-D"' in html

    def test_field_term_and_definition(self, document):
        html = render_html(document)
        assert "<dt>SIL</dt>" in html
        assert "<dd>ASIL-D</dd>" in html

    def test_body_rendered_as_html(self, document):
        html = render_html(document)
        assert (
            '<div class="fire-entry__body"><p>The brake shall engage'
            " within 100 ms.</p></div>" in html
        )


class TestTemplateOverride:
    def test_custom_template_path_is_used(self, document, tmp_path):
        custom = tmp_path / "minimal.html.j2"
        custom.write_text("<h1>{{ document.title }}</h1>\n")
        html = render_html(document, template_name=str(custom))
        assert html.strip() == "<h1>Braking System Requirements</h1>"

    def test_builtin_template_name_still_resolves(self, document):
        assert "fire-entry" in render_html(document, template_name="document.html.j2")


class TestStylesheets:
    def test_base_stylesheet_inlined(self, document):
        assert ".fire-entry" in render_html(document)

    def test_user_stylesheet_cascades_after_base(self, document, tmp_path):
        override = tmp_path / "corporate.css"
        override.write_text(".fire-cover__title { color: rebeccapurple; }\n")
        html = render_html(document, stylesheets=[str(override)])
        assert "rebeccapurple" in html
        assert html.index(".fire-entry") < html.index("rebeccapurple")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
