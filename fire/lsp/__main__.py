#!/usr/bin/env python3
"""Entry point: ``python -m fire.lsp [--config fire_config.yaml]`` (stdio)."""

import argparse

from fire.lsp.server import create_server
from fire.starlark.config_models import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="FIRE language server (stdio)")
    parser.add_argument("--config", default=None, help="Path to fire_config.yaml")
    args = parser.parse_args()
    create_server(load_config(args.config)).start_io()


if __name__ == "__main__":
    main()
