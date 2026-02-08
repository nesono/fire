"""Common code generation utilities for Fire parameter generators.

This module provides reusable patterns for generating code files from templates,
reducing duplication across language-specific generators.
"""

from collections.abc import Callable

from fire.starlark.generators.template_loader import render_template


def generate_files_per_item(
    items: list[dict],
    template_name: str,
    filename_pattern: Callable[[dict], str],
    context_builder: Callable[[dict], dict] | None = None,
) -> list[tuple[str, str]]:
    """Generate one file per item using a template.

    Args:
        items: List of parameter items to generate files for
        template_name: Jinja2 template file name
        filename_pattern: Function that takes an item and returns the output filename
        context_builder: Optional function that takes an item and returns extra context

    Returns:
        List of (filename, content) tuples

    Example:
        >>> generate_files_per_item(
        ...     items=[{"base_name": "speed", "version": 1}],
        ...     template_name="python.py.j2",
        ...     filename_pattern=lambda item: f"{item['base_name']}_v{item['version']}.py"
        ... )
        [('speed_v1.py', '<generated content>')]
    """
    files = []
    for item in items:
        # Build template context
        context = {"item": item}
        if context_builder:
            context.update(context_builder(item))

        # Generate file
        filename = filename_pattern(item)
        content = render_template(template_name, **context)
        files.append((filename, content))

    return files


def generate_file_aggregate(
    items: list[dict],
    template_name: str,
    filename: str,
    extra_context: dict | None = None,
) -> list[tuple[str, str]]:
    """Generate a single file containing all items using a template.

    Args:
        items: List of parameter items to include in the file
        template_name: Jinja2 template file name
        filename: Output filename
        extra_context: Optional extra context variables for the template

    Returns:
        List with single (filename, content) tuple

    Example:
        >>> generate_file_aggregate(
        ...     items=[{"base_name": "speed", "version": 1}],
        ...     template_name="rust_all.rs.j2",
        ...     filename="lib.rs"
        ... )
        [('lib.rs', '<generated content>')]
    """
    context = {"items": items}
    if extra_context:
        context.update(extra_context)

    content = render_template(template_name, **context)
    return [(filename, content)]
