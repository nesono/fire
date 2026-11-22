#!/usr/bin/env python3
"""Convert document URIs to file paths."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse


def uri_to_path(uri: str) -> Path | None:
    """Return the path of a ``file:`` URI, or ``None`` for any other scheme."""
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return None
    return Path(unquote(parsed.path))
