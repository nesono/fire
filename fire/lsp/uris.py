#!/usr/bin/env python3
"""Convert document URIs to file paths."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from urllib.parse import unquote, urlparse


def uri_to_path(uri: str) -> Path | None:
    """Return the path of a ``file:`` URI, or ``None`` for any other scheme."""
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return None
    return Path(unquote(parsed.path))


def document_overlay(documents: Mapping[str, str]) -> dict[Path, str]:
    """Map open ``file:`` documents (uri to text) to their paths."""
    paths = {uri: uri_to_path(uri) for uri in documents}
    return {path: documents[uri] for uri, path in paths.items() if path is not None}
