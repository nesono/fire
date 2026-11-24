#!/usr/bin/env python3
"""A cached index of the parameter and requirement links in requirement files."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from lsprotocol import types as lsp

from fire.lsp.conversion import to_lsp_range
from fire.lsp.document_parser import Link, parse_links
from fire.lsp.document_types import DocumentTypes
from fire.lsp.file_index import FileIndex
from fire.lsp.link_diagnostics import is_checked_link, is_parameter_link

PARAMETER = "parameter"
REQUIREMENT = "requirement"


@dataclass(frozen=True)
class IndexedLink:
    location: lsp.Location
    path: str
    kind: str
    name: str
    version: int | None


def identify(link: Link) -> tuple[str, str]:
    """Return ``(kind, name)`` of what *link* points at."""
    if is_parameter_link(link):
        return PARAMETER, link.anchor or link.text[1:]
    return REQUIREMENT, link.text


class LinkIndex(FileIndex[IndexedLink]):
    """Indexes links with repository-relative paths in requirement files."""

    def __init__(self, root: Path, types: DocumentTypes) -> None:
        super().__init__(root, types.is_document)

    def links(self, overlay: Mapping[Path, str]) -> list[IndexedLink]:
        """Return all indexed links, ordered by file then position."""
        return self.items(overlay)

    def _parse(self, path: Path, text: str) -> list[IndexedLink]:
        lines = text.split("\n")
        uri = path.as_uri()
        return [
            _indexed(link, uri, lines)
            for link in parse_links(text)
            if is_checked_link(link) and link.path.startswith("/")
        ]


def _indexed(link: Link, uri: str, lines: list[str]) -> IndexedLink:
    kind, name = identify(link)
    return IndexedLink(
        location=lsp.Location(uri, to_lsp_range(link.span, lines)),
        path=link.path,
        kind=kind,
        name=name,
        version=link.version,
    )
