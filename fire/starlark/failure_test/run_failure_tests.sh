#!/bin/bash
# Run all targets tagged with 'failure_test'
#
# This script parses BUILD files to find targets with the 'failure_test' tag
# and verifies they fail or produce warnings as expected.

set -euo pipefail

echo "========================================="
echo "Running Failure Tests"
echo "========================================="
echo ""

FAILURES=0
SUCCESSES=0

# Query Bazel once for all targets with build output format (easy to parse!)
# Output format: //package:target|tag1 tag2 tag3
echo "Querying Bazel for failure test targets..."
PARSED_TARGETS=$(bazel query --output=build '//fire/starlark/failure_test/...' 2>/dev/null | awk '
  /^[ \t]*[A-Za-z_][A-Za-z0-9_]*\([ \t]*$/ { in_rule=1; name=""; tags=""; pkg=""; next }

  in_rule && /^[ \t]*\)[ \t]*$/ {
    if (name != "" && pkg != "" && tags ~ /failure_test/ && name !~ /_validation$/) {
      print "//" pkg ":" name "|" tags
    }
    in_rule=0
    next
  }

  in_rule && /^[ \t]*name[ \t]*=/ {
    s=$0
    sub(/.*name[ \t]*=[ \t]*"/, "", s)
    sub(/".*/, "", s)
    name=s
    next
  }

  in_rule && /^[ \t]*generator_location[ \t]*=/ {
    s=$0
    sub(/.*generator_location[ \t]*=[ \t]*"/, "", s)
    sub(/\/BUILD.bazel.*/, "", s)
    pkg=s
    next
  }

  in_rule && /^[ \t]*tags[ \t]*=/ {
    s=$0
    sub(/.*tags[ \t]*=[ \t]*/, "", s)
    sub(/,[ \t]*$/, "", s)
    gsub(/[\[\]"]/, "", s)
    gsub(/,/, " ", s)
    gsub(/[ \t]+/, " ", s)
    sub(/^[ \t]+/, "", s)
    sub(/[ \t]+$/, "", s)
    tags=s
    next
  }
')

if [ -z "$PARSED_TARGETS" ]; then
    echo "No targets with 'failure_test' tag found"
    exit 1
fi

# Extract list of failure test targets
FAILURE_TARGETS=$(echo "$PARSED_TARGETS" | cut -d'|' -f1)

# Fast tag lookup using parsed BUILD file data (bash 3.2 compatible)
has_tag() {
    local target=$1
    local tag=$2
    local tags=$(echo "$PARSED_TARGETS" | grep "^${target}|" | cut -d'|' -f2)
    [[ " $tags " == *" $tag "* ]]
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
                if echo "$run_output" | grep -qE "older than expected|RuntimeError|IllegalArgumentException|panic|ModuleNotFoundError|ImportError|No module named"; then
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
        # Force full rebuild to see compile-time warnings
        set +e
        output=$(bazel build --action_env=CACHE_BUST=$RANDOM "$target" 2>&1)
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

    elif has_tag "$target" "too_many_versions"; then
        set +e
        output=$(bazel build --action_env=CACHE_BUST=$RANDOM "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -eq 0 ]; then
            echo "❌ FAIL: Build should fail for too many versions test"
            echo "Exit code: $build_exit_code"
            echo "Output excerpt:"
            echo "$output" | head -20
            FAILURES=$((FAILURES + 1))
        else
            # Check for compile-time deprecation warning (C++)
            if echo "$output" | grep -qiE "exceed two entries"; then
                echo "✅ PASS: Build produced too many versions error"
                SUCCESSES=$((SUCCESSES + 1))
            fi
        fi

    elif has_tag "$target" "missing_version"; then
        # Missing version suffix tests should fail at build time
        set +e
        output=$(bazel build "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            # Check for expected error pattern
            if echo "$output" | grep -qE "is missing \?version= suffix"; then
                echo "✅ PASS: Build failed with missing version suffix error"
                SUCCESSES=$((SUCCESSES + 1))
            else
                echo "✅ PASS: Build failed (missing version)"
                SUCCESSES=$((SUCCESSES + 1))
            fi
        else
            echo "❌ FAIL: Build should have failed with missing version error"
            echo "Exit code: $build_exit_code"
            FAILURES=$((FAILURES + 1))
        fi

    elif has_tag "$target" "outdated_version"; then
        # Outdated version tests should succeed but emit warning
        set +e
        output=$(bazel build --action_env=CACHE_BUST=$RANDOM "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            echo "❌ FAIL: Build should not fail for outdated version test"
            echo "Exit code: $build_exit_code"
            echo "Output excerpt:"
            echo "$output" | head -20
            FAILURES=$((FAILURES + 1))
        else
            # Check for outdated version warning
            if echo "$output" | grep -qE "WARNING.*OUTDATED|but requirement is at version"; then
                echo "✅ PASS: Build produced outdated version warning"
                SUCCESSES=$((SUCCESSES + 1))
            else
                echo "❌ FAIL: Should have produced outdated version warning"
                echo "Output excerpt:"
                echo "$output" | head -20
                FAILURES=$((FAILURES + 1))
            fi
        fi

    elif has_tag "$target" "future_version"; then
        # Future version tests should fail at build time
        set +e
        output=$(bazel build "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            # Check for expected error pattern
            if echo "$output" | grep -qE "but requirement is only at version"; then
                echo "✅ PASS: Build failed with future version error"
                SUCCESSES=$((SUCCESSES + 1))
            else
                echo "✅ PASS: Build failed (future version)"
                SUCCESSES=$((SUCCESSES + 1))
            fi
        else
            echo "❌ FAIL: Build should have failed with future version error"
            echo "Exit code: $build_exit_code"
            FAILURES=$((FAILURES + 1))
        fi

    else
        # Legacy tests - check for dependency errors or VERSION MISMATCH
        # Force full rebuild to see warnings
        set +e
        output=$(bazel build --action_env=CACHE_BUST=$RANDOM "$target" 2>&1)
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
        # Check for missing required fields (should FAIL)
        elif echo "$output" | grep -qE "is a required property|has no metadata|Field required"; then
            echo "✅ PASS: Build failed with missing required field error"
            SUCCESSES=$((SUCCESSES + 1))
        # Check for non-repository-relative paths (should FAIL)
        elif echo "$output" | grep -q "must be repository-relative"; then
            echo "✅ PASS: Build failed with non-repository-relative path error"
            SUCCESSES=$((SUCCESSES + 1))
        # Check for bare/malformed TODO markers (should FAIL)
        elif echo "$output" | grep -q "Bare or malformed TODO"; then
            echo "✅ PASS: Build failed with bare/malformed TODO error"
            SUCCESSES=$((SUCCESSES + 1))
        # Check for Pydantic validation errors (should FAIL)
        elif echo "$output" | grep -qE "not a valid boolean|not a valid enumeration member|Input should be one of|not a valid integer|greater than or equal"; then
            echo "✅ PASS: Build failed with Pydantic validation error"
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
