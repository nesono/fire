#!/usr/bin/env python3
"""Draft helpers for the release report format."""

from __future__ import annotations

import re
from typing import Final

from fire.starlark import (
    file_io_common,
    markdown_common,
    metadata_parsing,
    path_common,
    validate_cross_references,
)
from fire.starlark.config_models import (
    LEGACY_COVERAGE,
    DocumentTypeDefinition,
    FireConfig,
    load_config,
)
from fire.starlark.patterns import REQ_ID_PATTERN, TODO_PATTERN
from fire.starlark.version_tracking import (
    build_param_version_map,
    build_requirement_version_map,
    merge_param_versions,
)

_VALID_TRACE_TYPES: Final = {"impl", "verif"}


def load_yaml_file(path: str) -> object:
    """Load YAML from disk and normalize empty files to an empty list."""
    data, error = file_io_common.load_yaml_safe(path)
    if error:
        raise OSError(error)
    return data if data is not None else []


def load_json_file(path: str) -> object:
    """Load JSON from disk."""
    data, error = file_io_common.load_json_safe(path)
    if error:
        raise OSError(error)
    return data


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


def extract_todos(content: str) -> list[str]:
    """Return all TODO ticket markers embedded in the given text."""
    return TODO_PATTERN.findall(content)


def parse_requirement_sections(
    content: str,
    file_path: str,
    known_fields: list[str] | None = None,
) -> list[dict]:
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

        metadata_line = metadata_parsing.extract_next_metadata_line(
            section_lines, 0, known_fields
        )
        metadata = {}
        if metadata_line:
            metadata = metadata_parsing.parse_metadata_fields(metadata_line, req_id)

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
                "file_path": file_path,
                "line": start + 1,
            }
        )

    return sections


def collect_parent_references(
    section: dict,
) -> list[tuple[str, int | None, str | None]]:
    """Collect the requirements a section lists as ``Parent`` with their versions."""
    refs: list[tuple[str, int | None, str | None]] = []
    parent = section["metadata"].get("parent")
    for parent_value in parent if isinstance(parent, list) else []:
        match = re.match(markdown_common.MARKDOWN_LINK_PATTERN, str(parent_value))
        if match:
            _, version = path_common.extract_version_from_url(match.group(2))
            refs.append((match.group(1), version, match.group(2)))
    return refs


def collect_requirement_references(
    section: dict,
) -> list[tuple[str, int | None, str | None]]:
    """Collect requirement references and their tracked versions from a section."""
    refs: list[tuple[str, int | None, str | None]] = []
    for req_id, path in markdown_common.extract_requirement_references(section["body"]):
        _, version = path_common.extract_version_from_url(path)
        refs.append((req_id, version, path))
    return refs + collect_parent_references(section)


def collect_param_references(
    section: dict,
) -> list[tuple[str, int | None, str | None]]:
    """Collect parameter references and their tracked versions from a section."""
    refs: list[tuple[str, int | None, str | None]] = []
    for param_name, path in markdown_common.extract_param_references(section["body"]):
        _, version = path_common.extract_version_from_url(path)
        refs.append((param_name, version, path))
    return refs


def find_stale_requirement_references(
    sections: list[dict], requirement_versions: dict[str, int]
) -> list[tuple[str, str, int, int]]:
    """Find requirement references that track an outdated version."""
    stale: list[tuple[str, str, int, int]] = []
    for section in sections:
        refs = collect_requirement_references(section)
        for req_id, version, _ in refs:
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
        for param_name, version, _ in refs:
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


def _document_type_for(path: str, config: FireConfig) -> DocumentTypeDefinition | None:
    matches = [dt for dt in config.document_types.values() if path.endswith(dt.suffix)]
    return max(matches, key=lambda dt: len(dt.suffix), default=None)


def _required_coverage(section: dict, config: FireConfig) -> list[str]:
    doc_type = _document_type_for(section["file_path"], config)
    return doc_type.required_coverage() if doc_type else list(LEGACY_COVERAGE)


