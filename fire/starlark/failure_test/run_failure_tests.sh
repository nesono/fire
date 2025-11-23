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

# Function to check if target has a specific tag
has_tag() {
    local target=$1
    local tag=$2
    bazel query "attr(tags, '$tag', $target)" 2>/dev/null | grep -q "$target"
}

# Run each failure test
for target in $FAILURE_TARGETS; do
    echo "Testing: $target ..."

    # Determine test type based on tags
    if has_tag "$target" "version_too_old"; then
        # Version too old tests should fail at compile or runtime
        set +e
        output=$(bazel build "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            # Check for expected error patterns
            if echo "$output" | grep -qE "static_assert|older than expected|assertion.*failed"; then
                echo "✅ PASS: Build failed with version too old error"
                SUCCESSES=$((SUCCESSES + 1))
            else
                echo "✅ PASS: Build failed (version too old)"
                SUCCESSES=$((SUCCESSES + 1))
            fi
        else
            # Build succeeded, try running to check for runtime error
            set +e
            run_output=$(bazel run "$target" 2>&1)
            run_exit_code=$?
            set -e

            if [ $run_exit_code -ne 0 ]; then
                if echo "$run_output" | grep -qE "older than expected|RuntimeError|IllegalArgumentException|panic"; then
                    echo "✅ PASS: Runtime failed with version too old error"
                    SUCCESSES=$((SUCCESSES + 1))
                else
                    echo "✅ PASS: Runtime failed (version too old)"
                    SUCCESSES=$((SUCCESSES + 1))
                fi
            else
                echo "❌ FAIL: Should have failed with version too old error"
                echo "Build exit code: $build_exit_code"
                echo "Run exit code: $run_exit_code"
                FAILURES=$((FAILURES + 1))
            fi
        fi

    elif has_tag "$target" "version_upgraded"; then
        # Version upgraded tests should succeed but emit warning
        set +e
        output=$(bazel build "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            echo "❌ FAIL: Build should not fail for version upgraded test"
            echo "Exit code: $build_exit_code"
            echo "Output excerpt:"
            echo "$output" | head -20
            FAILURES=$((FAILURES + 1))
        else
            # Check for compile-time deprecation warning (C++)
            if echo "$output" | grep -qiE "warning.*deprecated|has been updated to version"; then
                echo "✅ PASS: Build produced deprecation warning"
                SUCCESSES=$((SUCCESSES + 1))
            else
                # Run and check for runtime warning
                set +e
                run_output=$(bazel run "$target" 2>&1)
                run_exit_code=$?
                set -e

                if echo "$run_output" | grep -qiE "warning.*updated to version|DeprecationWarning|has been updated"; then
                    echo "✅ PASS: Runtime produced version upgrade warning"
                    SUCCESSES=$((SUCCESSES + 1))
                elif [ $run_exit_code -eq 0 ]; then
                    echo "❌ FAIL: Should have produced version upgrade warning"
                    echo "Output excerpt:"
                    echo "$run_output" | head -20
                    FAILURES=$((FAILURES + 1))
                else
                    echo "❌ FAIL: Runtime should not fail for version upgraded test"
                    echo "Exit code: $run_exit_code"
                    FAILURES=$((FAILURES + 1))
                fi
            fi
        fi

    else
        # Legacy tests - check for dependency errors or VERSION MISMATCH
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
