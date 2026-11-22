#!/usr/bin/env python3
"""Resolve what a link in a requirement document points to."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fire.lsp.document_parser import Link, Position, Range, parse_links
from fire.lsp.index import parameters_in, requirements_in
from fire.lsp.link_diagnostics import is_checked_link, is_parameter_link
from fire.lsp.workspace import Workspace

_FILE_START = Range(Position(0, 0), Position(0, 0))


@dataclass(frozen=True)
class Target:
    path: Path
    range: Range


def _contains(link: Link, position: Position) -> bool:
    """True if *position* is within ``[text](url)``, brackets included."""
    if position.line != link.text_range.start.line:
        return False
    start = link.text_range.start.character - 1
    end = link.url_range.end.character + 1
    return start <= position.character < end


def link_at(text: str, position: Position) -> Link | None:
    """Return the link under *position*, if any."""
    return next((link for link in parse_links(text) if _contains(link, position)), None)


def _parameter_range(link: Link, content: str) -> Range | None:
    info = parameters_in(content).get(link.anchor or link.text[1:])
    if info is None:
        return None
    return info.versions.get(link.version) or info.versions[max(info.versions)]


def _requirement_range(
    link: Link, content: str, suffixes: tuple[str, ...]
) -> Range | None:
    if not link.path.endswith(suffixes):
        return None
    info = requirements_in(content).get(link.text)
    return info.range if info else None


def definition_at(
    text: str, position: Position, workspace: Workspace, suffixes: tuple[str, ...]
) -> Target | None:
    """Return where the link under *position* is defined.

    Falls back to the start of the target file when the file exists but the
    specific ID or parameter is not found in it.
    """
    link = link_at(text, position)
    if link is None or not is_checked_link(link) or not link.path.startswith("/"):
        return None
    located = workspace.locate(link.path)
    if located is None:
        return None
    path, content = located
    if is_parameter_link(link):
        found = _parameter_range(link, content)
    else:
        found = _requirement_range(link, content, suffixes)
    return Target(path, found or _FILE_START)
