"""Common path handling utilities for Fire requirements management system.

This module provides path validation and normalization functions used across
validation and code generation modules.
"""


def extract_version_from_url(full_url: str) -> tuple[str, int | None]:
    """Parse URL to extract clean path and version query parameter.

    Handles URLs of the form:
    - path/to/file.yaml?version=2#anchor
    - path/to/file.yaml?version=2
    - path/to/file.yaml#anchor
    - path/to/file.yaml

    Args:
        full_url: URL string potentially containing query parameters and fragments

    Returns:
        Tuple of (clean_path, version) where:
        - clean_path: URL with version removed but fragment preserved
        - version: Integer version if specified, None otherwise

    Example:
        >>> extract_version_from_url("params.yaml?version=2#velocity")
        ("params.yaml#velocity", 2)
    """
    version = None
    clean_path = full_url

    if "?" in full_url:
        path_part, query_part = full_url.split("?", 1)
        # Extract query string (before fragment if present)
        query_str = query_part.split("#")[0] if "#" in query_part else query_part

        # Parse query parameters
        for param in query_str.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                if key == "version" and value.isdigit():
                    version = int(value)

        # Reconstruct path without version query but with fragment
        clean_path = path_part
        if "#" in query_part:
            clean_path = clean_path + "#" + query_part.split("#")[1]

    return clean_path, version


def normalize_repo_path(path: str) -> tuple[str, str | None]:
    """Validate and normalize repository-relative paths.

    Repository-relative paths must start with "/" to indicate they are
    relative to the workspace root, not the current file.

    Args:
        path: Path string to validate and normalize

    Returns:
        Tuple of (normalized_path, error_msg) where:
        - normalized_path: Path with leading "/" removed (empty if invalid)
        - error_msg: Error message if invalid, None if valid

    Example:
        >>> normalize_repo_path("/path/to/file.yaml")
        ("path/to/file.yaml", None)
        >>> normalize_repo_path("relative/path.yaml")
        ("", "Path must be repository-relative (start with /)")
    """
    if not path.startswith("/"):
        return (
            "",
            "Path must be repository-relative (start with /) to ensure "
            "unambiguous references across the workspace",
        )

    # Strip leading slash for filesystem operations
    normalized = path[1:]
    return (normalized, None)


def validate_reference_path(
    path: str,
    expected_extension: str | list[str] | None = None,
    ref_type: str = "reference",
) -> tuple[str, str | None]:
    """Validate reference paths with optional extension checking.

    Combines repository-relative validation with file extension checking.

    Args:
        path: Path to validate
        expected_extension: Required extension(s) like ".yaml" or [".md", ".txt"]
        ref_type: Description of reference type for error messages

    Returns:
        Tuple of (normalized_path, error_msg) where error_msg is None if valid

    Example:
        >>> validate_reference_path("/params.yaml", ".yaml")
        ("params.yaml", None)
        >>> validate_reference_path("/doc.md", [".md", ".txt"])
        ("doc.md", None)
    """
    # First validate repository-relative format
    normalized, error = normalize_repo_path(path)
    if error:
        return ("", error)

    # Check file extension if specified
    if expected_extension is not None:
        extensions = (
            [expected_extension]
            if isinstance(expected_extension, str)
            else expected_extension
        )
        if not any(path.endswith(ext) for ext in extensions):
            ext_list = ", ".join(extensions)
            return (
                "",
                f"{ref_type.capitalize()} path must end with {ext_list}, got: {path}",
            )

    return (normalized, None)
