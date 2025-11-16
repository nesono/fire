#!/bin/bash
# Integration test runner for fire requirements management system
#
# This script tests the end-to-end workflow of consuming fire as
# a Bazel module dependency.

set -euo pipefail

cd "$(dirname "$0")"

echo "========================================="
echo "Fire Integration Test"
echo "========================================="
echo ""

# Run all Bazel tests
echo "Running all Bazel tests..."
if ! bazel test //... --test_output=errors; then
    echo "❌ FAIL: Bazel tests failed"
    exit 1
fi
echo "✅ PASS: All Bazel tests passed"
echo ""

# Verify generated reports exist
echo "Verifying generated reports..."
FAILURES=0

if [ -f bazel-bin/compliance_report.md ]; then
    echo "✅ Compliance report generated"
else
    echo "❌ Compliance report not found"
    FAILURES=$((FAILURES + 1))
fi

if [ -f bazel-bin/coverage_report.md ]; then
    echo "✅ Coverage report generated"
else
    echo "❌ Coverage report not found"
    FAILURES=$((FAILURES + 1))
fi

if [ -f bazel-bin/traceability_report.md ]; then
    echo "✅ Traceability report generated"
else
    echo "❌ Traceability report not found"
    FAILURES=$((FAILURES + 1))
fi

echo ""

if [ $FAILURES -eq 0 ]; then
    echo "========================================="
    echo "Integration Test PASSED"
    echo "========================================="
    exit 0
else
    echo "========================================="
    echo "Integration Test FAILED"
    echo "========================================="
    exit 1
fi
