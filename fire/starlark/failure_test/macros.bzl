"""Helpers for failure tests."""

def discoverable(rule, **kwargs):
    """Instantiates a rule from a macro so that run_failure_tests.sh finds it.

    The runner discovers targets through the generator_location attribute, which
    only targets created by macros have. Plain rules such as rust_binary or
    release_readiness_test would otherwise be skipped.

    Args:
        rule: The rule to instantiate.
        **kwargs: Attributes of the target, including its name and tags.
    """
    rule(**kwargs)
