"""Normalization of parameter units into suffixes of generated identifiers."""

import re
from typing import Final

_ASCII_ALNUM: Final = re.compile(r"[a-z0-9]")

_SYMBOLS: Final = {
    "°": "deg",
    "%": "percent",
    "‰": "permille",
    "²": "2",
    "³": "3",
    "\u00b5": "u",  # micro sign
    "\u03bc": "u",  # greek small mu
    "\u03a9": "ohm",  # greek capital omega
    "\u2126": "ohm",  # ohm sign
    "(": "",
    ")": "",
}
_DROPPED: Final = str.maketrans("", "", "^·* -")


def normalize_unit_suffix(unit: str) -> str:
    """Convert a unit string to a suffix for generated identifiers.

    Examples:
        "m/s"    -> "mps"
        "m/s^2"  -> "mps2"
        "m/s²"   -> "mps2"
        "°C"     -> "degc"
        "%"      -> "percent"
        "kg/m^3" -> "kgpm3"
        "1"      -> ""  (dimensionless)
    """
    if not unit or unit == "1" or unit.lower() == "dimensionless":
        return ""
    mapped = "".join(_SYMBOLS.get(char, char) for char in unit)
    return mapped.lower().replace("/", "p").translate(_DROPPED)


def unsupported_characters(unit: str) -> list[str]:
    """Return the characters of the normalized unit that are not [a-z0-9]."""
    bad: list[str] = []
    for char in normalize_unit_suffix(unit):
        if not _ASCII_ALNUM.fullmatch(char) and char not in bad:
            bad.append(char)
    return bad
