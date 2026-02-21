# Release Report Draft Format

This document captures the draft format for release readiness reporting.

Report inputs

- Requirements markdown files with inline metadata
- Parameter files (yaml)
- Implementation trace files (yaml)
- Verification trace files (yaml)
- Optional exemptions file (yaml)

Trace file format (YAML)

```yaml
- type: impl
  requirement: REQ-ABC-001
  source: src/control/brake_controller.py
  version: 2
  note: Implemented in braking controller
- type: verif
  requirement: REQ-ABC-001
  source: tests/test_brake_controller.py
  version: 2
```

Trace entry fields

- type: impl or verif
- requirement: Requirement id, required when tracing requirements
- param: Parameter name, required when tracing parameters
- source: Path to the implementation or test artifact
- version: Optional version tracked by the trace
- note: Optional description

Exemptions file format (YAML)

```YAML
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
