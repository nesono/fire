#!/usr/bin/env python3
"""Tests for the command line of the language server."""

import pytest

from fire.lsp.__main__ import create_server_from_arguments


class TestCommandLine:
    def test_defaults_need_no_arguments(self):
        assert create_server_from_arguments([]) is not None

    def test_glob_rules_are_accepted(self):
        arguments = [
            "--glob-type",
            "docs/**/*.md=sysreq",
            "--glob-type",
            "x/*.md=swreq",
        ]
        assert create_server_from_arguments(arguments) is not None

    def test_unknown_document_type_is_rejected(self, capsys):
        with pytest.raises(SystemExit) as raised:
            create_server_from_arguments(["--glob-type", "*.md=nope"])
        assert raised.value.code == 2
        assert "unknown document type 'nope'" in capsys.readouterr().err

    def test_malformed_rule_is_rejected(self, capsys):
        with pytest.raises(SystemExit):
            create_server_from_arguments(["--glob-type", "no-equals-sign"])
        assert "PATTERN=TYPE" in capsys.readouterr().err


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
