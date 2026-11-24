#!/usr/bin/env python3
"""Entry point: ``python -m fire.lsp [options]`` (stdio)."""

import argparse
from collections.abc import Sequence

from pygls.lsp.server import LanguageServer

from fire.lsp.document_types import GlobRule, parse_glob_rule
from fire.lsp.server import create_server
from fire.starlark.config_models import load_config


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FIRE language server (stdio)")
    parser.add_argument("--config", default=None, help="Path to fire_config.yaml")
    parser.add_argument(
        "--glob-type",
        action="append",
        default=[],
        metavar="PATTERN=TYPE",
        help=(
            "Treat workspace-relative files matching PATTERN (`**` crosses "
            "directories) as document type TYPE, e.g. 'docs/**/*.md=sysreq'. "
            "Repeatable; the first matching rule wins."
        ),
    )
    return parser


def create_server_from_arguments(
    arguments: Sequence[str] | None = None,
) -> LanguageServer:
    parser = _parser()
    args = parser.parse_args(arguments)
    config = load_config(args.config)
    rules: list[GlobRule] = []
    for spec in args.glob_type:
        try:
            rules.append(parse_glob_rule(spec, config.document_types))
        except ValueError as error:
            parser.error(str(error))
    return create_server(config, rules)


def main() -> None:
    create_server_from_arguments().start_io()


if __name__ == "__main__":
    main()
