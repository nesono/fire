#!/usr/bin/env python3
"""Test that importing a version that doesn't exist causes import error."""

# test_value_v3 does not exist (max version is v2), so this should fail
from fire.starlark.failure_test.parameter_version.test_params_py.test_value_v3 import (
    TEST_VALUE,
)

print(f"Value: {TEST_VALUE}")
