#!/usr/bin/env python3
"""Diagnostic types shared by the language-server rule modules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from fire.lsp.document_parser import Range


class Severity(IntEnum):
    """Severity values as defined by the Language Server Protocol."""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass(frozen=True)
class Diagnostic:
    range: Range
    severity: Severity
    code: str
    message: str


def error(range_: Range, code: str, message: str) -> Diagnostic:
    return Diagnostic(range_, Severity.ERROR, code, message)
