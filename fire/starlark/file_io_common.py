"""Common file I/O utilities for Fire requirements management system.

This module provides safe file reading and YAML/JSON loading with consistent
error handling.

Error-handling conventions used across ``fire/starlark``:

- **Library functions that touch I/O** return ``(data, error_msg)`` tuples.
  Callers branch on whether ``error_msg`` is ``None``. This module is the
  reference implementation.
- **Library functions that validate inputs** raise ``ValueError`` (or
  pydantic's ``ValidationError``) with a descriptive message.
- **CLI entry points** (modules with a ``main()`` function) catch errors,
  print them to ``stderr``, and exit via ``sys.exit(1)``.
"""

import json
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
    except OSError as e:
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
    except OSError as e:
        return None, f"Error loading YAML from {file_path}: {e}"


def load_json_safe(file_path: str) -> tuple[Any | None, str | None]:
    """Safely load JSON file with consistent error handling.

    Args:
        file_path: Path to JSON file to load

    Returns:
        Tuple of (data, error_msg) where:
        - data: Parsed JSON data if successful, None otherwise
        - error_msg: Error message if failed, None otherwise

    Example:
        >>> data, error = load_json_safe("trace.json")
        >>> if error:
        ...     print(f"Failed: {error}")
        ... else:
        ...     process(data)
    """
    try:
        with open(file_path) as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {file_path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON syntax in {file_path}: {e}"
    except PermissionError:
        return None, f"Permission denied: {file_path}"
    except OSError as e:
        return None, f"Error loading JSON from {file_path}: {e}"


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
    except OSError as e:
        return f"Error writing YAML to {file_path}: {e}"
