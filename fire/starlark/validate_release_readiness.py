#!/usr/bin/env python3
"""Validate release readiness by checking the release report."""

from __future__ import annotations

import argparse
import sys


def validate_release_readiness(report_path: str) -> int:
    """Check if the release report indicates readiness.

    Args:
        report_path: Path to the release report markdown file

    Returns:
        0 if ready for release, 1 if not ready
    """
    with open(report_path, "r") as f:
        content = f.read()

    # Check if the report indicates readiness
    if "NOT READY FOR RELEASE" in content:
        print("❌ RELEASE READINESS CHECK FAILED")
        print()

        # Extract and display the issues section
        lines = content.split("\n")
        in_issues = False
        in_summary = False

        for i, line in enumerate(lines):
            # Find the summary section
            if "## Release Readiness Summary" in line:
                in_summary = True
                continue

            # Print the status line
            if in_summary and line.startswith("**Status:"):
                print(line)
                print()
                continue

            # Find the issues section
            if in_summary and "### Issues Found" in line:
                in_issues = True
                print("Issues preventing release:")
                continue

            # Print issue lines
            if in_issues:
                if line.startswith("- ⚠️"):
                    print(f"  {line}")
                elif line.strip() == "" and i > 0 and lines[i - 1].startswith("- ⚠️"):
                    # End of issues section
                    break

        print()
        print(f"📄 Full report: {report_path}")
        return 1

    elif "READY FOR RELEASE" in content:
        print("✅ RELEASE READINESS CHECK PASSED")
        print()
        print("The product is ready for release!")
        print(f"📄 Full report: {report_path}")
        return 0

    else:
        print("⚠️  WARNING: Could not determine release readiness status")
        print(f"Report may be malformed: {report_path}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release readiness")
    parser.add_argument("report", help="Path to the release report markdown file")
    args = parser.parse_args()

    return validate_release_readiness(args.report)


if __name__ == "__main__":
    sys.exit(main())
