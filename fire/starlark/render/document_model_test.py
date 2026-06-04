#!/usr/bin/env python3
"""Tests for building the PDF render model from parsed FIRE markdown."""

import pytest

from fire.starlark.render.document_model import build_render_document

_SYSREQ = """\
# Braking System Requirements

## REQ-BRK-001

Sil: ASIL-D | Sec: true | Version: 1 | Parent: [REQ-SYS-001](/sys.sysreq.md?version=1)

The brake shall engage within 100 ms.

## REQ-BRK-002

Sil: ASIL-B | Sec: false | Version: 2

The brake shall release on command.
"""


@pytest.fixture()
def document(default_config):
    return build_render_document(_SYSREQ, "brake.sysreq.md", default_config)


class TestDocument:
    def test_doc_type_from_suffix(self, document):
        assert document.doc_type == "sysreq"

    def test_display_name(self, document):
        assert document.display_name == "System Requirement"

    def test_title_from_h1(self, document):
        assert document.title == "Braking System Requirements"

    def test_title_falls_back_to_stem(self, default_config):
        doc = build_render_document("## REQ-X\n", "brake.sysreq.md", default_config)
        assert doc.title == "brake"

    def test_source_path(self, document):
        assert document.source_path == "brake.sysreq.md"

    def test_unknown_suffix_raises(self, default_config):
        with pytest.raises(ValueError):
            build_render_document("# X\n", "notes.txt", default_config)


class TestEntries:
    def test_entry_ids(self, document):
        assert [e.entry_id for e in document.entries] == ["REQ-BRK-001", "REQ-BRK-002"]

    def test_body_excludes_metadata(self, document):
        assert document.entries[0].body == "The brake shall engage within 100 ms."

    def test_field_order_follows_config(self, document):
        names = [f.name for f in document.entries[0].fields]
        assert names == ["sil", "sec", "version", "parent"]

    def test_optional_field_omitted_when_absent(self, document):
        names = [f.name for f in document.entries[1].fields]
        assert names == ["sil", "sec", "version"]


class TestFields:
    def test_display_name_and_value(self, document):
        sil = document.entries[0].fields[0]
        assert sil.display_name == "SIL"
        assert sil.value == "ASIL-D"

    def test_bool_formatting(self, document):
        sec = document.entries[0].fields[1]
        assert sec.value == "true"

    def test_int_formatting(self, document):
        version = document.entries[0].fields[2]
        assert version.value == "1"

    def test_parent_link_value(self, document):
        parent = document.entries[0].fields[3]
        assert parent.values == ("[REQ-SYS-001](/sys.sysreq.md?version=1)",)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
