# Test Missing Requirement Dependency

## REQ-MISSING-001

SIL: ASIL-A | Sec: Public | Version: 1

This requirement references [REQ-BASE-001](/fire/starlark/failure_test/dependency_failures/base_requirement.md?version=1#REQ-BASE-001) but the dependency is NOT declared in BUILD.

This should FAIL validation.
