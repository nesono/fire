# Test Missing Parameter Dependency

## REQ-PARAM-001

```yaml
id: REQ-PARAM-001
status: draft
type: functional
references:
  parameters:
    - fire/starlark/tests/dependency_failures/test_params.bzl#test_parameter
```

This requirement references [@test_parameter](fire/starlark/tests/dependency_failures/test_params.bzl#test_parameter) but the dependency is NOT declared in BUILD.

This should FAIL validation.
