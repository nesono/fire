#!/usr/bin/env python3
"""Tests for deciding which files are FIRE documents and of which type."""

import pytest

from fire.lsp.document_types import (
    DocumentTypes,
    GlobRule,
    glob_to_regex,
    parse_glob_rule,
)
from fire.starlark.config_models import load_config

_TYPES = DocumentTypes.from_config(load_config())


class TestSuffixRules:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("reqs/a.sysreq.md", "sysreq"),
            ("a.swreq.md", "swreq"),
            ("a/b/c.regreq.md", "regreq"),
            ("README.md", None),
            ("params.yaml", None),
        ],
    )
    def test_type_of(self, path, expected):
        assert _TYPES.type_of(path) == expected

    def test_leading_slash_is_ignored(self):
        assert _TYPES.type_of("/reqs/a.sysreq.md") == "sysreq"

    def test_is_document(self):
        assert _TYPES.is_document("a.sysreq.md")
        assert not _TYPES.is_document("a.md")

    def test_types_for_plain_suffixes(self):
        types = DocumentTypes.for_suffixes((".x.md",))
        assert types.type_of("a.x.md") == ".x.md"


class TestGlobRules:
    def _types(self, *rules: GlobRule) -> DocumentTypes:
        return DocumentTypes.from_config(load_config(), rules)

    def test_glob_assigns_a_type_to_plain_files(self):
        types = self._types(GlobRule("failure_test/**/*.md", "sysreq"))
        assert types.type_of("failure_test/a/b.md") == "sysreq"
        assert types.is_document("failure_test/b.md")

    def test_files_outside_the_glob_are_not_documents(self):
        types = self._types(GlobRule("failure_test/**/*.md", "sysreq"))
        assert types.type_of("docs/readme.md") is None

    def test_glob_wins_over_the_suffix(self):
        types = self._types(GlobRule("legacy/**/*.md", "regreq"))
        assert types.type_of("legacy/a.sysreq.md") == "regreq"

    def test_first_matching_rule_wins(self):
        types = self._types(GlobRule("a/*.md", "swreq"), GlobRule("**/*.md", "sysreq"))
        assert types.type_of("a/x.md") == "swreq"
        assert types.type_of("b/x.md") == "sysreq"

    def test_leading_slash_is_ignored(self):
        types = self._types(GlobRule("a/*.md", "sysreq"))
        assert types.type_of("/a/x.md") == "sysreq"


class TestGlobToRegex:
    @pytest.mark.parametrize(
        ("pattern", "path", "matches"),
        [
            ("*.md", "a.md", True),
            ("*.md", "dir/a.md", False),
            ("**/*.md", "a.md", True),
            ("**/*.md", "x/y/a.md", True),
            ("docs/**/*.md", "docs/a.md", True),
            ("docs/**/*.md", "docs/x/y/a.md", True),
            ("docs/**/*.md", "other/a.md", False),
            ("docs/**", "docs/x/y/a.md", True),
            ("a?.md", "ab.md", True),
            ("a?.md", "a/.md", False),
            ("a.md", "axmd", False),
            ("req[1].md", "req[1].md", True),
        ],
    )
    def test_matching(self, pattern, path, matches):
        assert bool(glob_to_regex(pattern).fullmatch(path)) is matches


class TestParseGlobRule:
    def test_pattern_and_type(self):
        rule = parse_glob_rule("docs/**/*.md=sysreq", {"sysreq", "swreq"})
        assert rule == GlobRule("docs/**/*.md", "sysreq")

    def test_only_the_last_equals_sign_splits(self):
        rule = parse_glob_rule("a=b/*.md=sysreq", {"sysreq"})
        assert rule == GlobRule("a=b/*.md", "sysreq")

    @pytest.mark.parametrize("spec", ["no-equals-sign", "=sysreq", "docs/*.md="])
    def test_malformed_specs(self, spec):
        with pytest.raises(ValueError, match="PATTERN=TYPE"):
            parse_glob_rule(spec, {"sysreq"})

    def test_unknown_type(self):
        with pytest.raises(ValueError, match="unknown document type 'nope'"):
            parse_glob_rule("*.md=nope", {"sysreq", "swreq"})


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
