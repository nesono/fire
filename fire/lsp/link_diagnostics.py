#!/usr/bin/env python3
"""Check parameter and requirement links without touching the filesystem.

These rules mirror what the build enforces for link syntax. Whether the target
exists, or is stale, needs a workspace index and is checked elsewhere.
"""

from __future__ import annotations

import re
from typing import Final

from fire.lsp.diagnostic import Diagnostic, error, warning
from fire.lsp.document_parser import (
    Link,
    Requirement,
    parse_links,
    parse_unresolved_references,
)
from fire.starlark import patterns

_PARAM_TEXT_RE: Final = re.compile(r"@[a-zA-Z_][a-zA-Z0-9_]*")


def is_parameter_link(link: Link) -> bool:
    return bool(_PARAM_TEXT_RE.fullmatch(link.text))


def is_requirement_link(link: Link) -> bool:
    return bool(patterns.REQ_ID_PATTERN.match(link.text)) and ".md" in link.url


def _path_diagnostics(link: Link) -> list[Diagnostic]:
    if link.path.startswith("/"):
        return []
    message = f"Reference path must be repository-relative (start with /): '{link.url}'"
    return [error(link.url_range, "FIRE009", message)]


def _version_diagnostics(link: Link) -> list[Diagnostic]:
    if link.version is not None:
        return []
    message = f"Reference '{link.text}' is missing a ?version=N query parameter"
    if is_parameter_link(link):
        return [error(link.url_range, "FIRE010", message)]
    return [warning(link.url_range, "FIRE010", message)]


def _anchor_diagnostics(link: Link) -> list[Diagnostic]:
    if not is_parameter_link(link) or link.anchor in (None, link.text[1:]):
        return []
    message = f"Link text '{link.text}' does not match anchor '#{link.anchor}'"
    return [error(link.text_range, "FIRE011", message)]


def _parent_lines(requirements: list[Requirement]) -> set[int]:
    return {
        field.value_range.start.line
        for requirement in requirements
        for field in requirement.fields
        if field.key.lower() == "parent"
    }


def _diagnose_link(link: Link, check_path: bool) -> list[Diagnostic]:
    diagnostics = _path_diagnostics(link) if check_path else []
    return diagnostics + _version_diagnostics(link) + _anchor_diagnostics(link)


def is_checked_link(link: Link) -> bool:
    if "TODO" in link.url:
        return False
    return is_parameter_link(link) or is_requirement_link(link)


def _looks_like_a_reference(text: str) -> bool:
    return bool(_PARAM_TEXT_RE.fullmatch(text) or patterns.REQ_ID_PATTERN.match(text))


def _undefined_references(text: str) -> list[Diagnostic]:
    # Only parameter and requirement references are checked, so prose such as
    # array[i][j] is left alone.
    return [
        error(ref.range, "FIRE016", f"Reference label '{ref.label}' is not defined")
        for ref in parse_unresolved_references(text)
        if _looks_like_a_reference(ref.text)
    ]


def diagnose_links(text: str, requirements: list[Requirement]) -> list[Diagnostic]:
    """Return diagnostics for parameter and requirement links in *text*.

    Paths on ``Parent`` lines are left to the metadata field rules.
    """
    parent_lines = _parent_lines(requirements)
    diagnostics = _undefined_references(text)
    for link in parse_links(text):
        if is_checked_link(link):
            check_path = link.url_range.start.line not in parent_lines
            diagnostics.extend(_diagnose_link(link, check_path))
    return diagnostics
