"""Linter aspect configurations for the project."""

load("@aspect_rules_lint//lint:lint_test.bzl", "lint_test")
load("@aspect_rules_lint//lint:ty.bzl", "lint_ty_aspect")

ty = lint_ty_aspect(
    binary = "@aspect_rules_lint//lint:ty_bin",
    config = Label("@fire//:pyproject.toml"),
)

ty_test = lint_test(aspect = ty)
