# Release Report Draft Format

This document captures the draft format for release readiness reporting.

Report inputs

- Requirements markdown files with inline metadata
- Parameter files (yaml)
- Source traceability files (json)

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

Report sections

- Release readiness summary (pass or fail)
- Version consistency summary and outdated versions list
- TODO inventory
- Implementation coverage and verification coverage
- Mermaid graph for requirement and parameter traces
