#!/usr/bin/env python3
"""Draft helpers for the release report format."""

from __future__ import annotations

import re
from typing import Final

import yaml

_VALID_TRACE_TYPES: Final = {"impl", "verif"}
_VALID_EXEMPTION_KINDS: Final = {"impl", "verif", "version", "todo"}
_TODO_PATTERN: Final = re.compile(r"TODO\([A-Z]+-[0-9]+\)")


def load_yaml_file(path: str) -> object:
    with open(path, "r") as handle:
        data = yaml.safe_load(handle)
    return data if data is not None else []


def _ensure_list_of_dicts(data: object, source: str) -> list[dict]:
    if data is None:
        return []
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError(f"{source}: expected a list of maps")
    return data


def parse_trace_entries(data: object, source: str) -> list[dict]:
    entries = _ensure_list_of_dicts(data, source)
    for entry in entries:
        trace_type = entry.get("type")
        if trace_type not in _VALID_TRACE_TYPES:
            raise ValueError(f"{source}: Unknown trace type '{trace_type}'")
        if not entry.get("requirement") and not entry.get("param"):
            raise ValueError(f"{source}: Trace entry missing requirement or param")
    return entries


def parse_exemptions(data: object, source: str) -> list[dict]:
    entries = _ensure_list_of_dicts(data, source)
    for entry in entries:
        if entry.get("kind") not in _VALID_EXEMPTION_KINDS:
            raise ValueError(f"{source}: Unknown exemption kind '{entry.get('kind')}'")
        if not entry.get("requirement"):
            raise ValueError(f"{source}: Exemption missing requirement")
        if not entry.get("justification"):
            raise ValueError(f"{source}: Exemption missing justification")
    return entries


def extract_todos(content: str) -> list[str]:
    return _TODO_PATTERN.findall(content)
