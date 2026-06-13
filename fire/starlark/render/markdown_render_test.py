#!/usr/bin/env python3
"""Tests for converting FIRE markdown bodies to HTML fragments."""

import pytest

from fire.starlark.render.markdown_render import render_markdown


class TestRenderMarkdown:
    def test_blank_input_renders_empty(self):
        assert render_markdown("") == ""

    def test_paragraph(self):
        assert render_markdown("The brake shall engage.") == (
            "<p>The brake shall engage.</p>"
        )

    def test_inline_link(self):
        html = render_markdown("See [REQ-SYS-001](/sys.sysreq.md?version=1).")
        assert '<a href="/sys.sysreq.md?version=1">REQ-SYS-001</a>' in html

    def test_table(self):
        html = render_markdown("| A | B |\n| - | - |\n| 1 | 2 |")
        assert "<table>" in html
        assert "<th>A</th>" in html
        assert "<td>1</td>" in html

    def test_fenced_code(self):
        html = render_markdown("```\nx = 1\n```")
        assert "<pre><code>" in html
        assert "x = 1" in html

    def test_bullet_list(self):
        html = render_markdown("- one\n- two")
        assert "<ul>" in html
        assert "<li>one</li>" in html


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
