"""Common markdown parsing utilities for Fire requirements management system.

This module provides regex patterns and extraction functions for parsing
markdown references used in requirements documents.
"""

import re
from typing import Final

# Regex patterns for markdown reference parsing
MARKDOWN_LINK_PATTERN: Final = r"\[([^\]]+)\]\(([^\)]+)\)"
PARAM_REFERENCE_PATTERN: Final = r"\[@([a-zA-Z_][a-zA-Z0-9_]*)\]\(([^)]+)\)"
REQUIREMENT_REFERENCE_PATTERN: Final = r"\[([A-Z][A-Z0-9_-]+)\]\(([^)]+\.md[^)]*)\)"


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


def extract_link_definitions(text: str) -> dict[str, str]:
    """Extract reference-style link definitions from markdown text.

    Reference-style link definitions have the format:
        [label]: url

    Args:
        text: Markdown text containing link definitions

    Returns:
        Dictionary mapping reference labels to URLs

    Example:
        >>> text = "[1]: http://example.com\\n[ref]: /path/file.md"
        >>> extract_link_definitions(text)
        {'1': 'http://example.com', 'ref': '/path/file.md'}
    """
    pattern = r"^\[([^\]]+)\]:\s*(.+)$"
    definitions = {}
    for match in re.finditer(pattern, text, re.MULTILINE):
        label = match.group(1)
        url = match.group(2).strip()
        definitions[label] = url
    return definitions


def extract_reference_style_links(text: str) -> list[tuple[str, str]]:
    """Extract reference-style links from markdown text.

    Supports three formats:
        [text][ref]   - Explicit reference
        [text][]      - Implicit reference (text is the label)
        [text]        - Shortcut reference (text is the label)

    Args:
        text: Markdown text containing reference-style links

    Returns:
        List of (link_text, reference_label) tuples

    Example:
        >>> extract_reference_style_links("[See this][1] and [REQ-001]")
        [('See this', '1'), ('REQ-001', 'REQ-001')]
    """
    links = []

    # Explicit reference: [text][ref]
    for match in re.finditer(r"\[([^\]]+)\]\[([^\]]+)\]", text):
        links.append((match.group(1), match.group(2)))

    # Implicit reference: [text][]
    for match in re.finditer(r"\[([^\]]+)\]\[\]", text):
        links.append((match.group(1), match.group(1)))

    # Shortcut reference: [text] (not followed by (, [, or :)
    for match in re.finditer(r"\[([^\]]+)\](?!\(|\[|:)", text):
        links.append((match.group(1), match.group(1)))

    return links


def resolve_reference_links(text: str) -> str:
    """Resolve reference-style links to inline-style links.

    Finds reference-style link definitions and replaces all reference-style
    links with their corresponding inline links.

    Args:
        text: Markdown text with reference-style links and definitions

    Returns:
        Text with reference-style links converted to inline links

    Raises:
        ValueError: If a reference label is used but not defined

    Example:
        >>> text = "[See this][1]\\n[1]: http://example.com"
        >>> resolve_reference_links(text)
        '[See this](http://example.com)\\n[1]: http://example.com'
    """
    definitions = extract_link_definitions(text)

    # Process explicit references: [text][ref]
    def replace_explicit(match):
        link_text = match.group(1)
        ref_label = match.group(2)
        if ref_label not in definitions:
            raise ValueError(f"Undefined reference: [{ref_label}]")
        return f"[{link_text}]({definitions[ref_label]})"

    text = re.sub(r"\[([^\]]+)\]\[([^\]]+)\]", replace_explicit, text)

    # Process implicit references: [text][]
    def replace_implicit(match):
        link_text = match.group(1)
        if link_text not in definitions:
            raise ValueError(f"Undefined reference: [{link_text}]")
        return f"[{link_text}]({definitions[link_text]})"

    text = re.sub(r"\[([^\]]+)\]\[\]", replace_implicit, text)

    # Process shortcut references: [text] (not followed by (, [, or :)
    def replace_shortcut(match):
        link_text = match.group(1)
        if link_text not in definitions:
            raise ValueError(f"Undefined reference: [{link_text}]")
        return f"[{link_text}]({definitions[link_text]})"

    text = re.sub(r"\[([^\]]+)\](?!\(|\[|:)", replace_shortcut, text)

    return text
