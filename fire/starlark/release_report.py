#!/usr/bin/env python3
"""Draft helpers for the release report format."""

from __future__ import annotations

import re
from typing import Final

import yaml

from fire.starlark import markdown_common, path_common, validate_cross_references
from fire.starlark.patterns import PARAM_VERSION_SUFFIX_RE, REQ_ID_PATTERN, TODO_PATTERN

_VALID_TRACE_TYPES: Final = {"impl", "verif"}
_VALID_EXEMPTION_KINDS: Final = {"impl", "verif", "version", "todo"}


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
    return TODO_PATTERN.findall(content)


def parse_requirement_sections(content: str) -> list[dict]:
    sections: list[dict] = []
    lines = content.split("\n")
    indices: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        req_id = line[3:].strip()
        if REQ_ID_PATTERN.match(req_id):
            indices.append((i, req_id))

    for idx, (start, req_id) in enumerate(indices):
        end = indices[idx + 1][0] if idx + 1 < len(indices) else len(lines)
        section_lines = lines[start:end]

        metadata_line = validate_cross_references._extract_next_metadata_line(
            section_lines, 0
        )
        metadata = {}
        if metadata_line:
            metadata = validate_cross_references._parse_metadata_fields(
                metadata_line, req_id
            )

        body_start = 1
        if metadata_line:
            for offset, line in enumerate(section_lines[1:], start=1):
                if line.strip() == metadata_line.strip():
                    body_start = offset + 1
                    break

        body = "\n".join(section_lines[body_start:]).strip()
        sections.append(
            {
                "id": req_id,
                "metadata": metadata,
                "body": body,
                "metadata_line": metadata_line,
            }
        )

    return sections


def collect_requirement_references(section: dict) -> list[tuple[str, int | None]]:
    refs: list[tuple[str, int | None]] = []
    for req_id, path in markdown_common.extract_requirement_references(section["body"]):
        _, version = path_common.extract_version_from_url(path)
        refs.append((req_id, version))
    parent = section["metadata"].get("parent")
    if isinstance(parent, str):
        match = re.match(markdown_common.MARKDOWN_LINK_PATTERN, parent)
        if match:
            parent_id = match.group(1)
            parent_path = match.group(2)
            _, version = path_common.extract_version_from_url(parent_path)
            refs.append((parent_id, version))
    return refs


def build_param_version_map(data: object, source: str) -> dict[str, int]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{source}: expected mapping for parameter file")
    versions: dict[str, int] = {}
    for key in data:
        match = PARAM_VERSION_SUFFIX_RE.match(key)
        if not match:
            continue
        base_name = match.group(1)
        version = int(match.group(2))
        versions[base_name] = version
    return versions


def find_stale_requirement_references(
    sections: list[dict], requirement_versions: dict[str, int]
) -> list[tuple[str, str, int, int]]:
    stale: list[tuple[str, str, int, int]] = []
    for section in sections:
        refs = collect_requirement_references(section)
        for req_id, version in refs:
            if version is None:
                continue
            current = requirement_versions.get(req_id)
            if current is None:
                continue
            if current != version:
                stale.append((section["id"], req_id, version, current))
    return stale
