#!/bin/bash
# Integration test runner for fire requirements management system
#
# This script tests the end-to-end workflow of consuming fire as
# a Bazel module dependency.
#
# Usage: ./run.sh [--python-version VERSION]
#   --python-version: Python version to test (default: 3.11)

set -euo pipefail

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

echo "========================================="
echo "Fire Integration Test"
echo "Python Version: $PYTHON_VERSION"
echo "========================================="
echo ""

# Generate MODULE.bazel from template
echo "Generating MODULE.bazel for Python $PYTHON_VERSION..."
sed "s/{{PYTHON_VERSION}}/$PYTHON_VERSION/g" MODULE.bazel.template > MODULE.bazel
echo ""

echo "Running all Bazel tests..."
bazel test --config=ci --repository_cache="$HOME/.cache/bazel-repo" //... --test_output=errors
echo ""

echo "Building release report..."
bazel build --config=ci --repository_cache="$HOME/.cache/bazel-repo" //:integration_release_report
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
bazel test --config=ci --repository_cache="$HOME/.cache/bazel-repo" //:integration_release_readiness --test_output=all
echo ""

echo "Integration tests completed successfully!"

exit 0
