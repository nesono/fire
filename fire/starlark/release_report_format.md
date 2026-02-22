# Release Report Draft Format

This document captures the draft format for release readiness reporting.

Report inputs

- Requirements markdown files with inline metadata
- Parameter files (yaml)
- Source traceability files (json)
- Optional exemptions file (yaml)

Trace file format (source_traceability JSON)

```json
{
  "implements": {
    "src/control/brake_controller.py": [
      { "req_id": "REQ-ABC-001", "version": 2 }
    ]
  },
  "verifies": {
    "tests/test_brake_controller.py": [
      { "req_id": "REQ-ABC-001", "version": 2 }
    ]
  }
}
```

Trace entry fields

- implements: Map of source file to requirement list
- verifies: Map of test file to requirement list
- req_id: Requirement id
- version: Requirement version tracked by the trace

Exemptions file format (YAML)

```yaml
- requirement: REQ-ABC-001
  kind: impl
  justification: Deferred for prototype release
  owner: team-abc
  expires: 2026-06-01
```

Exemption entry fields

- requirement: Requirement id
- kind: impl, verif, version, or todo
- justification: Required explanation for release
- owner: Optional team or person
- expires: Optional ISO date

Report sections

- Release readiness summary (pass or fail)
- Version consistency summary and outdated versions list
- TODO inventory
- Implementation coverage and verification coverage
- Mermaid graph for requirement and parameter traces
- Exemptions list and their justifications
