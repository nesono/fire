# Change Proposal: Stylesheet-Driven PDF Export for FIRE

## Context

FIRE documents are Markdown (`## ENTRY-ID` + metadata line + body) with their types and fields described by `fire_config.yaml` (`FireConfig`: `field_definitions` + `document_types`).
Systems-engineering teams need styled PDF deliverables (cover page, structured entries, fields, tables, traceability) for regulatory submissions.

At the time of writing, a reference implementation exists in a colleague's branch at `sys_eng/ai_assist/tools/reporting/pdf_export/`.
It proves the desired output quality but uses hard-coded, imperative `fpdf2` code: a ~1200-line `FormalPDF(FPDF)` base class plus one hand-written subclass and parser per document type (`.hara.md`, `.concept.md`, `.env.md`, …), duplicated top-level CLI copies, and a fully standalone ~1480-line `sysreq_to_pdf.py`.
Styling (colors, fonts, publisher, classification markings, layout) is hard-coded throughout.
Adding or changing a format requires editing Python; end users cannot customize the rendering.

The goal of this proposal is to deliver the same output quality through **user-provided and user-customizable CSS stylesheets**, with no per-type Python — mirroring how FIRE already performs code generation through swappable Jinja2 templates (`fire/starlark/generators/template_loader.py` + `fire/starlark/templates/*.j2`).

## Design: data → templated HTML → CSS-styled PDF

```text
FIRE markdown (+ fire_config.yaml)
   │  reuse parse_requirement_sections + FireConfig
   ▼
structured render model (document, entries, typed fields, body)
   │  Jinja2 HTML template  (stable, documented class contract)
   ▼
HTML  +  markdown body → HTML
   │  base.css (FIRE-shipped)  ⊕  user stylesheets (CSS cascade / override)
   ▼
WeasyPrint (HTML + CSS → PDF)  ──▶  document.pdf
```

Existing FIRE code is reused for parsing, so little new parsing logic is introduced:

- `release_report.parse_requirement_sections()` → entries `{id, metadata, body}`
- `config_models.FireConfig` → field display names, required/optional fields
- `metadata_parsing`, `markdown_common`, `version_tracking` → inline metadata, cross-references, version maps

Markdown body text is converted to HTML via a small dependency (recommended: `markdown-it-py`; alternative: `python-markdown` with the `tables`, `fenced_code`, and `attr_list` extensions).

### Two customization layers, no Python required

1. **CSS stylesheets (primary).** Control `@page` size/margins, running headers/footers, page counters, fonts, colors, badges, and table styling. Users add `.css` files or override the FIRE default through the CSS cascade.
2. **HTML Jinja2 template (advanced, optional).** Controls document structure: cover page, table of contents, field ordering, traceability matrix. A default ships with FIRE and may be overridden.

### The stable class contract

The mechanism that makes CSS-only styling possible is a documented set of HTML classes and `data-` attributes emitted by the template, driven generically by `fire_config.yaml`.
For example:

```html
<section class="fire-entry" data-doc-type="sysreq">
  <h2 class="fire-entry__id">REQ-BRK-001</h2>
  <dl class="fire-fields">
    <div class="fire-field fire-field--sil" data-value="ASIL-D">
      <dt>SIL</dt>
      <dd>ASIL-D</dd>
    </div>
  </dl>
  <div class="fire-entry__body">…</div>
</section>
```

CSS then targets these hooks (`.fire-field--sil[data-value="ASIL-D"]`, `.fire-entry[data-doc-type="hara"]`, …).
New document types and fields are styled entirely in CSS with **no new Python**.

## Key Architectural Decisions

