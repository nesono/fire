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
    """Load YAML from disk and normalize empty files to an empty list."""
    with open(path, "r") as handle:
        data = yaml.safe_load(handle)
    return data if data is not None else []


def load_json_file(path: str) -> object:
    """Load JSON from disk."""
    import json

    with open(path, "r") as handle:
        return json.load(handle)


def _ensure_list_of_dicts(data: object, source: str) -> list[dict]:
    if data is None:
        return []
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError(f"{source}: expected a list of maps")
    return data


def parse_source_traceability_data(data: object, source: str) -> list[dict]:
    """Normalize source_traceability JSON into release report trace entries."""
    if not isinstance(data, dict):
        raise ValueError(f"{source}: expected JSON object")

    entries: list[dict] = []
    for trace_type, key in [("impl", "implements"), ("verif", "verifies")]:
        mapping = data.get(key, {})
        if not isinstance(mapping, dict):
            raise ValueError(f"{source}: expected '{key}' mapping")
        for source_file, refs in mapping.items():
            if not isinstance(refs, list):
                raise ValueError(f"{source}: '{key}' values must be lists")
            for ref in refs:
                if not isinstance(ref, dict):
                    raise ValueError(f"{source}: '{key}' entries must be objects")
                req_id = ref.get("req_id")
                version = ref.get("version")
                if not isinstance(req_id, str):
                    raise ValueError(f"{source}: missing req_id in '{key}' entry")
                if not isinstance(version, int):
                    raise ValueError(f"{source}: missing version in '{key}' entry")
                entries.append(
                    {
                        "type": trace_type,
                        "requirement": req_id,
                        "source": source_file,
                        "version": version,
                    }
                )

    return entries


def parse_exemptions(data: object, source: str) -> list[dict]:
    """Validate exemptions and require justification for every excluded requirement."""
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
    """Return all TODO ticket markers embedded in the given text."""
    return TODO_PATTERN.findall(content)


def parse_requirement_sections(content: str) -> list[dict]:
    """Split a requirements file into sections with parsed inline metadata."""
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
    """Collect requirement references and their tracked versions from a section."""
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


def collect_param_references(section: dict) -> list[tuple[str, int | None]]:
    """Collect parameter references and their tracked versions from a section."""
    refs: list[tuple[str, int | None]] = []
    for param_name, path in markdown_common.extract_param_references(section["body"]):
        _, version = path_common.extract_version_from_url(path)
        refs.append((param_name, version))
    return refs


def build_param_version_map(data: object, source: str) -> dict[str, int]:
    """Extract latest parameter versions from a parameter YAML mapping."""
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
    """Build a requirement id to version map from parsed sections."""
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


def find_stale_requirement_references(
    sections: list[dict], requirement_versions: dict[str, int]
) -> list[tuple[str, str, int, int]]:
    """Find requirement references that track an outdated version."""
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


def find_stale_param_references(
    sections: list[dict], param_versions: dict[str, int]
) -> list[tuple[str, str, int, int]]:
    """Find parameter references that track an outdated version."""
    stale: list[tuple[str, str, int, int]] = []
    for section in sections:
        refs = collect_param_references(section)
        for param_name, version in refs:
            if version is None:
                continue
            current = param_versions.get(param_name)
            if current is None:
                continue
            if current != version:
                stale.append((section["id"], param_name, version, current))
    return stale


def _load_yaml_list(path: str) -> list[dict]:
    data = load_yaml_file(path)
    return _ensure_list_of_dicts(data, path)


def load_trace_entries(paths: list[str]) -> list[dict]:
    """Load and validate source_traceability JSON files."""
    entries: list[dict] = []
    for path in paths:
        data = load_json_file(path)
        entries.extend(parse_source_traceability_data(data, path))
    return entries


def load_exemptions(path: str | None) -> list[dict]:
    """Load exemptions if provided, otherwise return an empty list."""
    if path is None:
        return []
    data = load_yaml_file(path)
    return parse_exemptions(data, path)


def build_trace_index(entries: list[dict]) -> dict[str, dict[str, list[dict]]]:
    """Index trace entries by type and requirement/parameter for quick lookup."""
    index: dict[str, dict[str, list[dict]]] = {"impl": {}, "verif": {}}
    for entry in entries:
        trace_type = entry["type"]
        req_id = entry.get("requirement")
        param = entry.get("param")
        key = req_id if req_id else f"param:{param}"
        index[trace_type].setdefault(key, []).append(entry)
    return index


