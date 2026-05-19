#!/usr/bin/env python3
"""Helpers for tracking parameter and requirement versions across files.

These utilities build maps from parsed YAML/section data and find references
whose tracked version no longer matches the current one. They are kept
separate from ``release_report`` so they can be unit-tested in isolation
and reused without dragging in the full report generator.
"""

from __future__ import annotations

from fire.starlark.patterns import PARAM_VERSION_SUFFIX_RE


def build_param_version_map(data: object, source: str) -> dict[str, int]:
    """Extract the latest parameter version for each base name from a YAML mapping.

    Args:
        data: Parsed YAML data (typically a dict of ``"<name>_v<N>"`` keys).
        source: Source path used only for error messages.

    Returns:
        A dict mapping base name to its highest declared version.

    Raises:
        ValueError: If *data* is not a mapping (and not ``None``).
    """
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


def build_requirement_version_map(sections: list[dict]) -> dict[str, int]:
    """Build a requirement-id-to-version map from parsed sections.

    Each section is a dict with at least ``"id"`` and ``"metadata"`` keys.
    Sections without an integer ``version`` in their metadata are skipped.
    """
    versions: dict[str, int] = {}
    for section in sections:
        version = section["metadata"].get("version")
        if isinstance(version, int):
            versions[section["id"]] = version
    return versions


def merge_param_versions(maps: list[dict[str, int]]) -> dict[str, int]:
    """Merge parameter version maps by taking the highest version per name."""
    merged: dict[str, int] = {}
    for version_map in maps:
        for name, version in version_map.items():
            current = merged.get(name)
            if current is None or version > current:
                merged[name] = version
    return merged
