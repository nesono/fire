#!/usr/bin/env python3
"""Test that requesting an older version causes deprecation warning."""

import warnings
from fire.starlark.failure_test.parameter_version.test_params import test_value

# Ensure warnings are displayed
warnings.simplefilter("always", DeprecationWarning)

# Parameter is at version 2, but we request version 1
# This should emit a DeprecationWarning
value = test_value(1)
print(f"Value: {value}")
