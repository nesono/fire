#!/usr/bin/env python3
"""Build a structured render model from parsed FIRE markdown and config.

The render model is the type-agnostic intermediate consumed by the HTML
template (Phase 2). It reuses ``parse_requirement_sections`` and
``FireConfig`` so no new parsing logic is introduced here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fire.starlark import release_report
from fire.starlark.config_models import DocumentTypeDefinition, FireConfig


@dataclass(frozen=True)
class RenderField:
    """A single metadata field with its display name and formatted values."""

    name: str
    display_name: str
    values: tuple[str, ...]

    @property
    def value(self) -> str:
        """Return the values joined for single-valued display."""
        return ", ".join(self.values)


@dataclass(frozen=True)
class RenderEntry:
    """One ``## ENTRY-ID`` section with ordered fields and body text."""

    entry_id: str
    fields: tuple[RenderField, ...]
    body: str


@dataclass(frozen=True)
class RenderDocument:
    """A whole document: its type, title, and rendered entries."""

    source_path: str
    doc_type: str
    display_name: str
    title: str
    entries: tuple[RenderEntry, ...]


def build_render_document(
    content: str, file_path: str, config: FireConfig
) -> RenderDocument:
    """Construct a :class:`RenderDocument` from markdown *content*."""
    doc_key, doc_type = _resolve_document_type(file_path, config)
    sections = release_report.parse_requirement_sections(
        content, file_path, config.known_fields()
    )
    entries = tuple(_build_entry(s, doc_type, config) for s in sections)
    return RenderDocument(
        source_path=file_path,
        doc_type=doc_key,
        display_name=doc_type.display_name,
        title=_extract_title(content, file_path),
        entries=entries,
    )


def _resolve_document_type(
    file_path: str, config: FireConfig
) -> tuple[str, DocumentTypeDefinition]:
    """Return the config key and definition for *file_path*'s suffix."""
    for key, doc_type in config.document_types.items():
        if file_path.endswith(doc_type.suffix):
            return key, doc_type
    raise ValueError(f"no document type matches '{file_path}'")


def _extract_title(content: str, file_path: str) -> str:
    """Return the first H1 heading, or the filename stem as a fallback."""
    for line in content.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return Path(file_path).name.split(".", 1)[0]


def _build_entry(
    section: dict, doc_type: DocumentTypeDefinition, config: FireConfig
) -> RenderEntry:
    """Build a :class:`RenderEntry` from a parsed *section*."""
    ordered = doc_type.required_fields + doc_type.optional_fields
    fields = tuple(
        field
        for name in ordered
        if (field := _build_field(name, section["metadata"], config)) is not None
    )
    return RenderEntry(entry_id=section["id"], fields=fields, body=section["body"])


def _build_field(name: str, metadata: dict, config: FireConfig) -> RenderField | None:
    """Build a :class:`RenderField`, or ``None`` when the value is absent."""
    field_def = config.field_definitions[name]
    raw = metadata.get(field_def.display_name.lower())
    if raw is None:
        return None
    return RenderField(name, field_def.display_name, _format_values(raw))


def _format_values(raw: object) -> tuple[str, ...]:
    """Normalize a metadata value to a tuple of display strings."""
    if isinstance(raw, list):
        return tuple(_format_scalar(v) for v in raw)
    return (_format_scalar(raw),)


def _format_scalar(value: object) -> str:
    """Format a scalar value, rendering booleans as ``true``/``false``."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
