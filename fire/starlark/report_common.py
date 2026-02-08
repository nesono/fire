"""Common utilities for Fire requirement report generation.

This module provides reusable components for building markdown reports,
reducing duplication across report generation functions.
"""


def extract_references(frontmatter: dict, ref_type: str) -> list:
    """Extract references of a specific type from requirement frontmatter.

    Args:
        frontmatter: Requirement metadata dictionary
        ref_type: Type of reference ('parameters', 'tests', 'standards', 'requirements')

    Returns:
        List of references, empty list if not found

    Example:
        >>> frontmatter = {"references": {"parameters": ["speed", "accel"]}}
        >>> extract_references(frontmatter, "parameters")
        ['speed', 'accel']
    """
    if "references" not in frontmatter or not isinstance(
        frontmatter["references"], dict
    ):
        return []
    return frontmatter["references"].get(ref_type, [])


def build_markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    """Build markdown table lines from headers and rows.

    Args:
        headers: Column headers
        rows: List of row data (each row is a list of cell values)

    Returns:
        List of markdown lines for the table

    Example:
        >>> headers = ["ID", "Name"]
        >>> rows = [["REQ-1", "Speed"], ["REQ-2", "Accel"]]
        >>> table = build_markdown_table(headers, rows)
        >>> print(table[0])
        | ID | Name |
    """
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    # Create separator line with dashes matching header length
    separators = ["-" * (len(h) + 2) for h in headers]
    lines.append("|" + "|".join(separators) + "|")

    for row in rows:
        lines.append("| " + " | ".join(row) + " |")

    return lines


def format_reference_list(refs: list, formatter=None) -> str:
    """Format a list of references as markdown.

    Args:
        refs: List of references
        formatter: Optional function to format each reference (default: backtick wrap)

    Returns:
        Formatted string, or "-" if empty

    Example:
        >>> format_reference_list(["speed", "accel"])
        '`speed`, `accel`'
        >>> format_reference_list([])
        '-'
    """
    if not refs:
        return "-"

    if formatter is None:

        def formatter(x):
            return f"`{x}`"

    return ", ".join([formatter(ref) for ref in refs])
