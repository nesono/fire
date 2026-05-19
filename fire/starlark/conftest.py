"""Shared pytest fixtures for fire/starlark tests."""

import pytest

from fire.starlark.config_models import load_config


@pytest.fixture()
def default_config():
    """Return the built-in default FIRE config."""
    return load_config()
