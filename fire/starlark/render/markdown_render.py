#!/usr/bin/env python3
"""Convert a FIRE markdown body fragment to an HTML fragment.

The render model (Phase 1) carries each entry's body as raw markdown. The
HTML template (Phase 2) embeds that body as HTML, so this module performs the
markdown→HTML conversion for paragraphs, inline references/links, tables, and
fenced code blocks.
"""

from __future__ import annotations

from markdown_it import MarkdownIt

_RENDERER = MarkdownIt("commonmark").enable("table")


def render_markdown(text: str) -> str:
    """Render a markdown *text* fragment to an HTML fragment.

    Returns an empty string for blank input so callers can emit an empty body
    without a stray ``<p>`` wrapper.
    """
    return _RENDERER.render(text).strip()
