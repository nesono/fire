"""Tests for escaping of parameter text in generated code."""

import sys

import pytest

from fire.starlark.generate_code import yaml_to_items
from fire.starlark.generators import escaping
from fire.starlark.generators.cpp import generate_cpp_files
from fire.starlark.generators.go import generate_go_files
from fire.starlark.generators.java import generate_java_files
from fire.starlark.generators.python import generate_python_files
from fire.starlark.generators.rust import generate_rust_files

LANGUAGES = ["cpp", "python", "go", "rust", "java"]
VALUE = 'say "hi" \\ done\tx\nline2'
DESCRIPTION = 'first\nINJECTED = 1  //\n"""\n*/ \\u000a'
COMMENT_PREFIXES = {
    "cpp": ("//",),
    "go": ("//",),
    "rust": ("//",),
    "java": ("//", "*", "/*"),
    "python": ("#", '"""'),
}


class TestEscapeString:
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_quote_backslash_and_whitespace_escapes(self, language):
        text = 'a"b\\c\nd\te\rf'
        assert escaping.escape_string(language, text) == 'a\\"b\\\\c\\nd\\te\\rf'

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_plain_and_non_ascii_text_unchanged(self, language):
        assert escaping.escape_string(language, "Bremsweg é 100%") == "Bremsweg é 100%"

    @pytest.mark.parametrize(
        "language, expected",
        [
            ("cpp", "\\001"),
            ("java", "\\001"),
            ("python", "\\x01"),
            ("go", "\\x01"),
            ("rust", "\\x01"),
        ],
    )
    def test_other_control_characters(self, language, expected):
        assert escaping.escape_string(language, "\x01") == expected

    def test_non_string_values_are_converted(self):
        assert escaping.escape_string("go", 42) == "42"


class TestSanitizeComment:
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_line_breaks_become_single_spaces(self, language):
        text = "a\nb\r\nc\u2028d\x85e  f"
        assert escaping.sanitize_comment(language, text) == "a b c d e f"

    def test_java_block_comment_terminator_is_broken_up(self):
        assert escaping.sanitize_comment("java", "a */ b") == "a * / b"

    def test_java_unicode_escape_is_broken_up(self):
        assert escaping.sanitize_comment("java", "x \\u000a y") == "x \\ u000a y"

    @pytest.mark.parametrize("language", ["cpp", "python", "go", "rust"])
    def test_block_comment_terminator_kept_where_harmless(self, language):
        assert escaping.sanitize_comment(language, "a */ b") == "a */ b"

    def test_cpp_trailing_backslash_removed_to_avoid_line_splice(self):
        assert escaping.sanitize_comment("cpp", "path C:\\ ") == "path C:"


def _items():
    return yaml_to_items(
        {
            "s_v1": {
                "type": "string",
                "value": VALUE,
                "unit": "1",
                "description": DESCRIPTION,
            },
            "t_v1": {
                "type": "table",
                "description": DESCRIPTION,
                "columns": [
                    {"name": "a", "type": "string", "unit": "1"},
                    {"name": "b", "type": "i64", "unit": "1"},
                ],
                "rows": [[VALUE, 1]],
            },
        }
    )


def _generated(language):
    items = _items()
    if language == "cpp":
        return generate_cpp_files(items)
    if language == "python":
        return generate_python_files(items)
    if language == "go":
        return generate_go_files(items, package_name="params")
    if language == "rust":
        return generate_rust_files(items)
    return generate_java_files(items, namespace="p", class_name="Params")


class TestGeneratedCode:
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_value_is_emitted_as_escaped_literal(self, language):
        content = "".join(text for _, text in _generated(language))
        assert f'"{escaping.escape_string(language, VALUE)}"' in content

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_description_cannot_inject_code(self, language):
        for _, content in _generated(language):
            for line in content.split("\n"):
                if "INJECTED" in line:
                    assert line.lstrip().startswith(COMMENT_PREFIXES[language]), line

    def test_python_values_and_docstring_round_trip(self):
        namespace: dict = {}
        for name, content in _generated("python"):
            exec(compile(content, name, "exec"), namespace)
        assert namespace["S"] == VALUE
        assert namespace["T"][0].a == VALUE
        assert namespace["TRow"].__doc__ == DESCRIPTION


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