def find_stale_trace_versions(
    entries: list[dict],
    requirement_versions: dict[str, int],
    param_versions: dict[str, int],
) -> list[tuple[str, str, int, int]]:
    """Find traces that reference a version older than the current source."""
    stale: list[tuple[str, str, int, int]] = []
    for entry in entries:
        version = entry.get("version")
        if not isinstance(version, int):
            continue
        if entry.get("requirement"):
            req_id = entry["requirement"]
            current = requirement_versions.get(req_id)
            if current is not None and current != version:
                stale.append((req_id, "requirement", version, current))
        if entry.get("param"):
            param = entry["param"]
            current = param_versions.get(param)
            if current is not None and current != version:
                stale.append((param, "param", version, current))
    return stale


def _has_exemption(exemptions: list[dict], req_id: str, kind: str) -> bool:
    for entry in exemptions:
        if entry.get("requirement") == req_id and entry.get("kind") == kind:
            return True
    return False


def _format_exemptions(exemptions: list[dict]) -> list[str]:
    if not exemptions:
        return ["- None"]
    lines = []
    for entry in exemptions:
        owner = entry.get("owner", "-")
        expires = entry.get("expires", "-")
        lines.append(
            f"- **{entry['requirement']}** ({entry['kind']}): "
            f"{entry['justification']} (owner: {owner}, expires: {expires})"
        )
    return lines


def _sanitize_mermaid_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def build_mermaid_graph(
    sections: list[dict],
    impl_index: dict[str, list[dict]],
    verif_index: dict[str, list[dict]],
) -> list[str]:
    """Render a Mermaid graph of requirement, parameter, impl, and verif links."""
    lines = ["```mermaid", "graph LR"]
    for section in sections:
        req_id = section["id"]
        req_node = f"req_{_sanitize_mermaid_id(req_id)}"
        lines.append(f'    {req_node}["{req_id}"]')
        for param_name, _ in collect_param_references(section):
            param_node = f"param_{_sanitize_mermaid_id(param_name)}"
            lines.append(f'    {param_node}["param:{param_name}"]')
            lines.append(f"    {req_node} --> {param_node}")
        for entry in impl_index.get(req_id, []):
            source = entry.get("source", "impl")
            impl_node = f"impl_{_sanitize_mermaid_id(source)}"
            lines.append(f'    {impl_node}["impl:{source}"]')
            lines.append(f"    {req_node} --> {impl_node}")
        for entry in verif_index.get(req_id, []):
            source = entry.get("source", "verif")
            verif_node = f"verif_{_sanitize_mermaid_id(source)}"
            lines.append(f'    {verif_node}["verif:{source}"]')
            lines.append(f"    {req_node} --> {verif_node}")
    lines.append("```")
    return lines


