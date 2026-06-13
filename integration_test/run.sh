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

# Accept extra Bazel options from environment (e.g., --config=ci --repository_cache=...)
BAZEL_OPTS="${BAZEL_EXTRA_OPTS:-}"

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
bazel test $BAZEL_OPTS //... --test_output=errors
echo ""

echo "Building release report..."
bazel build $BAZEL_OPTS //:integration_release_report
echo ""

echo "Verifying release report..."
if [ -f bazel-bin/RELEASE_REPORT.md ]; then
    echo "Release report generated successfully"
    echo ""
    echo "Report summary:"
    head -20 bazel-bin/RELEASE_REPORT.md
else
    echo "Release report not found"
    exit 1
fi
echo ""

echo "Building custom config targets (configurable document types)..."
bazel build $BAZEL_OPTS //custom_config:custom_format_spec //custom_config:custom_release_report
echo ""

echo "Verifying custom FORMAT_SPECIFICATION.md..."
CUSTOM_FORMAT_SPEC="bazel-bin/custom_config/FORMAT_SPECIFICATION.md"
if [ -f "$CUSTOM_FORMAT_SPEC" ]; then
    echo "Custom format spec generated successfully"
    # Verify it contains the custom handbook type
    if grep -q "Handbook Entry" "$CUSTOM_FORMAT_SPEC"; then
        echo "Custom document type 'Handbook Entry' found in format spec"
    else
        echo "ERROR: Custom document type 'Handbook Entry' not found in format spec"
        exit 1
    fi
else
    echo "ERROR: Custom format spec not found"
    exit 1
fi
echo ""

echo "Verifying custom release report..."
CUSTOM_REPORT="bazel-bin/custom_config/CUSTOM_RELEASE_REPORT.md"
if [ -f "$CUSTOM_REPORT" ]; then
    echo "Custom release report generated successfully"
    if grep -q "HB-001" "$CUSTOM_REPORT"; then
        echo "Handbook requirement HB-001 found in release report"
    else
        echo "ERROR: Handbook requirement HB-001 not found in release report"
        exit 1
    fi
else
    echo "ERROR: Custom release report not found"
    exit 1
fi
echo ""

echo "Rendering PDF deliverable (document_pdf)..."
PDF_BUILD_LOG=$(mktemp)
if bazel build $BAZEL_OPTS //:integration_pdf 2>"$PDF_BUILD_LOG"; then
    PDF_OUT="bazel-bin/braking.pdf"
    if [ -s "$PDF_OUT" ] && head -c 4 "$PDF_OUT" | grep -q "%PDF"; then
        echo "PDF deliverable generated successfully ($(wc -c <"$PDF_OUT") bytes)"
    else
        echo "ERROR: PDF deliverable was not produced or is empty"
        exit 1
    fi
elif grep -q "WeasyPrint could not" "$PDF_BUILD_LOG"; then
    echo "WARNING: skipping PDF assertion - WeasyPrint native libraries/fonts"
    echo "         are not available on this host (see README PDF Export)."
else
    cat "$PDF_BUILD_LOG"
    echo "ERROR: PDF build failed"
    exit 1
fi
echo ""

echo "Running release readiness test..."
bazel test $BAZEL_OPTS //:integration_release_readiness --test_output=all
echo ""

echo "Integration tests completed successfully!"

exit 0
