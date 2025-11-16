# Test Missing Parameter Dependency

## REQ-PARAM-001

This requirement references [@test_parameter](fire/starlark/failure_test/dependency_failures/test_params.bzl#test_parameter) but the dependency is NOT declared in BUILD.

This should FAIL validation.
