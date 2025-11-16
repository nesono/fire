#!/bin/bash
# Run all targets tagged with 'failure_test'
#
# This script queries for all targets with the 'failure_test' tag
# and verifies they fail or produce warnings as expected.

set -euo pipefail

echo "========================================="
echo "Running Failure Tests"
echo "========================================="
echo ""

FAILURES=0
SUCCESSES=0

# Query all targets with the 'failure_test' tag, excluding _validation targets
# (validation targets are internal implementation details)
FAILURE_TARGETS=$(bazel query 'attr(tags, "failure_test", //...) except attr(name, ".*_validation$", //...)' 2>/dev/null)

if [ -z "$FAILURE_TARGETS" ]; then
    echo "No targets with 'failure_test' tag found"
    exit 1
fi

# Run each failure test
for target in $FAILURE_TARGETS; do
    echo "Testing: $target ..."

    # Capture output (don't exit on bazel build failure)
    set +e
    output=$(bazel build "$target" 2>&1)
    build_exit_code=$?
    set -e

    # Check for dependency errors (should FAIL)
    if echo "$output" | grep -q "not in declared dependencies"; then
        echo "✅ PASS: Build failed with dependency error"
        SUCCESSES=$((SUCCESSES + 1))
    # Check for version mismatch warnings (should WARN)
    elif echo "$output" | grep -q "VERSION MISMATCH"; then
        echo "✅ PASS: Build produced version mismatch warning"
        SUCCESSES=$((SUCCESSES + 1))
    # Unexpected: build succeeded or failed with wrong error
    else
        echo "❌ FAIL: Build should have failed or produced expected warning"
        echo "Exit code: $build_exit_code"
        echo "Output excerpt:"
        echo "$output" | head -20
        FAILURES=$((FAILURES + 1))
    fi
    echo ""
done

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "✅ Passed: $SUCCESSES"
echo "❌ Failed: $FAILURES"
echo ""

if [ $FAILURES -eq 0 ]; then
    echo "All failure tests passed!"
    exit 0
else
    echo "Some failure tests failed!"
    exit 1
fi
