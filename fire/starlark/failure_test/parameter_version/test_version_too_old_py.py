#!/usr/bin/env python3
"""Test that requesting a version newer than available causes runtime error."""

from fire.starlark.failure_test.parameter_version.test_params import test_value

# Parameter is at version 2, but we request version 3
# This should raise RuntimeError
value = test_value(3)
print(f"Value: {value}")
