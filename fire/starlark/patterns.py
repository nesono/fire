#!/usr/bin/env python3
"""Shared regex patterns for FIRE tooling."""

from __future__ import annotations

import re
from typing import Final

TODO_PATTERN: Final = re.compile(r"TODO\([A-Z]+-[0-9]+\)")
REQ_ID_PATTERN: Final = re.compile(r"^[A-Z][A-Z0-9_-]+$")
PARAM_VERSION_SUFFIX_RE: Final = re.compile(r"^([a-z][a-z0-9_]*)_v([1-9][0-9]*)$")