- **WeasyPrint** as the HTML→PDF engine: pure-Python, pip-installable, with first-class CSS paged-media support (`@page`, running headers/footers, page counters). This makes "CSS = the stylesheet" natural and keeps FIRE's minimal, pip-managed dependency philosophy. Tradeoff: it pulls native libraries (pango/cairo/harfbuzz) and requires fonts to be provisioned.
- **Default stylesheet and template ship with FIRE** (analog of `default_fire_config.yaml`). User stylesheets are cascaded after the base, so overriding requires no full rewrite.
- **`document_pdf` is a build rule** that produces the `.pdf` as an output artifact. Because the engine needs native libs and fonts, the action runs via `run_python_script(..., no_sandbox = True, use_default_shell_env = True)` — the same escape hatch the existing `_validate_requirements` rule already uses for workspace and native access. Font availability is documented as a prerequisite (the colleague's implementation likewise requires DejaVu fonts).
- **Config-driven, type-agnostic rendering** — no per-suffix Python branches.

## Files to Create

| File                                              | Purpose                                                                                                     |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `fire/starlark/render/document_model.py`          | Build a render model (document + entries + typed fields) from parsed sections and `FireConfig`              |
| `fire/starlark/render/markdown_render.py`         | Convert markdown body → HTML (inline refs, tables, code)                                                    |
| `fire/starlark/render/html_render.py`             | Jinja2 environment + render model → HTML (analog of `template_loader.py`)                                   |
| `fire/starlark/render/render_pdf.py`              | CLI: HTML + stylesheets → PDF via WeasyPrint (`--config`, `--stylesheet` repeatable, `--template`, `--out`) |
| `fire/starlark/render/templates/document.html.j2` | Default document template that defines the class contract                                                   |
| `fire/starlark/render/styles/base.css`            | Default FIRE stylesheet (A4, headers/footers, badges, tables)                                               |
| `fire/starlark/render/*_test.py`                  | TDD unit tests for each module                                                                              |
| `fire/starlark/pdf.bzl`                           | `document_pdf` rule (+ optional `pdf_stylesheet` macro for reusable branding bundles)                       |

## Files to Modify

| File                                          | Change                                                                                                          |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `fire/starlark/BUILD.bazel`                   | New `py_binary`/`py_library`/`py_test` targets; `data = glob(["render/templates/*.j2", "render/styles/*.css"])` |
| `requirements.txt`                            | Add `weasyprint` (+ transitive deps) and the markdown library                                                   |
| `fire/starlark/BUILD.bazel` (`exports_files`) | Export `pdf.bzl`, default CSS and template                                                                      |
| `README.md`                                   | New "PDF Export" section (concise, snippet-driven)                                                              |
| `integration_test/`                           | End-to-end `document_pdf` target asserting a PDF is produced                                                    |

## Bazel Integration

```starlark
load("@fire//fire/starlark:pdf.bzl", "document_pdf")

document_pdf(
    name = "braking_pdf",
    srcs = ["requirements/braking.sysreq.md"],
    config = ":fire_config.yaml",                 # optional → embedded default
    stylesheets = ["//branding:corporate.css"],   # cascaded over FIRE base.css
    # template = "//branding:doc.html.j2",          # optional override
    out = "braking.pdf",
)
```

| Attribute     | Type                                         | Notes                                      |
| ------------- | -------------------------------------------- | ------------------------------------------ |
| `srcs`        | `label_list([".md"])`                        | Markdown document(s) to render             |
| `config`      | `label(allow_single_file=[".yaml", ".yml"])` | Optional; `None` → embedded default config |
| `stylesheets` | `label_list([".css"])`                       | Ordered; cascaded after `base.css`         |
| `template`    | `label(allow_single_file=[".j2", ".html"])`  | Optional override of the default template  |
| `out`         | `output`                                     | Generated PDF                              |
| `_script`     | `label(executable, cfg="exec")`              | Hidden; the `render_pdf` binary            |

## Implementation Phases

Each phase is byte-sized, TDD, and independently mergeable, per `AGENT.md`.

### Phase 1: Render model (no Bazel)

Build the render model from existing parsers (`parse_requirement_sections` + `FireConfig`).
Fully unit-tested, no rule yet.

### Phase 2: HTML rendering

Markdown→HTML renderer, default HTML template, `base.css`, and the documented class contract.
Unit tests render the model with the default and an overriding stylesheet.

### Phase 3: PDF CLI

`render_pdf.py` converting HTML + CSS → PDF via WeasyPrint.
Guarded engine import with an actionable error when the engine or fonts are missing.

### Phase 4: Bazel rule

`document_pdf` rule, `BUILD.bazel` targets, and an integration test asserting a non-empty PDF is produced.

### Phase 5: Documentation and example

README "PDF Export" section, an example target, and documented font/native-lib prerequisites.

## Feature Reductions vs. the Reference Implementation

This proposal intentionally narrows scope relative to the colleague's `fpdf2` implementation.
The table records what is **dropped or deferred** and why, so we can schedule the deferred items as later phases.

| Reference feature                                                                                                          | Status here            | Rationale                                                                                           |
| -------------------------------------------------------------------------------------------------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------------- |
| Per-type imperative `fpdf2` subclasses + parsers (`hara`, `tara`, `mara`, `concept`, `env`, `handbook`, `opman`, `sysreq`) | **Replaced**           | Single config-driven, type-agnostic renderer; styling moves to CSS                                  |
| Hard-coded colors, publisher, `CONFIDENTIAL` markings, fonts                                                               | **Replaced**           | Moved into the user-customizable `base.css` / stylesheets                                           |
| Cross-document traceability matrix (upstream + downstream, `build_downstream_index`, `build_safety_index`)                 | **Deferred** (Phase 6) | v1 renders a single document; cross-doc indexing needs the full document set wired through the rule |
| Multi-file merge into one PDF (`--merge`)                                                                                  | **Deferred** (Phase 6) | Not needed for the single-doc v1 deliverable                                                        |
| Mermaid diagram rendering (`render_mermaid_to_png`, mermaid-py)                                                            | **Deferred** (Phase 6) | WeasyPrint has no JS engine; needs a separate diagram pre-render step                               |
| Encrypted/timestamped ZIP data packages (`--zip`, `--password`, pyzipper)                                                  | **Deferred** (Phase 6) | Packaging concern, orthogonal to rendering; can be a separate rule                                  |
| Orchestrator that discovers and dispatches all formats (`generate_all_pdfs.py`)                                            | **Replaced**           | Bazel targets provide discovery/dispatch via the build graph                                        |
| Automatic content-drop audit (`audit_content_drops.py`, `pdftotext`)                                                       | **Deferred** (Phase 6) | Useful fidelity check; revisit once rendering is stable                                             |
| KV-bullet promotion, grid-table width heuristics, rich-text font switching                                                 | **Replaced**           | Handled by the markdown→HTML step and CSS table/list styling                                        |
| Latin-1 sanitization fallback (`sanitize_latin1`)                                                                          | **Dropped**            | WeasyPrint + provisioned Unicode fonts render UTF-8 directly                                        |
| Cover-page metadata (commit hash/date, entry count, classification)                                                        | **Reduced**            | Default template includes a basic cover; richer metadata is a template/CSS enhancement              |

### Deferred backlog (Phase 6 and beyond)

1. Cross-document traceability matrix (upstream + downstream).
2. Multi-file merge into a single PDF.
3. Mermaid (and general diagram) rendering via a pre-render step.
4. Encrypted/timestamped ZIP data-package bundling.
5. Automatic markdown-vs-PDF content-drop audit.
6. Richer cover-page metadata (commit hash/date, classification, entry counts).

## Verification

- Unit tests: render-model construction, markdown→HTML, HTML rendering with the default and an overriding stylesheet.
- Integration test in `integration_test/run.sh` producing a non-empty PDF, plus a failure-mode test for a missing engine/fonts.
- `bazel test //...` with and without `--config=typecheck`.
- Pre-commit (Black, Ruff, Buildifier) and README consistency.

## Risks and Mitigations

- **Native libs/fonts (non-hermetic).** Mitigate with a `no_sandbox` rule, documented prerequisites, and actionable error messages. A hermetic font/lib toolchain is a possible future improvement.
- **New runtime dependencies vs. FIRE's minimalism.** Scope `weasyprint` and the markdown library to the PDF binary target only, not to core validation.
- **Diagrams deferred.** WeasyPrint has no JS engine; mermaid support is documented as a follow-up pre-render plugin (Phase 6).
