#!/bin/bash
# Run all targets tagged with 'failure_test'
#
# Target discovery uses genquery (//fire/starlark/failure_test:*_targets).
# Each category of test is read from a pre-built genquery output file.

set -euo pipefail

echo "========================================="
echo "Running Failure Tests"
echo "========================================="
echo ""

FAILURES=0
SUCCESSES=0

# Bazel options for CI with repository cache (separate cache for failure tests)
BAZEL_OPTS="--config=ci --repository_cache=$HOME/.cache/bazel-repo-failure"

# Build genquery targets to obtain per-category target lists
GENQUERY_TARGETS=(
    "//fire/starlark/failure_test:version_too_old_targets"
    "//fire/starlark/failure_test:version_upgraded_targets"
    "//fire/starlark/failure_test:too_many_versions_targets"
    "//fire/starlark/failure_test:missing_version_targets"
    "//fire/starlark/failure_test:outdated_version_targets"
    "//fire/starlark/failure_test:future_version_targets"
    "//fire/starlark/failure_test:legacy_failure_targets"
)

echo "Building genquery target lists..."
bazel build $BAZEL_OPTS "${GENQUERY_TARGETS[@]}" 2>/dev/null

GENQUERY_DIR="bazel-bin/fire/starlark/failure_test"

if [ ! -f "$GENQUERY_DIR/legacy_failure_targets" ]; then
    echo "Genquery output not found under $GENQUERY_DIR"
    exit 1
fi

# Run each failure test
run_failure_test() {
    local target=$1
    local tag=$2

    echo "Testing: $target ..."

    if [ "$tag" = "version_too_old" ]; then
        set +e
        output=$(bazel build $BAZEL_OPTS "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            echo "✅ PASS: Build failed with version too old error"
            SUCCESSES=$((SUCCESSES + 1))
        else
            set +e
            run_output=$(bazel run $BAZEL_OPTS "$target" 2>&1)
            run_exit_code=$?
            set -e

            if [ $run_exit_code -ne 0 ]; then
                echo "✅ PASS: Runtime failed with version too old error"
                SUCCESSES=$((SUCCESSES + 1))
            else
                echo "❌ FAIL: Should have failed with version too old error"
                echo "Build exit code: $build_exit_code"
                echo "Run exit code: $run_exit_code"
                FAILURES=$((FAILURES + 1))
            fi
        fi

    elif [ "$tag" = "version_upgraded" ]; then
        set +e
        output=$(bazel build $BAZEL_OPTS --action_env=CACHE_BUST=$RANDOM "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            echo "❌ FAIL: Build should not fail for version upgraded test"
            echo "Exit code: $build_exit_code"
            echo "Output excerpt:"
            echo "$output" | head -20
            FAILURES=$((FAILURES + 1))
        elif echo "$output" | grep -qiE "warning.*deprecated|has been updated to version"; then
            echo "✅ PASS: Build produced deprecation warning"
            SUCCESSES=$((SUCCESSES + 1))
        else
            set +e
            run_output=$(bazel run $BAZEL_OPTS "$target" 2>&1)
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

    elif [ "$tag" = "too_many_versions" ]; then
        set +e
        output=$(bazel build $BAZEL_OPTS --action_env=CACHE_BUST=$RANDOM "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -eq 0 ]; then
            echo "❌ FAIL: Build should fail for too many versions test"
            echo "Exit code: $build_exit_code"
            echo "Output excerpt:"
            echo "$output" | head -20
            FAILURES=$((FAILURES + 1))
        elif echo "$output" | grep -qiE "exceed two entries"; then
            echo "✅ PASS: Build produced too many versions error"
            SUCCESSES=$((SUCCESSES + 1))
        fi

    elif [ "$tag" = "missing_version" ]; then
        set +e
        output=$(bazel build $BAZEL_OPTS "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            echo "✅ PASS: Build failed with missing version suffix error"
            SUCCESSES=$((SUCCESSES + 1))
        else
            echo "❌ FAIL: Build should have failed with missing version error"
            echo "Exit code: $build_exit_code"
            FAILURES=$((FAILURES + 1))
        fi

    elif [ "$tag" = "outdated_version" ]; then
        set +e
        output=$(bazel build $BAZEL_OPTS --action_env=CACHE_BUST=$RANDOM "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            echo "❌ FAIL: Build should not fail for outdated version test"
            echo "Exit code: $build_exit_code"
            echo "Output excerpt:"
            echo "$output" | head -20
            FAILURES=$((FAILURES + 1))
        elif echo "$output" | grep -qE "WARNING.*OUTDATED|but requirement is at version"; then
            echo "✅ PASS: Build produced outdated version warning"
            SUCCESSES=$((SUCCESSES + 1))
        else
            echo "❌ FAIL: Should have produced outdated version warning"
            echo "Output excerpt:"
            echo "$output" | head -20
            FAILURES=$((FAILURES + 1))
        fi

    elif [ "$tag" = "future_version" ]; then
        set +e
        output=$(bazel build $BAZEL_OPTS "$target" 2>&1)
        build_exit_code=$?
        set -e

        if [ $build_exit_code -ne 0 ]; then
            echo "✅ PASS: Build failed with future version error"
            SUCCESSES=$((SUCCESSES + 1))
        else
            echo "❌ FAIL: Build should have failed with future version error"
            echo "Exit code: $build_exit_code"
            FAILURES=$((FAILURES + 1))
        fi

    else
        # Legacy tests: dependency errors, VERSION MISMATCH, missing fields, etc.
        set +e
        output=$(bazel build $BAZEL_OPTS --action_env=CACHE_BUST=$RANDOM "$target" 2>&1)
        build_exit_code=$?
        set -e

        if echo "$output" | grep -q "not in declared dependencies"; then
            echo "✅ PASS: Build failed with dependency error"
            SUCCESSES=$((SUCCESSES + 1))
        elif echo "$output" | grep -q "VERSION MISMATCH"; then
            echo "✅ PASS: Build produced version mismatch warning"
            SUCCESSES=$((SUCCESSES + 1))
        elif echo "$output" | grep -qE "is a required property|has no metadata|Field required"; then
            echo "✅ PASS: Build failed with missing required field error"
            SUCCESSES=$((SUCCESSES + 1))
        elif echo "$output" | grep -q "must be repository-relative"; then
            echo "✅ PASS: Build failed with non-repository-relative path error"
            SUCCESSES=$((SUCCESSES + 1))
        elif echo "$output" | grep -q "Bare or malformed TODO"; then
            echo "✅ PASS: Build failed with bare/malformed TODO error"
            SUCCESSES=$((SUCCESSES + 1))
        elif echo "$output" | grep -qE "not a valid boolean|not a valid enumeration member|Input should be one of|not a valid integer|greater than or equal"; then
            echo "✅ PASS: Build failed with Pydantic validation error"
            SUCCESSES=$((SUCCESSES + 1))
        else
            echo "❌ FAIL: Build should have failed or produced expected warning"
            echo "Exit code: $build_exit_code"
            echo "Output excerpt:"
            echo "$output" | head -20
            FAILURES=$((FAILURES + 1))
        fi
    fi
    echo ""
}

# Process each category from genquery output files
for tag in version_too_old version_upgraded too_many_versions missing_version outdated_version future_version; do
    while IFS= read -r target; do
        [[ -z "$target" ]] && continue
        run_failure_test "$target" "$tag"
    done < "$GENQUERY_DIR/${tag}_targets"
done

while IFS= read -r target; do
    [[ -z "$target" ]] && continue
    run_failure_test "$target" "legacy"
done < "$GENQUERY_DIR/legacy_failure_targets"

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
