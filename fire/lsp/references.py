#!/usr/bin/env python3
"""Find the links that point at a requirement or a parameter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fire.lsp.document_parser import Position, Range
from fire.lsp.index import parameters_in, requirements_in
from fire.lsp.link_diagnostics import is_checked_link
from fire.lsp.link_index import PARAMETER, REQUIREMENT, IndexedLink, identify
from fire.lsp.navigation import link_at
from fire.lsp.workspace import Workspace

_YAML_SUFFIX = ".yaml"


@dataclass(frozen=True)
class ReferenceTarget:
    """What references are wanted for: a requirement ID or a parameter name.

    *version* is the version at the cursor, used to list links to exactly that
    version before links to other versions.
    """

    path: Path
    kind: str
    name: str
    version: int | None


def _within(range_: Range, position: Position) -> bool:
    if position.line != range_.start.line:
        return False
    return range_.start.character <= position.character < range_.end.character


def _link_target(
    text: str, position: Position, workspace: Workspace
) -> ReferenceTarget | None:
    link = link_at(text, position)
    if link is None or not is_checked_link(link) or not link.path.startswith("/"):
        return None
    located = workspace.locate(link.path)
    if located is None:
        return None
    kind, name = identify(link)
    return ReferenceTarget(located[0], kind, name, link.version)


def _parameter_target(
    text: str, position: Position, path: Path
) -> ReferenceTarget | None:
    for info in parameters_in(text).values():
        for version, key_range in info.versions.items():
            if _within(key_range, position):
                return ReferenceTarget(path, PARAMETER, info.name, version)
    return None


def _requirement_target(
    text: str, position: Position, path: Path
) -> ReferenceTarget | None:
    for info in requirements_in(text).values():
        if _within(info.range, position):
            return ReferenceTarget(path, REQUIREMENT, info.id, info.version)
    return None


def target_at(
    text: str,
    position: Position,
    path: Path,
    workspace: Workspace,
    suffixes: tuple[str, ...],
) -> ReferenceTarget | None:
    """Return what the cursor in the document at *path* asks references for.

    The cursor can be on a link, on a requirement heading ID, or on a
    ``name_vN`` key in a parameter file.
    """
    target = _link_target(text, position, workspace)
    if target is not None:
        return target
    if path.suffix == _YAML_SUFFIX:
        return _parameter_target(text, position, path)
    return _requirement_target(text, position, path)


def _points_at(link: IndexedLink, target: ReferenceTarget, root: Path) -> bool:
    linked = (root / link.path[1:]).resolve()
    validated = linked.with_name(f"{linked.stem}_validated{_YAML_SUFFIX}")
    # parameter_library emits foo_validated.yaml for a generated foo.yaml
    return linked == target.path or (
        linked.suffix == _YAML_SUFFIX and validated == target.path
    )


def find_references(
    links: list[IndexedLink], target: ReferenceTarget, root: Path
) -> list[IndexedLink]:
    """Return the links to *target*, those to its exact version first."""
    matching = [
        link
        for link in links
        if link.kind == target.kind
        and link.name == target.name
        and _points_at(link, target, root)
    ]
    return sorted(matching, key=lambda link: link.version != target.version)


def declaration_range(target: ReferenceTarget, text: str) -> Range | None:
    """Return where *target* is declared in *text*: its heading ID or key.

    For a parameter this is the key of the target's version, or of the latest
    version if that one is not defined.
    """
    if target.kind == PARAMETER:
        info = parameters_in(text).get(target.name)
        if info is None:
            return None
        return info.versions.get(target.version) or info.versions[max(info.versions)]
    requirement = requirements_in(text).get(target.name)
    return requirement.range if requirement else None
