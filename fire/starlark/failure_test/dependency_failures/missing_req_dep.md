# Test Missing Requirement Dependency

## REQ-MISSING-001

```yaml
id: REQ-MISSING-001
status: draft
type: functional
references:
  requirements:
    - path: fire/starlark/tests/dependency_failures/base_requirement.md
      version: 1
```

This requirement references [REQ-BASE-001](fire/starlark/tests/dependency_failures/base_requirement.md#REQ-BASE-001) but the dependency is NOT declared in BUILD.

This should FAIL validation.
