#!/usr/bin/env python3
"""A position-aware view of YAML documents.

``yaml.safe_load`` discards where values were written. Composing the document
keeps a node tree with line and column marks, which lets validation errors
that name a path such as ``max_speed_v1 -> unit`` point at the offending text.
Columns are code points, like the rest of the language server.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from dataclasses import dataclass

import yaml

from fire.lsp.document_parser import Position, Range


class YamlSyntaxError(Exception):
    """The text is not valid YAML."""

    def __init__(self, message: str, range_: Range) -> None:
        super().__init__(message)
        self.message = message
        self.range = range_


@dataclass(frozen=True)
class Located:
    """A node found by path: its value, and its key when it is a mapping entry."""

    value: Range
    key: Range | None
    is_scalar: bool


def _range(node: yaml.Node) -> Range:
    start, end = node.start_mark, node.end_mark
    return Range(Position(start.line, start.column), Position(end.line, end.column))


def _error_range(error: yaml.MarkedYAMLError) -> Range:
    mark = error.problem_mark or error.context_mark
    if mark is None:
        return Range(Position(0, 0), Position(0, 0))
    return Range(Position(mark.line, mark.column), Position(mark.line, mark.column + 1))


def _syntax_error(error: yaml.YAMLError) -> YamlSyntaxError:
    if isinstance(error, yaml.MarkedYAMLError):
        return YamlSyntaxError(error.problem or "invalid YAML", _error_range(error))
    return YamlSyntaxError(str(error), Range(Position(0, 0), Position(0, 1)))


def parse_yaml(text: str) -> yaml.Node | None:
    """Compose *text* into a node tree; ``None`` if it has no document."""
    try:
        return yaml.compose(text)
    except yaml.YAMLError as error:
        raise _syntax_error(error) from error


def load_yaml(text: str) -> Any:
    """Load *text* as plain data. Unsupported tags are reported as syntax errors."""
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise _syntax_error(error) from error


def top_level_keys(root: yaml.Node | None) -> dict[str, Range]:
    """Return the keys of the top-level mapping with their ranges."""
    if not isinstance(root, yaml.MappingNode):
        return {}
    return {
        key.value: _range(key)
        for key, _ in root.value
        if isinstance(key, yaml.ScalarNode)
    }


def _child(
    node: yaml.Node, step: str | int
) -> tuple[yaml.Node | None, yaml.Node | None]:
    """Return ``(key node, value node)`` for one step below *node*."""
    if isinstance(node, yaml.MappingNode) and isinstance(step, str):
        for key, value in node.value:
            if isinstance(key, yaml.ScalarNode) and key.value == step:
                return key, value
    if isinstance(node, yaml.SequenceNode) and isinstance(step, int):
        if 0 <= step < len(node.value):
            return None, node.value[step]
    return None, None


def locate(root: yaml.Node | None, path: Sequence[str | int]) -> Located | None:
    """Find the node at *path*: mapping keys are strings, list items are indexes."""
    node, key = root, None
    for step in path:
        if node is None:
            return None
        key, node = _child(node, step)
    if node is None:
        return None
    return Located(
        _range(node), _range(key) if key else None, isinstance(node, yaml.ScalarNode)
    )