def find_missing_coverage(
    sections: list[dict],
    trace_index: dict[str, dict[str, list[dict]]],
    config: FireConfig,
) -> dict[str, list[dict]]:
    """Find the requirements that lack the coverage their document type requires."""
    parented = {pid for s in sections for pid, _, _ in collect_parent_references(s)}
    covered = {
        "child": parented,
        "implementation": set(trace_index["impl"]),
        "verification": set(trace_index["verif"]),
    }
    missing: dict[str, list[dict]] = {kind: [] for kind in covered}
    for section in sections:
        for kind in _required_coverage(section, config):
            if section["id"] not in covered[kind]:
                missing[kind].append(section)
    return missing


def _required_coverage_lines(config: FireConfig) -> list[str]:
    lines = ["### Required Coverage", ""]
    for doc_type in config.document_types.values():
        kinds = ", ".join(doc_type.required_coverage()) or "none"
        lines.append(f"- {doc_type.display_name} (`{doc_type.suffix}`): {kinds}")
    lines.append(f"- Other files: {', '.join(LEGACY_COVERAGE)}")
    lines.append("")
    return lines


def _missing_coverage_lines(title: str, sections: list[dict]) -> list[str]:
    lines = [f"### {title}"]
    for section in sections:
        lines.append(f"- [{section['id']}]({section['file_path']}#{section['id']})")
    lines.append("")
    return lines


def _find_duplicate_requirement_ids(sections: list[dict]) -> dict[str, list[str]]:
    return validate_cross_references.find_duplicate_ids(
        [(s["id"], f"{s['file_path']}:{s['line']}") for s in sections]
    )


