#!/usr/bin/env python3
"""Check that link targets exist and that the linked version is current.

Severity follows the build: a parameter link to a future version is an error,
while version differences on requirement links are only warnings.
"""

from __future__ import annotations

from fire.lsp.diagnostic import Diagnostic, error, warning
from fire.lsp.document_parser import Link, parse_links
from fire.lsp.index import (
    ParameterInfo,
    RequirementInfo,
    parameters_in,
    requirements_in,
)
from fire.lsp.link_diagnostics import is_checked_link, is_parameter_link
from fire.lsp.workspace import Workspace


class _Targets:
    """Reads and parses each link target at most once per analysis."""

    def __init__(self, workspace: Workspace) -> None:
        self._workspace = workspace
        self._texts: dict[str, str | None] = {}

    def text(self, path: str) -> str | None:
        if path not in self._texts:
            self._texts[path] = self._workspace.read(path)
        return self._texts[path]


def _stale_or_future(
    link: Link, current: int | None, label: str, future_is_error: bool
) -> list[Diagnostic]:
    if link.version is None or current is None or link.version == current:
        return []
    if link.version > current:
        message = f"{label} expects a future version ({link.version}), but the latest is {current}"
        make = error if future_is_error else warning
        return [make(link.url_range, "FIRE014", message)]
    message = f"{label} links version {link.version}, but the latest is {current}"
    return [warning(link.url_range, "FIRE015", message)]


def _parameter_diagnostics(link: Link, targets: _Targets) -> list[Diagnostic]:
    text = targets.text(link.path)
    if text is None:
        message = f"Parameter file does not exist: {link.path}"
        return [error(link.url_range, "FIRE012", message)]
    name = link.anchor or link.text[1:]
    info: ParameterInfo | None = parameters_in(text).get(name)
    if info is None:
        message = f"Parameter '{name}' not found in {link.path}"
        return [error(link.text_range, "FIRE013", message)]
    latest = max(info.versions)
    if link.version is not None and link.version < latest:
        if link.version not in info.versions:
            available = ", ".join(str(v) for v in sorted(info.versions))
            message = (
                f"Parameter '{name}' has no version {link.version} "
                f"(available: {available})"
            )
            return [error(link.url_range, "FIRE013", message)]
    return _stale_or_future(link, latest, f"Parameter '{name}'", True)


def _requirement_diagnostics(
    link: Link, targets: _Targets, suffixes: tuple[str, ...]
) -> list[Diagnostic]:
    text = targets.text(link.path)
    if text is None:
        message = f"Requirement file does not exist: {link.path}"
        return [error(link.url_range, "FIRE012", message)]
    if not link.path.endswith(suffixes):
        return []
    info: RequirementInfo | None = requirements_in(text).get(link.text)
    if info is None:
        message = f"Requirement file {link.path} does not contain ID '{link.text}'"
        return [error(link.text_range, "FIRE013", message)]
    return _stale_or_future(link, info.version, f"Requirement '{link.text}'", False)


class ReferenceChecker:
    """Checks parameter and requirement links against files in a workspace.

    *suffixes* are the document-type file suffixes. Requirement links to other
    Markdown files only need to resolve to an existing file.
    """

    def __init__(self, workspace: Workspace, suffixes: tuple[str, ...]) -> None:
        self._workspace = workspace
        self._suffixes = suffixes

    def diagnose(self, text: str) -> list[Diagnostic]:
        targets = _Targets(self._workspace)
        diagnostics: list[Diagnostic] = []
        for link in parse_links(text):
            if is_checked_link(link) and link.path.startswith("/"):
                diagnostics.extend(self._diagnose_link(link, targets))
        return diagnostics

    def _diagnose_link(self, link: Link, targets: _Targets) -> list[Diagnostic]:
        if is_parameter_link(link):
            return _parameter_diagnostics(link, targets)
        return _requirement_diagnostics(link, targets, self._suffixes)
