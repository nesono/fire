#!/bin/bash
# Integration test runner for fire requirements management system
#
# This script tests the end-to-end workflow of consuming fire as
# a Bazel module dependency.

set -euo pipefail

cd "$(dirname "$0")"

fail=0

echo "========================================="
echo "Fire Integration Test"
echo "========================================="
echo ""

echo "Running all Bazel tests..."
bazel test //... --test_output=errors
echo ""

echo "Verifying generated reports..."
if [ -f bazel-bin/compliance_report.md ]; then
    echo "Compliance report generated"
else
    echo "Compliance report not found"
	fail=1
fi

if [ -f bazel-bin/coverage_report.md ]; then
    echo "Coverage report generated"
else
    echo "Coverage report not found"
	fail=1
fi

if [ -f bazel-bin/traceability_report.md ]; then
    echo "Traceability report generated"
else
    echo "Traceability report not found"
	fail=1
fi

exit $fail
