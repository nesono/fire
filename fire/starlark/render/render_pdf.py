#!/usr/bin/env python3
"""CLI: render a FIRE markdown document to a styled PDF via WeasyPrint.

The pipeline reuses the render model (Phase 1) and HTML rendering (Phase 2):
markdown + config → render model → self-contained HTML → PDF. WeasyPrint
itself is a normal pip dependency, but it loads native libraries (pango, cairo,
harfbuzz) at import time; that load is guarded so a host missing those libraries
or fonts produces an actionable error rather than an opaque ``OSError``.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from fire.starlark.config_models import load_config
from fire.starlark.render.document_model import build_render_document
from fire.starlark.render.html_render import render_html

_ENGINE_MISSING = (
    "WeasyPrint could not be initialized. Its native libraries (pango, cairo, "
    "harfbuzz) and fonts must be available on the host; see the PDF Export "
    "section of the README for prerequisites."
)


def build_html(
    source: str,
    config: str | None = None,
    stylesheets: Sequence[str] = (),
    template: str | None = None,
) -> str:
    """Render *source* markdown to a self-contained HTML string."""
    content = Path(source).read_text()
    document = build_render_document(content, source, load_config(config))
    if template is None:
        return render_html(document, stylesheets=stylesheets)
    return render_html(document, stylesheets=stylesheets, template_name=template)


def write_pdf(html: str, out: str) -> None:
    """Write *html* to the PDF file *out* using the WeasyPrint engine."""
    _load_engine().HTML(string=html).write_pdf(out)


def _load_engine():
    """Import WeasyPrint, raising an actionable error when its libs are missing.

    A missing native library or font surfaces as ``OSError`` from the cffi
    bindings at import time; ``ImportError`` covers an absent package.
    """
    try:
        import weasyprint
    except (ImportError, OSError) as exc:
        raise RuntimeError(_ENGINE_MISSING) from exc
    return weasyprint


def main() -> int:
    """CLI entrypoint for Bazel."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Render a FIRE document to PDF")
    parser.add_argument("source", help="Markdown document to render")
    parser.add_argument("--config", default=None, help="Path to fire_config.yaml")
    parser.add_argument(
        "--stylesheet",
        action="append",
        default=[],
        dest="stylesheets",
        help="CSS file cascaded after base.css (repeatable)",
    )
    parser.add_argument(
        "--template", default=None, help="Custom HTML template path or built-in name"
    )
    parser.add_argument("--out", required=True, help="Output PDF path")
    args = parser.parse_args()

    html = build_html(args.source, args.config, args.stylesheets, args.template)
    try:
        write_pdf(html, args.out)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
