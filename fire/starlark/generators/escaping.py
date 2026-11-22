"""Escaping of parameter text for the source code generators."""

import re
from typing import Final

_ESCAPED_CHARS: Final = re.compile(r'[\\"\x00-\x1f\x7f]')
_LINE_BREAKS: Final = re.compile(r"[\x00-\x1f\x7f\x85\u2028\u2029]+")

_NAMED_ESCAPES: Final = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}

# Octal in C++ and Java: both treat \x as greedy (C++) or do not have it (Java),
# and Java rewrites \uXXXX before lexing, so no unicode escapes are emitted.
_CONTROL_ESCAPES: Final = {
    "cpp": "\\{:03o}",
    "java": "\\{:03o}",
    "python": "\\x{:02x}",
    "go": "\\x{:02x}",
    "rust": "\\x{:02x}",
}


def escape_string(language: str, text: object) -> str:
    """Escape ``text`` for use between the quotes of a string literal."""
    control_format = _CONTROL_ESCAPES[language]

    def replace(match: re.Match[str]) -> str:
        char = match.group()
        return _NAMED_ESCAPES.get(char) or control_format.format(ord(char))

    return _ESCAPED_CHARS.sub(replace, str(text))


def sanitize_comment(language: str, text: object) -> str:
    """Flatten ``text`` so that it cannot end or escape a comment.

    Line breaks are collapsed, since they would end a line comment. Java
    additionally gets ``*/`` and ``\\u`` defused (block comments end at ``*/``
    and unicode escapes are processed inside comments). A trailing backslash is
    dropped for C++, where it would splice the next line into the comment.
    """
    flat = " ".join(_LINE_BREAKS.sub(" ", str(text)).split())
    if language == "java":
        flat = flat.replace("*/", "* /").replace("\\u", "\\ u")
    if language == "cpp":
        flat = flat.rstrip("\\ ")
    return flat
