#!/usr/bin/env python3
"""Diagnostics for parameter YAML files.

The rules are those of the build: the file is validated with the same Pydantic
model. Its errors carry a path into the document, which is mapped back to the
range of the offending text. Two kinds of errors need extra care:

* A parameter is validated against every parameter type, so one mistake
  produces an error per type. Only the errors of the type that fits the value
  (the one whose ``type`` literal matches) are reported.
* Errors raised by whole-file rules (key names, versions, identifiers) have no
  path, only quoted names in their message, which are matched to the keys.
"""

from __future__ import annotations

import re
from typing import Any, Final

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from fire.lsp.diagnostic import Diagnostic, error
from fire.lsp.document_parser import Position, Range
from fire.lsp.yaml_nodes import (
    YamlSyntaxError,
    load_yaml,
    locate,
    parse_yaml,
    top_level_keys,
)
from fire.starlark.parameter_models import (
    BoolParameter,
    F64Parameter,
    I64Parameter,
    ParameterFile,
    StringParameter,
    TableParameter,
)
from fire.starlark.patterns import PARAM_VERSION_SUFFIX_RE
from fire.starlark.pydantic_tools import format_validation_errors

_SYNTAX: Final = "FIRE017"
_PARAMETER: Final = "FIRE018"
_MEMBERS: Final = tuple(
    cls.__name__
    for cls in (
        I64Parameter,
        F64Parameter,
        StringParameter,
        BoolParameter,
        TableParameter,
    )
)
_QUOTED_RE: Final = re.compile(r"'([^']+)'")
_SHAPE_MESSAGE: Final = (
    "A parameter must be a mapping with value, unit and description, "
    "or a table with columns and rows"
)
_DOCUMENT_START: Final = Range(Position(0, 0), Position(0, 0))
_VERSIONED_KEY_RE: Final = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*_v[0-9]+[ \t]*:", re.MULTILINE
)


def _base_name(key: str) -> str:
    match = PARAM_VERSION_SUFFIX_RE.match(key)
    return match.group(1) if match else key


def _document_start(root: Any) -> Range:
    located = locate(root, [])
    return located.value if located else _DOCUMENT_START


def _unfit_members(errors: list[ErrorDetails]) -> set[tuple[str, str]]:
    """Parameter types whose ``type`` literal does not match the value."""
    return {
        (str(e["loc"][0]), str(e["loc"][1]))
        for e in errors
        if e["type"] == "literal_error"
        and len(e["loc"]) >= 3
        and e["loc"][-1] == "type"
    }


def _root_error(
    root: Any, keys: dict[str, Range], err: ErrorDetails
) -> list[Diagnostic]:
    message = err["msg"].removeprefix("Value error, ")
    names = _QUOTED_RE.findall(message)
    if message.startswith("Parameter key"):
        names = names[:1]
    ranges = [r for key, r in keys.items() if key in names or _base_name(key) in names]
    return [error(r, _PARAMETER, message) for r in ranges or [_document_start(root)]]


def _range_for(root: Any, path: list[Any], error_type: str) -> Range:
    located = locate(root, path[:-1] if error_type == "missing" else path)
    located = located or locate(root, path[:1])
    if located is None:
        return _document_start(root)
    wants_key = error_type in ("missing", "extra_forbidden") or not located.is_scalar
    return located.key if wants_key and located.key else located.value


def _is_injected_column_type(err: ErrorDetails, rest: list[Any]) -> bool:
    """Column types are inferred from the rows, so a missing one is never the fault."""
    return (
        err["type"] == "missing"
        and len(rest) == 3
        and rest[0] == "columns"
        and rest[2] == "type"
    )


def _field_error(
    root: Any, err: ErrorDetails, message: str, unfit: set[tuple[str, str]]
) -> list[Diagnostic]:
    key, rest = str(err["loc"][0]), list(err["loc"][1:])
    member = str(rest.pop(0)) if rest and rest[0] in _MEMBERS else None
    if (member and (key, member) in unfit) or _is_injected_column_type(err, rest):
        return []
    if err["type"] == "model_type" and not rest:
        return [
            error(_range_for(root, [key], "model_type"), _PARAMETER, _SHAPE_MESSAGE)
        ]
    return [error(_range_for(root, [key, *rest], err["type"]), _PARAMETER, message)]


def _validation_diagnostics(root: Any, exc: ValidationError) -> list[Diagnostic]:
    errors = exc.errors()
    messages = format_validation_errors(exc, skip_loc_tags=list(_MEMBERS))
    keys, unfit = top_level_keys(root), _unfit_members(errors)
    diagnostics: list[Diagnostic] = []
    for err, message in zip(errors, messages):
        if err["loc"]:
            diagnostics.extend(_field_error(root, err, message, unfit))
        else:
            diagnostics.extend(_root_error(root, keys, err))
    return diagnostics


def diagnose_parameters(text: str) -> list[Diagnostic]:
    """Return diagnostics for the text of a parameter YAML file."""
    try:
        root = parse_yaml(text)
        data = load_yaml(text)
    except YamlSyntaxError as exc:
        return [error(exc.range, _SYNTAX, f"Invalid YAML: {exc.message}")]
    if root is None:
        return []
    try:
        ParameterFile.model_validate(data)
    except ValidationError as exc:
        unique = dict.fromkeys(_validation_diagnostics(root, exc))
        return sorted(
            unique, key=lambda d: (d.range.start.line, d.range.start.character)
        )
    return []


def looks_like_parameter_file(text: str) -> bool:
    """True if a top-level key ends in ``_v<digits>``, as parameter keys do.

    A plain ``.yaml`` file has no distinctive name, and CI or Docker files must
    not be flagged. The check works on the raw text so that a parameter file
    that is invalid YAML while being edited still gets its diagnostics, and a
    wrongly written key such as ``maxSpeed_v1`` still counts.
    """
    return _VERSIONED_KEY_RE.search(text) is not None
