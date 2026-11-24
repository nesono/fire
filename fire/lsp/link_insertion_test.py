#!/usr/bin/env python3
"""Tests for inserting a complete link from ``[@`` or ``[REQ``."""

import pytest
from lsprotocol import types as lsp

from fire.lsp.document_parser import Position, Range
from fire.lsp.link_insertion import link_insertion_candidates
from fire.lsp.link_targets import LinkTarget

_CURSOR = "§"
_TARGETS = [
    LinkTarget("parameter", "max_speed", 2, "/params.yaml"),
    LinkTarget("parameter", "wheel_count", 1, "/params.yaml"),
    LinkTarget("requirement", "REQ-A", 3, "/reqs/a.sysreq.md"),
    LinkTarget("requirement", "REQ-B", None, "/reqs/a.sysreq.md"),
]


def _candidates(marked: str, targets=_TARGETS):
    before, _, after = marked.partition(_CURSOR)
    line = before.count("\n")
    character = len(before) - (before.rfind("\n") + 1)
    return link_insertion_candidates(
        before + after, Position(line, character), lambda: targets
    )


def _labels(marked: str) -> list[str]:
    return [c.label for c in _candidates(marked)]


class TestParameters:
    def test_at_sign_offers_the_parameters(self):
        assert _labels("See [@§") == ["@max_speed", "@wheel_count"]

    def test_candidate_inserts_the_whole_link(self):
        first = _candidates("See [@§")[0]
        assert first.new_text == "[@max_speed](/params.yaml?version=2#max_speed)"
        assert first.kind == lsp.CompletionItemKind.Reference
        assert first.detail == "/params.yaml, version 2"

    def test_typed_text_including_the_bracket_is_replaced(self):
        candidate = _candidates("See [@ma§")[0]
        assert candidate.replace == Range(Position(0, 4), Position(0, 8))
        assert candidate.filter_text == "[@max_speed"

    def test_requirements_are_not_offered_after_an_at_sign(self):
        assert all(not label.startswith("REQ") for label in _labels("[@§"))


class TestRequirements:
    def test_uppercase_start_offers_the_requirements(self):
        assert _labels("See [REQ§") == ["REQ-A", "REQ-B"]

    def test_a_single_letter_is_enough(self):
        assert _labels("See [R§") == ["REQ-A", "REQ-B"]

    def test_candidate_inserts_the_whole_link(self):
        first = _candidates("See [REQ§")[0]
        assert first.new_text == "[REQ-A](/reqs/a.sysreq.md?version=3#REQ-A)"
        assert first.detail == "/reqs/a.sysreq.md, version 3"
        assert first.replace == Range(Position(0, 4), Position(0, 8))

    def test_requirement_without_a_version_has_no_query(self):
        second = _candidates("[REQ§")[1]
        assert second.new_text == "[REQ-B](/reqs/a.sysreq.md#REQ-B)"
        assert second.detail == "/reqs/a.sysreq.md"

    def test_parameters_are_not_offered(self):
        assert all(label.startswith("REQ") for label in _labels("[REQ§"))


class TestWhenNotToOffer:
    @pytest.mark.parametrize(
        "marked",
        [
            "plain §",
            "See [§",
            "See [r§",
            "See [1§",
            "[REQ-1][lab§",
            "[REQ-1](/a.md?version=1#§",
            "mid[@ma§x](/p.yaml?version=1#max_speed)",
            "[@§](/p.yaml?version=1#x)",
            "[§text](/p.yaml)",
        ],
    )
    def test_nothing(self, marked):
        assert _candidates(marked) == []

    def test_targets_are_only_loaded_when_needed(self):
        calls = []

        def targets():
            calls.append(1)
            return _TARGETS

        for text in ("plain", "See [", "[r"):
            link_insertion_candidates(text, Position(0, len(text)), targets)
        assert calls == []


class TestAutoPairedBracket:
    def test_the_closing_bracket_is_replaced_too(self):
        prefix = "See [@"
        candidate = _candidates(prefix + "§]")[0]
        assert candidate.replace == Range(Position(0, 4), Position(0, len(prefix) + 1))

    def test_typed_prefix_with_a_closing_bracket(self):
        candidate = _candidates("[REQ-§] and more")[0]
        assert candidate.replace == Range(Position(0, 0), Position(0, 6))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
