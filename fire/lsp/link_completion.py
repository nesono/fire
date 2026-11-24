#!/usr/bin/env python3
"""Completion inside the URL of a link: the path, ``?version=N`` and ``#anchor``.

Works for inline links (``[text](url)``) and for reference-style definition
lines (``[label]: url``). Positions are code points.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final

from lsprotocol import types as lsp

from fire.lsp.completion import Candidate
from fire.lsp.document_parser import Position, Range
from fire.lsp.index import parameters_in, requirements_in
from fire.lsp.workspace import Workspace
from fire.starlark.patterns import REQ_ID_PATTERN

_INLINE_RE: Final = re.compile(r"\[(?P<text>[^\]]*)\]\((?P<url>[^)\s]*)$")
_DEFINITION_RE: Final = re.compile(r"^ {0,3}\[(?P<text>[^\]]+)\]:[ \t]*(?P<url>\S*)$")
_URL_REST_RE: Final = re.compile(r"[^)\s]*")
_VERSION_RE: Final = re.compile(r"^version=(?P<digits>\d*)$")
_QUERY_KEY: Final = "version="
_YAML_SUFFIX: Final = ".yaml"


@dataclass(frozen=True)
class _Url:
    text: str
    start: int
    prefix: str
    rest: str


def _url_at(line: str, character: int) -> _Url | None:
    before = line[:character]
    match = _INLINE_RE.search(before) or _DEFINITION_RE.match(before)
    if match is None:
        return None
    rest = _URL_REST_RE.match(line, character)
    return _Url(
        match["text"], match.start("url"), match["url"], rest.group(0) if rest else ""
    )


def _range(line: int, start: int, end: int) -> Range:
    return Range(Position(line, start), Position(line, end))


def _path_candidates(files: Sequence[str], replace: Range) -> list[Candidate]:
    return [
        Candidate(
            label=file,
            new_text=file,
            replace=replace,
            kind=lsp.CompletionItemKind.File,
            detail=(
                "parameter file" if file.endswith(_YAML_SUFFIX) else "requirement file"
            ),
        )
        for file in files
    ]


def _name_of_link(url: _Url, path: str) -> str | None:
    """The requirement ID or parameter name the link is about, if known."""
    anchor = (url.prefix + url.rest).partition("#")[2] or None
    if path.endswith(_YAML_SUFFIX):
        return url.text[1:] if url.text.startswith("@") else anchor
    return url.text if REQ_ID_PATTERN.match(url.text) else anchor


def _version_candidates(
    url: _Url, path: str, workspace: Workspace, replace: Range
) -> list[Candidate]:
    located = workspace.locate(path)
    name = _name_of_link(url, path)
    if located is None or name is None:
        return []
    content = located[1]
    if path.endswith(_YAML_SUFFIX):
        info = parameters_in(content).get(name)
        versions = sorted(info.versions, reverse=True) if info else []
        details = ["latest"] + ["older"] * len(versions)
    else:
        requirement = requirements_in(content).get(name)
        versions = [requirement.version] if requirement and requirement.version else []
        details = ["current version"]
    return [
        Candidate(str(v), str(v), replace, lsp.CompletionItemKind.Value, detail=detail)
        for v, detail in zip(versions, details)
    ]


def _anchor_candidates(
    url: _Url, path: str, workspace: Workspace, replace: Range
) -> list[Candidate]:
    located = workspace.locate(path)
    if located is None:
        return []
    content = located[1]
    if path.endswith(_YAML_SUFFIX):
        entries = [(name, "parameter") for name in parameters_in(content)]
    else:
        entries = [
            (r.id, f"version {r.version}" if r.version else "")
            for r in requirements_in(content).values()
        ]
    linked = url.text[1:] if url.text.startswith("@") else url.text
    return [
        Candidate(
            label=name,
            new_text=name,
            replace=replace,
            kind=lsp.CompletionItemKind.Reference,
            detail=detail,
            sort_text=f"{name != linked:d}{index:04d}",
        )
        for index, (name, detail) in enumerate(entries)
    ]


def _query_candidates(
    url: _Url, line: int, cursor: int, workspace: Workspace
) -> list[Candidate]:
    path, _, query = url.prefix.partition("?")
    version = _VERSION_RE.match(query)
    if version:
        digits = version["digits"]
        replace = _range(line, cursor - len(digits), cursor)
        return _version_candidates(url, path, workspace, replace)
    if _QUERY_KEY.startswith(query):
        replace = _range(line, cursor - len(query), cursor)
        return [
            Candidate("version=", _QUERY_KEY, replace, lsp.CompletionItemKind.Property)
        ]
    return []


def link_candidates(
    text: str,
    position: Position,
    workspace: Workspace,
    files: Callable[[], Sequence[str]],
) -> list[Candidate]:
    """Complete the part of a link URL at *position*.

    *files* returns the repository-relative paths (``/dir/file``) offered for
    the path and is only called when a path is being completed; *workspace*
    reads the target to offer its versions and anchors.
    """
    lines = text.split("\n")
    if position.line >= len(lines):
        return []
    url = _url_at(lines[position.line], position.character)
    if url is None:
        return []
    line, cursor = position.line, position.character
    if "#" in url.prefix:
        path_part, _, typed = url.prefix.partition("#")
        replace = _range(line, cursor - len(typed), cursor)
        return _anchor_candidates(url, path_part.partition("?")[0], workspace, replace)
    if "?" in url.prefix:
        return _query_candidates(url, line, cursor, workspace)
    return _path_candidates(files(), _range(line, url.start, cursor))
