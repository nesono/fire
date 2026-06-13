#!/usr/bin/env python3
"""Render the PDF render model to HTML using a Jinja2 template.

The template defines the stable HTML class contract documented in the PDF
export design: ``fire-entry``/``fire-field`` classes plus ``data-doc-type`` and
``data-value`` hooks that user stylesheets target. The FIRE-shipped ``base.css``
is inlined first and any user stylesheets are inlined after it, so the CSS
cascade lets users override the defaults without a full rewrite.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from fire.starlark.render.document_model import RenderDocument
from fire.starlark.render.markdown_render import render_markdown

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_BASE_CSS = Path(__file__).parent / "styles" / "base.css"
_DEFAULT_TEMPLATE = "document.html.j2"


def render_html(
    document: RenderDocument,
    stylesheets: Sequence[str] = (),
    template_name: str = _DEFAULT_TEMPLATE,
) -> str:
    """Render *document* to a self-contained HTML string.

    *stylesheets* are filesystem paths whose contents are cascaded after the
    FIRE default ``base.css``.
    """
    template = _create_environment().get_template(template_name)
    return template.render(document=document, stylesheets=_collect_styles(stylesheets))


def _collect_styles(extra: Sequence[str]) -> list[str]:
    """Return the base stylesheet followed by each user stylesheet's content."""
    return [_BASE_CSS.read_text()] + [Path(p).read_text() for p in extra]


def _create_environment() -> Environment:
    """Create the Jinja2 environment with the markdown body filter registered."""
    env = Environment(
        loader=FileSystemLoader(_TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["markdown"] = lambda text: Markup(render_markdown(text))
    return env
