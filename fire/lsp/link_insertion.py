#!/usr/bin/env python3
"""Insert a complete link when a requirement ID or parameter name is typed.

Typing ``[@`` offers the parameters and ``[REQ`` the requirements; choosing one
replaces what was typed with ``[name](/path?version=N#name)`` for the latest
version. Positions are code points.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Final

from lsprotocol import types as lsp

from fire.lsp.completion import Candidate
from fire.lsp.document_parser import Position, Range
from fire.lsp.link_targets import PARAMETER, REQUIREMENT, LinkTarget

_OPEN_RE: Final = re.compile(r"(?<!\])\[(?P<token>@[A-Za-z0-9_]*|[A-Z][A-Za-z0-9_-]*)$")
_TOKEN_CHAR_RE: Final = re.compile(r"[A-Za-z0-9_-]")
_EXISTING_LINK_CONTINUATION: Final = "(["


def _url(target: LinkTarget) -> str:
    query = f"?version={target.version}" if target.version is not None else ""
    return f"{target.path}{query}#{target.name}"


def _detail(target: LinkTarget) -> str:
    if target.version is None:
        return target.path
    return f"{target.path}, version {target.version}"


def _candidate(target: LinkTarget, replace: Range, prefix: str) -> Candidate:
    label = f"{prefix}{target.name}"
    return Candidate(
        label=label,
        new_text=f"[{label}]({_url(target)})",
        replace=replace,
        kind=lsp.CompletionItemKind.Reference,
        detail=_detail(target),
        sort_text=label,
        filter_text=f"[{label}",
    )


def _end_of_replacement(line: str, cursor: int) -> int | None:
    """Where the replaced text ends, or ``None`` if the cursor is in a link."""
    following = line[cursor : cursor + 1]
    if following and _TOKEN_CHAR_RE.match(following):
        return None
    if following != "]":
        return cursor
    after_bracket = line[cursor + 1 : cursor + 2]
    return (
        None
        if after_bracket and after_bracket in _EXISTING_LINK_CONTINUATION
        else cursor + 1
    )


def link_insertion_candidates(
    text: str, position: Position, targets: Callable[[], Sequence[LinkTarget]]
) -> list[Candidate]:
    """Offer complete links for the ``[@name`` or ``[REQ-ID`` typed at *position*."""
    lines = text.split("\n")
    if position.line >= len(lines):
        return []
    line, cursor = lines[position.line], position.character
    match = _OPEN_RE.search(line[:cursor])
    end = _end_of_replacement(line, cursor) if match else None
    if match is None or end is None:
        return []
    is_parameter = match["token"].startswith("@")
    replace = Range(
        Position(position.line, match.start()), Position(position.line, end)
    )
    kind, prefix = (PARAMETER, "@") if is_parameter else (REQUIREMENT, "")
    return [_candidate(t, replace, prefix) for t in targets() if t.kind == kind]
