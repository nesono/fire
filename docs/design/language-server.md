# Design: FIRE Language Server (Issue #307)

## Context

FIRE validates requirements and parameters at Bazel build time and reports
errors as plain strings without positions. A language server gives authors the
same feedback in the editor.

## Approach

- Python package `fire/lsp/` using `pygls`, reusing `fire_config.yaml`, the
  Pydantic models and `patterns.py` so editor and build rules do not drift.
- A position-aware parse layer (`fire/lsp/document_parser.py`) records the line
  and character range of headings, metadata fields, links and TODO markers.
  Validation failures map back to a range through the field node.
- Parity tests run build-time validation and LSP diagnostics over
  `failure_test/` and `examples/`; both must report the same rules.
- Bazel-dependent checks (`deps`, trace coverage, release readiness) stay in
  Bazel. The server never reports an error the build would accept.

Usage and the list of diagnostics are in [language-server.md](../language-server.md).

## Phases

1. Position-aware parser: headings and metadata fields, then links and TODOs
2. Requirement-file diagnostics and a minimal stdio server
3. Parameter YAML diagnostics
4. Workspace index and cross-file diagnostics, including stale versions
5. Definition, references, document links and symbols
6. Completion and hover, driven by the config
7. Code actions, such as bumping stale references
8. Rename and an "increment version" refactor
9. VS Code extension and editor documentation

## Open Questions

- Distribution: pip package versus Bazel target
- Detecting parameter YAML files: glob setting versus reading BUILD files
