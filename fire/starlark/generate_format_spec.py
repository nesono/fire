#!/usr/bin/env python3
"""Generate FORMAT_SPECIFICATION.md from a FIRE configuration file.

The document type sections are driven by the config; shared sections
(parameters, cross-references, validation rules, etc.) are static.
"""

from __future__ import annotations

from fire.starlark.config_models import FireConfig, load_config


def _generate_field_docs(
    config: FireConfig, field_name: str, *, required: bool
) -> list[str]:
    """Generate documentation lines for a single metadata field."""
    fdef = config.field_definitions[field_name]
    lines: list[str] = []
    lines.append(f"#### `{fdef.display_name}` Field")
    lines.append("")

    if fdef.type == "enum":
        lines.append(f"**Type:** {fdef.description}")
        lines.append(f"**Required:** {'Yes' if required else 'No'}")
        lines.append("**Valid Values:**")
        lines.append("")
        for val in fdef.values:
            lines.append(f"- `{val}`")
        if fdef.allow_todo:
            lines.append("- `TODO(TICKET-ID)` where TICKET-ID matches `[A-Z]+-[0-9]+`")
        lines.append("")
    elif fdef.type == "bool":
        lines.append(f"**Type:** {fdef.description}")
        lines.append(f"**Required:** {'Yes' if required else 'No'}")
        vals = "`true`, `false`"
        if fdef.allow_todo:
            vals += ", or `TODO(TICKET-ID)`"
        lines.append(f"**Valid Values:** {vals}")
        lines.append("")
    elif fdef.type == "int":
        lines.append("**Type:** Integer")
        lines.append(f"**Required:** {'Yes' if required else 'No'}")
        constraint = "Positive integer"
        if fdef.min_value is not None:
            constraint += f" >= {fdef.min_value}"
        lines.append(f"**Valid Values:** {constraint}")
        lines.append("**Format:** Plain integer (no quotes, no decimals)")
        lines.append("")
    elif fdef.type == "parent_link":
        lines.append("**Type:** Markdown link(s) to parent requirement(s)")
        lines.append(f"**Required:** {'Yes' if required else 'No'}")
        lines.append("**Format:**")
        lines.append("")
        lines.append(
            "- Single parent: `Parent: [REQ-ID](/path/to/file.md?version=N#REQ-ID)`"
        )
        if fdef.allow_multiple:
            lines.append("- Multiple parents: Multi-line with `|` continuation")
        lines.append("")
        lines.append("Each parent link must:")
        lines.append("")
        lines.append("- Be a Markdown link: `[text](url)`")
        lines.append("- Use a repository-relative path (starting with `/`)")
        lines.append("- Include version query parameter: `?version=N`")
        lines.append("- Include anchor to requirement ID: `#REQ-ID`")
        if fdef.allow_todo:
            lines.append("- Or use a TODO placeholder: `TODO(TICKET-ID)`")
        lines.append("")

    return lines


def _generate_metadata_format(config: FireConfig, doc_type_name: str) -> str:
    """Generate the example metadata line for a document type."""
    doc_type = config.document_types[doc_type_name]
    all_fields = doc_type.required_fields + doc_type.optional_fields
    parts = []
    for fname in all_fields:
        fdef = config.field_definitions[fname]
        parts.append(f"{fdef.display_name}: <{fname}-value>")
    return " | ".join(parts)


def _generate_document_type_section(
    config: FireConfig, doc_type_name: str
) -> list[str]:
    """Generate the full section for one document type."""
    doc_type = config.document_types[doc_type_name]
    lines: list[str] = []

    lines.append(f"## {doc_type.display_name} (`{doc_type.suffix}`)")
    lines.append("")
    if doc_type.description:
        lines.append(doc_type.description)
        lines.append("")

    lines.append("### Metadata Fields")
    lines.append("")

    # Required fields metadata line
    req_parts = []
    for fname in doc_type.required_fields:
        fdef = config.field_definitions[fname]
        req_parts.append(f"{fdef.display_name}: <{fname}-value>")
    if req_parts:
        lines.append("Required metadata line format:")
        lines.append("")
        lines.append("```text")
        lines.append(" | ".join(req_parts))
        lines.append("```")
        lines.append("")

    # Full metadata line with optional fields
    if doc_type.optional_fields:
        lines.append("With optional fields:")
        lines.append("")
        lines.append("```text")
        lines.append(_generate_metadata_format(config, doc_type_name))
        lines.append("```")
        lines.append("")

    lines.append("Fields must be separated by `|` (space-pipe-space).")
    lines.append("")

    # Document each field
    required_set = set(doc_type.required_fields)
    for fname in doc_type.required_fields + doc_type.optional_fields:
        lines.extend(
            _generate_field_docs(config, fname, required=fname in required_set)
        )

    return lines


