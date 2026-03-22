#!/bin/bash
# Integration test runner for fire requirements management system
#
# This script tests the end-to-end workflow of consuming fire as
# a Bazel module dependency.
#
# Usage: ./run.sh [--python-version VERSION]
#   --python-version: Python version to test (default: 3.11)

set -euo pipefail

# Disable MSYS path conversion for Bazel targets (prevents //target from becoming /target)
export MSYS2_ARG_CONV_EXCL="*"

cd "$(dirname "$0")"

# Parse command line arguments
PYTHON_VERSION="3.11"
while [[ $# -gt 0 ]]; do
    case $1 in
        --python-version)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--python-version VERSION]"
            exit 1
            ;;
    esac
done

fail=0

# Detect Windows (rules_rust toolchain cannot build on Windows)
IS_WINDOWS=false
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    IS_WINDOWS=true
fi

echo "========================================="
echo "Fire Integration Test"
echo "Python Version: $PYTHON_VERSION"
echo "========================================="
echo ""

# Generate MODULE.bazel from template
echo "Generating MODULE.bazel for Python $PYTHON_VERSION..."
sed "s/{{PYTHON_VERSION}}/$PYTHON_VERSION/g" MODULE.bazel.template > MODULE.bazel
echo ""

REPO_CACHE=$(cygpath -w "$HOME/.cache/bazel-repo" 2>/dev/null || echo "$HOME/.cache/bazel-repo")

echo "Running all Bazel tests..."
if [[ "$IS_WINDOWS" == true ]]; then
    # Exclude Rust targets: rules_rust toolchain cannot build on Windows
    TARGETS="//:test_speed_limit //:test_braking //:test_update_rate //consumer:test_cpp_test"
    bazel test --config=ci --repository_cache="$REPO_CACHE" $TARGETS --test_output=errors
else
    bazel test --config=ci --repository_cache="$REPO_CACHE" //... --test_output=errors
fi
echo ""

echo "Building release report..."
bazel build --config=ci --repository_cache="$REPO_CACHE" //:integration_release_report
echo ""

echo "Verifying release report..."
if [ -f bazel-bin/RELEASE_REPORT.md ]; then
    echo "✓ Release report generated successfully"
    echo ""
    echo "Report summary:"
    head -20 bazel-bin/RELEASE_REPORT.md
else
    echo "✗ Release report not found"
    exit 1
fi
echo ""

echo "Running release readiness test..."
if [[ "$IS_WINDOWS" == true ]]; then
    echo "Skipping release readiness test on Windows (sh_test not supported)"
else
    bazel test --config=ci --repository_cache="$REPO_CACHE" //:integration_release_readiness --test_output=all
fi
echo ""

echo "Integration tests completed successfully!"

exit 0
