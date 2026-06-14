#!/usr/bin/env python3
"""Tests for the FIRE markdown→PDF CLI pipeline and engine guard."""

import builtins

import pytest

from fire.starlark.render.render_pdf import build_html, main, write_pdf

_SYSREQ = """\
# Braking System Requirements

## REQ-BRK-001

Sil: ASIL-D | Sec: true | Version: 1

The brake shall engage within 100 ms.
"""


@pytest.fixture()
def source(tmp_path):
    path = tmp_path / "brake.sysreq.md"
    path.write_text(_SYSREQ)
    return str(path)


def _block_weasyprint(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "weasyprint":
            raise ImportError("weasyprint not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


class TestBuildHtml:
    def test_default_config_renders_entry(self, source):
        html = build_html(source)
        assert '<h2 class="fire-entry__id">REQ-BRK-001</h2>' in html

    def test_body_is_rendered(self, source):
        assert "<p>The brake shall engage within 100 ms.</p>" in build_html(source)

    def test_stylesheet_is_inlined(self, source, tmp_path):
        override = tmp_path / "corp.css"
        override.write_text(".fire-cover__title { color: rebeccapurple; }\n")
        assert "rebeccapurple" in build_html(source, stylesheets=[str(override)])

    def test_custom_template(self, source, tmp_path):
        template = tmp_path / "minimal.html.j2"
        template.write_text("<h1>{{ document.title }}</h1>\n")
        html = build_html(source, template=str(template))
        assert html.strip() == "<h1>Braking System Requirements</h1>"


class TestEngineGuard:
    def test_write_pdf_raises_actionable_error(self, monkeypatch, tmp_path):
        _block_weasyprint(monkeypatch)
        with pytest.raises(RuntimeError) as excinfo:
            write_pdf("<html></html>", str(tmp_path / "out.pdf"))
        assert "WeasyPrint" in str(excinfo.value)

    def test_write_pdf_surfaces_underlying_error(self, monkeypatch, tmp_path):
        _block_weasyprint(monkeypatch)
        with pytest.raises(RuntimeError, match="weasyprint not installed"):
            write_pdf("<html></html>", str(tmp_path / "out.pdf"))

    def test_main_reports_missing_engine(self, monkeypatch, capsys, source, tmp_path):
        _block_weasyprint(monkeypatch)
        out = str(tmp_path / "out.pdf")
        monkeypatch.setattr("sys.argv", ["render_pdf", source, "--out", out])
        assert main() == 1
        err = capsys.readouterr().err
        assert "WeasyPrint" in err
        assert "weasyprint not installed" in err


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
