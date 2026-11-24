# Release Report Format

This document describes the format for release readiness reporting.

## Report Inputs

- Requirements markdown files with inline metadata
- Parameter files (YAML)
- Source traceability files (JSON)

## Input File Formats

### Trace File Format (source_traceability JSON)

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

**Trace entry fields:**

- `implements`: Map of source file to requirement list
- `verifies`: Map of test file to requirement list
- `req_id`: Requirement ID
- `version`: Requirement version tracked by the trace

## Report Structure

### 1. Release Readiness Summary

Shows overall status and issues if any exist:

```markdown
**Status: READY FOR RELEASE**
```

or when issues are found:

```markdown
**Status: NOT READY FOR RELEASE**

### Issues Found

- ⚠️ Duplicate requirement IDs: **1** ([details](#requirement-id-uniqueness))
- ⚠️ Missing implementation traces: **5** ([details](#missing-implementation-traces))
- ⚠️ Missing verification traces: **3** ([details](#missing-verification-traces))
- ⚠️ Missing child requirements: **1** ([details](#missing-child-requirements))
- ⚠️ Stale references: **2** ([details](#version-consistency))
- ⚠️ Open TODOs: **1** ([details](#todo-inventory))
```

Each issue links to its detailed section for investigation.

### 2. Version Consistency

Reports on versioned references and identifies stale ones:

**When issues exist:**

```markdown
- ⚠️ **Found 2 stale reference(s) that need updating**
- ✓ 28 reference(s) are consistent
```

**When all consistent:**

```markdown
- ✓ All 30 versioned references are consistent
```

Followed by detailed lists of:

- **Stale Requirement References**: Requirements tracking outdated versions of parent requirements
- **Stale Parameter References**: Requirements tracking outdated parameter versions
- **Stale Trace Versions**: Implementation/verification traces tracking outdated requirement versions

Each stale reference shows source and destination links for easy navigation.

### 3. Requirement ID Uniqueness

Lists requirement IDs that are defined more than once across all requirement files, with every location:

```markdown
- **REQ-ABC-001** is defined at: first.md:1, second.md:12
```

or `- All requirement IDs are unique.` when there are none. Duplicate IDs make the report `NOT READY FOR RELEASE`.

### 4. TODO Inventory

Lists all TODO markers found in requirement and parameter files:

```markdown
- examples/requirements/braking.md: TODO(BRK-123)
- examples/params/vehicle.yaml: TODO(VEL-456)
```

TODOs must follow the pattern `TODO(TICKET-ID)` where TICKET-ID matches `[A-Z]+-[0-9]+`.

### 5. Coverage

Lists the coverage each document type requires (`child`, `implementation`,
`verification`; configurable in `fire_config.yaml`), then the requirements that
lack it:

```markdown
### Required Coverage

- System Requirement (`.sysreq.md`): child
- Software Requirement (`.swreq.md`): implementation, verification
- Regulatory Requirement (`.regreq.md`): verification
- Other files: implementation, verification

### Missing Implementation Traces

- [REQ-ABC-001](path/to/file.md#REQ-ABC-001)
- [REQ-XYZ-002](path/to/file.md#REQ-XYZ-002)

### Missing Verification Traces

- [REQ-ABC-003](path/to/file.md#REQ-ABC-003)

### Missing Child Requirements

- [REQ-SYS-004](path/to/file.md#REQ-SYS-004)
```

A requirement counts as having a child when another requirement lists it as
`Parent`, whatever version that link pins. Stale links are reported separately
under Version Consistency.

### 6. Traceability Graph

Mermaid diagram showing relationships between:

- Requirements → Parameters
- Requirements → Implementation files
- Requirements → Verification/test files

## Validation

Use `release_readiness_test` to validate that a report indicates readiness:

```python
release_readiness_test(
    name = "release_readiness",
    report = ":release_report",
)
```

The test fails if the report shows "NOT READY FOR RELEASE", making it suitable for CI/CD pipelines.