def generate_release_report(
    requirement_paths: list[str],
    parameter_paths: list[str],
    source_trace_paths: list[str],
    exemptions_path: str | None,
    product_name: str,
) -> str:
    """Build the full release readiness report from requirements and traces."""
    sections: list[dict] = []
    todos: list[tuple[str, str]] = []
    bare_todos: list[str] = []
    for path in requirement_paths:
        if not path.endswith(".md"):
            continue
        content = open(path, "r").read()
        sections.extend(parse_requirement_sections(content))
        for todo in extract_todos(content):
            todos.append((path, todo))
        bare_todos.extend(
            validate_cross_references.validate_no_bare_todos(content, path)
        )

    requirement_versions = build_requirement_version_map(sections)

    param_maps = []
    for path in parameter_paths:
        if not (path.endswith(".yaml") or path.endswith(".yml")):
            continue
        data = load_yaml_file(path)
        param_maps.append(build_param_version_map(data, path))
        content = open(path, "r").read()
        for todo in extract_todos(content):
            todos.append((path, todo))
        bare_todos.extend(
            validate_cross_references.validate_no_bare_todos(content, path)
        )

    param_versions = merge_param_versions(param_maps)

    stale_req_refs = find_stale_requirement_references(sections, requirement_versions)
    stale_param_refs = find_stale_param_references(sections, param_versions)

    all_trace_entries = load_trace_entries(source_trace_paths)
    trace_index = build_trace_index(all_trace_entries)

    stale_trace_versions = find_stale_trace_versions(
        all_trace_entries, requirement_versions, param_versions
    )

    exemptions = load_exemptions(exemptions_path)

    missing_impl: list[str] = []
    missing_verif: list[str] = []
    for section in sections:
        req_id = section["id"]
        if req_id not in trace_index["impl"]:
            missing_impl.append(req_id)
        if req_id not in trace_index["verif"]:
            missing_verif.append(req_id)

    readiness_issues: list[str] = []
    for req_id in missing_impl:
        if not _has_exemption(exemptions, req_id, "impl"):
            readiness_issues.append(f"Missing implementation trace for {req_id}")
    for req_id in missing_verif:
        if not _has_exemption(exemptions, req_id, "verif"):
            readiness_issues.append(f"Missing verification trace for {req_id}")
    if stale_req_refs:
        readiness_issues.append("Stale requirement references")
    if stale_param_refs:
        readiness_issues.append("Stale parameter references")
    if stale_trace_versions:
        readiness_issues.append("Stale trace versions")
    if todos or bare_todos:
        readiness_issues.append("Open TODOs")

    status = "PASS" if not readiness_issues else "FAIL"
    lines: list[str] = [f"# Release Readiness Report: {product_name}", ""]
    lines.append("## Release Readiness Summary")
    lines.append("")
    lines.append(f"- Status: **{status}**")
    if readiness_issues:
        lines.append("- Issues:")
        for issue in readiness_issues:
            lines.append(f"  - {issue}")
    lines.append("")

    lines.append("## Version Consistency")
    lines.append("")
    if stale_req_refs:
        lines.append("### Stale Requirement References")
        for req_id, parent_id, tracked, current in stale_req_refs:
            lines.append(
                f"- **{req_id}** tracks **{parent_id}** v{tracked}, current v{current}"
            )
        lines.append("")
    if stale_param_refs:
        lines.append("### Stale Parameter References")
        for req_id, param, tracked, current in stale_param_refs:
            lines.append(
                f"- **{req_id}** tracks **{param}** v{tracked}, current v{current}"
            )
        lines.append("")
    if stale_trace_versions:
        lines.append("### Stale Trace Versions")
        for item_id, kind, tracked, current in stale_trace_versions:
            lines.append(
                f"- **{item_id}** ({kind}) tracks v{tracked}, current v{current}"
            )
        lines.append("")
    if not stale_req_refs and not stale_param_refs and not stale_trace_versions:
        lines.append("- No stale versions found.")
        lines.append("")

    lines.append("## TODO Inventory")
    lines.append("")
    if todos:
        for path, todo in todos:
            lines.append(f"- {path}: {todo}")
    else:
        lines.append("- None")
    if bare_todos:
        lines.append("")
        lines.append("### Bare TODOs")
        for error in bare_todos:
            lines.append(f"- {error}")
    lines.append("")

    lines.append("## Implementation & Verification Coverage")
    lines.append("")
    if missing_impl:
        lines.append("### Missing Implementation Traces")
        for req_id in missing_impl:
            lines.append(f"- {req_id}")
        lines.append("")
    if missing_verif:
        lines.append("### Missing Verification Traces")
        for req_id in missing_verif:
            lines.append(f"- {req_id}")
        lines.append("")
    if not missing_impl and not missing_verif:
        lines.append("- All requirements have implementation and verification traces.")
        lines.append("")

    lines.append("## Traceability Graph")
    lines.append("")
    lines.extend(
        build_mermaid_graph(sections, trace_index["impl"], trace_index["verif"])
    )
    lines.append("")

    lines.append("## Exemptions")
    lines.append("")
    lines.extend(_format_exemptions(exemptions))
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    """CLI entrypoint for Bazel to write the report to the output file."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate release readiness report")
    parser.add_argument("--requirements", action="append", required=True)
    parser.add_argument("--params", action="append", default=[])
    parser.add_argument("--source-traces", action="append", default=[])
    parser.add_argument("--exemptions")
    parser.add_argument("--product", default="Product")
    parser.add_argument("--out", required=True)

    args = parser.parse_args()

    report = generate_release_report(
        requirement_paths=args.requirements,
        parameter_paths=args.params,
        source_trace_paths=args.source_traces,
        exemptions_path=args.exemptions,
        product_name=args.product,
    )
    with open(args.out, "w") as handle:
        handle.write(report)
        handle.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
