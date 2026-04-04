"""Common file I/O utilities for Fire requirements management system.

This module provides safe file reading and YAML loading with consistent
error handling.
"""

from typing import Any

import yaml


def read_file_safe(file_path: str) -> tuple[str | None, str | None]:
    """Safely read a file with consistent error handling.

    Args:
        file_path: Path to file to read

    Returns:
        Tuple of (content, error_msg) where:
        - content: File contents if successful, None otherwise
        - error_msg: Error message if failed, None otherwise

    Example:
        >>> content, error = read_file_safe("config.yaml")
        >>> if error:
        ...     print(f"Failed: {error}")
        ... else:
        ...     process(content)
    """
    try:
        with open(file_path) as f:
            return f.read(), None
    except FileNotFoundError:
        return None, f"File not found: {file_path}"
    except PermissionError:
        return None, f"Permission denied: {file_path}"
    except Exception as e:
        return None, f"Error reading {file_path}: {e}"


def load_yaml_safe(file_path: str) -> tuple[Any | None, str | None]:
    """Safely load YAML file with consistent error handling.

    Args:
        file_path: Path to YAML file to load

    Returns:
        Tuple of (data, error_msg) where:
        - data: Parsed YAML data if successful, None otherwise
        - error_msg: Error message if failed, None otherwise

    Example:
        >>> data, error = load_yaml_safe("config.yaml")
        >>> if error:
        ...     print(f"Failed: {error}")
        ... else:
        ...     process(data)
    """
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
            return data, None
    except FileNotFoundError:
        return None, f"File not found: {file_path}"
    except yaml.YAMLError as e:
        return None, f"Invalid YAML syntax in {file_path}: {e}"
    except PermissionError:
        return None, f"Permission denied: {file_path}"
    except Exception as e:
        return None, f"Error loading YAML from {file_path}: {e}"


def write_yaml_safe(file_path: str, data: Any) -> str | None:
    """Safely write data to YAML file with consistent error handling.

    Args:
        file_path: Path to YAML file to write
        data: Data to serialize to YAML

    Returns:
        Error message if failed, None if successful

    Example:
        >>> error = write_yaml_safe("config.yaml", {"key": "value"})
        >>> if error:
        ...     print(f"Failed: {error}")
    """
    try:
        with open(file_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            return None
    except PermissionError:
        return f"Permission denied: {file_path}"
    except yaml.YAMLError as e:
        return f"Error serializing YAML to {file_path}: {e}"
    except Exception as e:
        return f"Error writing YAML to {file_path}: {e}"
