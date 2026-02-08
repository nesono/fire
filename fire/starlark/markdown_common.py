"""Common markdown parsing utilities for Fire requirements management system.

This module provides regex patterns and extraction functions for parsing
markdown references used in requirements documents.
"""

import re

# Regex patterns for markdown reference parsing
MARKDOWN_LINK_PATTERN = r"\[([^\]]+)\]\(([^\)]+)\)"
PARAM_REFERENCE_PATTERN = r"\[@([a-zA-Z_][a-zA-Z0-9_]*)\]\(([^)]+)\)"
REQUIREMENT_REFERENCE_PATTERN = r"\[([A-Z][A-Z0-9_-]+)\]\(([^)]+\.md[^)]*)\)"


def extract_markdown_links(text: str) -> list[tuple[str, str]]:
    """Extract all markdown links from text.

    Args:
        text: Text containing markdown links

    Returns:
        List of (link_text, link_url) tuples

    Example:
        >>> extract_markdown_links("[Example](http://example.com)")
        [('Example', 'http://example.com')]
    """
    return re.findall(MARKDOWN_LINK_PATTERN, text)


def extract_param_references(text: str) -> list[tuple[str, str]]:
    """Extract parameter references from text.

    Parameter references use the [@param_name](path) syntax.

    Args:
        text: Text containing parameter references

    Returns:
        List of (param_name, path) tuples

    Example:
        >>> extract_param_references("[@velocity](params.yaml)")
        [('velocity', 'params.yaml')]
    """
    return re.findall(PARAM_REFERENCE_PATTERN, text)


def extract_requirement_references(text: str) -> list[tuple[str, str]]:
    """Extract requirement references from text.

    Requirement references use the [REQ-ID](path.md) syntax.

    Args:
        text: Text containing requirement references

    Returns:
        List of (req_id, path) tuples

    Example:
        >>> extract_requirement_references("[REQ-001](design.md)")
        [('REQ-001', 'design.md')]
    """
    return re.findall(REQUIREMENT_REFERENCE_PATTERN, text)
