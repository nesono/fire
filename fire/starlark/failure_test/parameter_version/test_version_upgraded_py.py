#!/usr/bin/env python3
"""Test that importing v1 when v2 exists causes deprecation warning."""

import warnings

# test_value_v1 exists but has a deprecation warning baked in
# The warning fires at import time, so we configure the filter first
warnings.simplefilter("always", DeprecationWarning)

from fire.starlark.failure_test.parameter_version.test_params_py.test_value_v1 import (  # noqa: E402
    TEST_VALUE,
)

print(f"Value: {TEST_VALUE}")
