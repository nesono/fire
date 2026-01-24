"""Utilities for working with Pydantic validation errors."""

from __future__ import annotations

from pydantic import ValidationError
from pydantic_core import ErrorDetails


def format_validation_errors(
    error: ValidationError | None,
    skip_loc_tags: list[str] | None = None,
) -> list[str]:
    """Format a Pydantic ValidationError into user-friendly messages.

    Args:
        error: The Pydantic ValidationError to format, or None.
        skip_loc_tags: Location path elements to skip (e.g. discriminator tags).

    Returns:
        List of formatted error strings.
    """
    if error is None:
        return []

    skip = set(skip_loc_tags) if skip_loc_tags else set()
    results = []

    for err in error.errors():
        path_parts = [str(p) for p in err["loc"] if str(p) not in skip]
        path = " -> ".join(path_parts) if path_parts else "root"
        msg = _format_message(err)
        results.append(f"Validation error at '{path}': {msg}")

    return results


def _format_message(err: ErrorDetails) -> str:
    """Map a Pydantic error dict to a user-friendly message."""
    error_type = err["type"]
    msg = err["msg"]

    if error_type == "missing":
        field = err["loc"][-1] if err["loc"] else "field"
        return f"'{field}' is a required property"
    if error_type == "int_type":
        return "value is not a valid integer"
    if error_type == "float_type":
        return "value is not a valid number"
    if error_type == "string_type":
        return "value is not a valid string"
    if error_type == "bool_type":
        return "value is not a valid boolean"
    if error_type == "literal_error":
        return "value is not a valid enumeration member"
    if error_type == "union_tag_invalid":
        return "value is not a valid enumeration member"
    if error_type == "extra_forbidden":
        field = err["loc"][-1] if err["loc"] else "field"
        return f"Additional properties are not allowed ('{field}' was unexpected)"
    if error_type == "string_pattern_mismatch":
        ctx = err.get("ctx", {})
        pattern = ctx.get("pattern", "") if ctx else ""
        value = err.get("input", "")
        return f"'{value}' does not match '{pattern}'"
    if error_type == "value_error":
        return msg.replace("Value error, ", "")
    return msg
