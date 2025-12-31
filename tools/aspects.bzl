"""Aspect definitions for Bazel aspects used in this repo."""

load("@pip_types//:types.bzl", "types")
load("@rules_mypy//mypy:mypy.bzl", "mypy")

mypy_aspect = mypy(types = types)
