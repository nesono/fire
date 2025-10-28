"""Bazel rules for requirement management."""

def requirement_library(name, srcs, visibility = None):
    """Validates requirement documents and creates a filegroup.

    This creates a filegroup containing all requirement files.
    The files are available as dependencies but no validation is performed
    at build time (validation happens in CI or via separate tools).

    Args:
        name: Name of the target
        srcs: List of requirement markdown files
        visibility: Visibility of the target

    Example:
        requirement_library(
            name = "safety_requirements",
            srcs = glob(["requirements/safety/*.md"]),
        )
    """
    native.filegroup(
        name = name,
        srcs = srcs,
        visibility = visibility,
    )
