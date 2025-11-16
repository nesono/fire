#!/bin/bash
# Run all targets tagged with 'failure_test'
#
# This script queries for all targets with the 'failure_test' tag
# and verifies they fail with the expected error message.

set -e

echo "========================================="
echo "Running Failure Tests"
echo "========================================="
echo ""

FAILURES=0
SUCCESSES=0

# Query all targets with the 'failure_test' tag
FAILURE_TARGETS=$(bazel query 'attr(tags, "failure_test", //...)' 2>/dev/null)

if [ -z "$FAILURE_TARGETS" ]; then
    echo "No targets with 'failure_test' tag found"
    exit 1
fi

# Run each failure test
for target in $FAILURE_TARGETS; do
    echo "Testing: $target (should FAIL)..."
    if bazel build "$target" 2>&1 | grep -q "not in declared dependencies"; then
        echo "✅ PASS: Build failed with correct error message"
        SUCCESSES=$((SUCCESSES + 1))
    else
        echo "❌ FAIL: Build should have failed with dependency error"
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