def generate_format_spec(config: FireConfig) -> str:
    """Generate the full FORMAT_SPECIFICATION.md content."""
    lines: list[str] = []

    lines.append("# FIRE Format Specification")
    lines.append("")
    lines.append(
        "This document specifies the format for all input files "
        "used in the FIRE requirements management system."
    )
    lines.append("")
    lines.append(
        "**Note:** This file is auto-generated from the FIRE configuration. "
        "Do not edit manually."
    )
    lines.append("")

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("")
    toc_idx = 1
    for doc_type in config.document_types.values():
        # Generate anchor from display name
        anchor = (
            doc_type.display_name.lower().replace(" ", "-")
            + "-"
            + doc_type.suffix.replace(".", "")
        )
        lines.append(
            f"{toc_idx}. [{doc_type.display_name} (`{doc_type.suffix}`)](#{anchor})"
        )
        toc_idx += 1
    lines.append(f"{toc_idx}. [Parameter Files (`.yaml`)](#parameter-files-yaml)")
    toc_idx += 1
    lines.append(f"{toc_idx}. [Cross-References](#cross-references)")
    toc_idx += 1
    lines.append(f"{toc_idx}. [Validation Rules](#validation-rules)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Document type sections (config-driven)
    for doc_type_name in config.document_types:
        lines.extend(_generate_document_type_section(config, doc_type_name))
        lines.append("---")
        lines.append("")

    # Requirement ID format (shared)
    lines.append("## Requirement ID Format")
    lines.append("")
    lines.append("**Pattern:** `^[A-Z][A-Z0-9_-]+$`")
    lines.append("")
    lines.append("- Must start with an uppercase letter")
    lines.append("- May contain uppercase letters, digits, underscores, and hyphens")
    lines.append("- No lowercase letters allowed")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Parameter Files section (static)
    lines.extend(_PARAMETER_FILES_SECTION)
    lines.append("")

    # Cross-References section (static)
    lines.extend(_CROSS_REFERENCES_SECTION)
    lines.append("")

    # Validation Rules section (static)
    lines.extend(_VALIDATION_RULES_SECTION)
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Static sections that don't change with configuration
# ---------------------------------------------------------------------------

_PARAMETER_FILES_SECTION = """\
## Parameter Files (`.yaml`)

Parameter files are YAML documents that define typed parameters with units
and descriptions. Parameters are versioned and can be referenced from
requirements.

### Parameter Naming

**Pattern:** `^[a-z][a-z0-9_]*_v[1-9][0-9]*$`

- Parameter name must be lowercase snake_case
- Must end with version suffix: `_v<N>` where N >= 1

### Version Constraints

- A parameter can have at most **2 versions** (e.g., `_v1` and `_v2`)
- Versions must be **consecutive** (no gaps)

### Scalar Parameters

Scalar parameters have a single value with a type, unit, and description.
Types are automatically inferred from values: `bool`, `i64` (int),
`f64` (float), `string`.

**Required fields:** `value`, `unit`, `description`

### Table Parameters

Table parameters contain tabular data with typed columns.

**Required fields:** `type: table`, `description`, `columns`, `rows`

Column types are inferred from the first row. All values in a column must
have the same type.

---""".split(
    "\n"
)

_CROSS_REFERENCES_SECTION = """\
## Cross-References

### Requirement-to-Requirement References

**Format:** `[REQ-ID](/path/to/file.md?version=N#REQ-ID)`

- Path: Repository-relative (starts with `/`)
- Query parameter: `?version=N`
- Anchor: `#REQ-ID`

### Requirement-to-Parameter References

**Format:** `[@param_name](/path/to/params.yaml?version=N#param_name)`

- Link text: `@` prefix + parameter name (without version suffix)
- Path: Repository-relative path to YAML file
- Anchor: base name without version suffix

### TODO Placeholders

**Pattern:** `TODO(TICKET-ID)` where TICKET-ID matches `[A-Z]+-[0-9]+`

---""".split(
    "\n"
)

_VALIDATION_RULES_SECTION = """\
## Validation Rules

1. **Requirement IDs** must match `^[A-Z][A-Z0-9_-]+$`
2. **Metadata lines** must follow the document type's field requirements
3. **SIL/Sec/Version** values must match their field type constraints
4. **Parent references** must be valid markdown links with repository-relative paths
5. **Parameter names** must match `^[a-z][a-z0-9_]*_v[1-9][0-9]*$`
6. **Parameter versions** must be consecutive with at most 2 versions
7. **Cross-references** must use repository-relative paths with `?version=N`
8. **TODO placeholders** must use `TODO(KEY-1234)` format""".split(
    "\n"
)


def main() -> int:
    """CLI entrypoint for Bazel."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate FORMAT_SPECIFICATION.md from FIRE config"
    )
    parser.add_argument("--config", default=None, help="Path to fire_config.yaml")
    parser.add_argument("--out", required=True, help="Output file path")
    args = parser.parse_args()

    config = load_config(args.config)
    content = generate_format_spec(config)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