def _duplicate_id_section(duplicates: dict[str, list[str]]) -> list[str]:
    lines = ["## Requirement ID Uniqueness", ""]
    for req_id, locations in duplicates.items():
        lines.append(f"- **{req_id}** is defined at: {', '.join(locations)}")
    if not duplicates:
        lines.append("- All requirement IDs are unique.")
    lines.append("")
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
        for param_name, _, _ in collect_param_references(section):
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
    product_name: str,
    config: FireConfig | None = None,
) -> str:
    """Build the full release readiness report from requirements and traces."""
    known_fields = config.known_fields() if config else None
    sections: list[dict] = []
    todos: list[tuple[str, str]] = []
    bare_todos: list[str] = []
    for path in requirement_paths:
        if not path.endswith(".md"):
            continue
        with open(path) as f:
            content = f.read()
        sections.extend(parse_requirement_sections(content, path, known_fields))
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
        with open(path) as f:
            content = f.read()
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

    coverage_config = config if config is not None else load_config()
    missing = find_missing_coverage(sections, trace_index, coverage_config)
    missing_impl = missing["implementation"]
    missing_verif = missing["verification"]
    missing_child = missing["child"]

    duplicate_ids = _find_duplicate_requirement_ids(sections)

    readiness_issues: list[str] = []
    if duplicate_ids:
        readiness_issues.append("Duplicate requirement IDs")
    if missing_impl:
        readiness_issues.append("Missing implementation traces")
    if missing_verif:
        readiness_issues.append("Missing verification traces")
    if missing_child:
        readiness_issues.append("Missing child requirements")
    if stale_req_refs:
        readiness_issues.append("Stale requirement references")
    if stale_param_refs:
        readiness_issues.append("Stale parameter references")
    if stale_trace_versions:
        readiness_issues.append("Stale trace versions")
    if todos or bare_todos:
        readiness_issues.append("Open TODOs")

    status = "READY FOR RELEASE" if not readiness_issues else "NOT READY FOR RELEASE"
    lines: list[str] = [f"# Release Readiness Report: {product_name}", ""]
    lines.append("## Release Readiness Summary")
    lines.append("")
    lines.append(f"**Status: {status}**")
    lines.append("")

    stale_total = (
        len(stale_req_refs) + len(stale_param_refs) + len(stale_trace_versions)
    )

    # Show issues prominently if they exist
    if readiness_issues:
        lines.append("### Issues Found")
        lines.append("")
        if duplicate_ids:
            lines.append(
                f"- ⚠️  Duplicate requirement IDs: **{len(duplicate_ids)}** "
                f"([details](#requirement-id-uniqueness))"
            )
        if len(missing_impl) > 0:
            lines.append(
                f"- ⚠️  Missing implementation traces: **{len(missing_impl)}** "
                f"([details](#missing-implementation-traces))"
            )
        if len(missing_verif) > 0:
            lines.append(
                f"- ⚠️  Missing verification traces: **{len(missing_verif)}** "
                f"([details](#missing-verification-traces))"
            )
        if missing_child:
            lines.append(
                f"- ⚠️  Missing child requirements: **{len(missing_child)}** "
                f"([details](#missing-child-requirements))"
            )
        if stale_total > 0:
            lines.append(
                f"- ⚠️  Stale references: **{stale_total}** "
                f"([details](#version-consistency))"
            )
        if todos:
            lines.append(
                f"- ⚠️  Open TODOs: **{len(todos)}** " f"([details](#todo-inventory))"
            )
        lines.append("")
    else:
        lines.append("✓ No issues found - all checks passed")
        lines.append("")

    lines.append("## Version Consistency")
    lines.append("")
    total_versioned_refs = (
        sum(
            1
            for section in sections
            for _, version, _ in collect_requirement_references(section)
            if version is not None
        )
        + sum(
            1
            for section in sections
            for _, version, _ in collect_param_references(section)
            if version is not None
        )
        + sum(1 for entry in all_trace_entries if isinstance(entry.get("version"), int))
    )
    consistent_refs = total_versioned_refs - stale_total

    if stale_total > 0:
        lines.append(
            f"- ⚠️  **Found {stale_total} stale reference(s) that need updating**"
        )
        lines.append(f"- ✓ {consistent_refs} reference(s) are consistent")
    else:
        lines.append(f"- ✓ All {consistent_refs} versioned references are consistent")
    lines.append("")
    if stale_req_refs:
        lines.append("### Stale Requirement References")
        for req_id, parent_id, tracked, current in stale_req_refs:
            section = next(s for s in sections if s["id"] == req_id)
            source_link = f"{section['file_path']}#{req_id}"
            dest_link = None
            for ref_id, version, path in collect_requirement_references(section):
                if ref_id == parent_id and version == tracked and path:
                    dest_link = path
                    break
            lines.append(
                f"- **{req_id}** tracks **{parent_id}** v{tracked}, current v{current} "
                f"(source: [{req_id}]({source_link}), dest: "
                f"[{parent_id}]({dest_link or parent_id}))"
            )
        lines.append("")
    if stale_param_refs:
        lines.append("### Stale Parameter References")
        for req_id, param, tracked, current in stale_param_refs:
            section = next(s for s in sections if s["id"] == req_id)
            source_link = f"{section['file_path']}#{req_id}"
            dest_link = None
            for param_name, version, path in collect_param_references(section):
                if param_name == param and version == tracked and path:
                    dest_link = path
                    break
            lines.append(
                f"- **{req_id}** tracks **{param}** v{tracked}, current v{current} "
                f"(source: [{req_id}]({source_link}), dest: "
                f"[{param}]({dest_link or param}))"
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

    lines.extend(_duplicate_id_section(duplicate_ids))

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

    lines.append("## Coverage")
    lines.append("")
    lines.extend(_required_coverage_lines(coverage_config))
    for title, found in (
        ("Missing Implementation Traces", missing_impl),
        ("Missing Verification Traces", missing_verif),
        ("Missing Child Requirements", missing_child),
    ):
        if found:
            lines.extend(_missing_coverage_lines(title, found))
    if not (missing_impl or missing_verif or missing_child):
        lines.append("- All requirements meet the coverage required by their type.")
        lines.append("")

    lines.append("## Traceability Graph")
    lines.append("")
    lines.extend(
        build_mermaid_graph(sections, trace_index["impl"], trace_index["verif"])
    )
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    """CLI entrypoint for Bazel to write the report to the output file."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate release readiness report")
    parser.add_argument("--requirements", action="append", required=True)
    parser.add_argument("--params", action="append", default=[])
    parser.add_argument("--source-traces", action="append", default=[])
    parser.add_argument("--product", default="Product")
    parser.add_argument("--config", default=None, help="Path to fire_config.yaml")
    parser.add_argument("--out", required=True)

    args = parser.parse_args()

    config = load_config(args.config)

    report = generate_release_report(
        requirement_paths=args.requirements,
        parameter_paths=args.params,
        source_trace_paths=args.source_traces,
        product_name=args.product,
        config=config,
    )
    with open(args.out, "w") as handle:
        handle.write(report)
        handle.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
