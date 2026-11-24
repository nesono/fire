#!/usr/bin/env python3
"""Decide which files are FIRE documents, and of which document type.

By default the type comes from the file suffix configured in
``fire_config.yaml`` (``.sysreq.md`` and so on). Glob rules can additionally
assign a type to files that do not follow the naming convention. All paths are
workspace-relative with ``/`` separators; a leading ``/`` is ignored.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from fire.starlark.config_models import FireConfig


@dataclass(frozen=True)
class GlobRule:
    pattern: str
    type_name: str


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a glob to a regex: ``**`` crosses directories, ``*`` and ``?`` do not."""
    parts: list[str] = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            parts.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            parts.append(".*")
            index += 2
        else:
            char = pattern[index]
            parts.append({"*": "[^/]*", "?": "[^/]"}.get(char, re.escape(char)))
            index += 1
    return re.compile("".join(parts))


def parse_glob_rule(spec: str, known_types: Collection[str]) -> GlobRule:
    """Parse ``PATTERN=TYPE`` and check that TYPE is a configured document type."""
    pattern, _, type_name = spec.rpartition("=")
    if not pattern or not type_name:
        raise ValueError(f"expected PATTERN=TYPE, got '{spec}'")
    if type_name not in known_types:
        known = ", ".join(sorted(known_types))
        raise ValueError(f"unknown document type '{type_name}' (known: {known})")
    return GlobRule(pattern, type_name)


class DocumentTypes:
    def __init__(
        self,
        suffix_types: Mapping[str, str],
        rules: Sequence[GlobRule] = (),
    ) -> None:
        self._suffix_types = dict(suffix_types)
        self._rules = [(glob_to_regex(r.pattern), r.type_name) for r in rules]

    @classmethod
    def from_config(
        cls, config: FireConfig, rules: Sequence[GlobRule] = ()
    ) -> DocumentTypes:
        suffixes = {dt.suffix: name for name, dt in config.document_types.items()}
        return cls(suffixes, rules)

    @classmethod
    def for_suffixes(cls, suffixes: Sequence[str]) -> DocumentTypes:
        """Types named after their suffix, for callers without a config."""
        return cls({suffix: suffix for suffix in suffixes})

    def type_of(self, relative_path: str) -> str | None:
        """Return the document type of a file, or ``None`` if it is not a document.

        Glob rules are tried first, in order, then the suffixes.
        """
        path = relative_path.lstrip("/")
        for regex, type_name in self._rules:
            if regex.fullmatch(path):
                return type_name
        for suffix, type_name in self._suffix_types.items():
            if path.endswith(suffix):
                return type_name
        return None

    def is_document(self, relative_path: str) -> bool:
        return self.type_of(relative_path) is not None
