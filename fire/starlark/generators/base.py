"""Base utilities for code generators."""

from typing import Any

# Type mappings for each language
TYPE_MAPS = {
    "cpp": {
        "i32": "int32_t",
        "i64": "int64_t",
        "u32": "uint32_t",
        "u64": "uint64_t",
        "f32": "float",
        "f64": "double",
        "string": "const char*",
        "bool": "bool",
    },
    "python": {
        "i32": "int",
        "i64": "int",
        "u32": "int",
        "u64": "int",
        "f32": "float",
        "f64": "float",
        "string": "str",
        "bool": "bool",
    },
    "go": {
        "i32": "int32",
        "i64": "int64",
        "u32": "uint32",
        "u64": "uint64",
        "f32": "float32",
        "f64": "float64",
        "string": "string",
        "bool": "bool",
    },
    "rust": {
        "i32": "i32",
        "i64": "i64",
        "u32": "u32",
        "u64": "u64",
        "f32": "f32",
        "f64": "f64",
        "string": "&'static str",
        "bool": "bool",
    },
    "java": {
        "i32": "int",
        "i64": "long",
        "u32": "int",  # Java doesn't have unsigned
        "u64": "long",  # Java doesn't have unsigned
        "f32": "float",
        "f64": "double",
        "string": "String",
        "bool": "boolean",
    },
}


def get_type(language: str, param_type: str) -> str:
    """Get the language-specific type for a parameter type."""
    return TYPE_MAPS[language].get(param_type, param_type)


def pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def camel_case(name: str) -> str:
    """Convert snake_case to camelCase."""
    words = name.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


def format_value(param_type: str, value: Any, language: str) -> str:
    """Format a value for the target language."""
    if param_type == "string":
        return f'"{value}"'
    elif param_type == "bool":
        if language in ["cpp", "go", "rust", "java"]:
            return "true" if value else "false"
        else:  # Python
            return str(value)
    else:
        return str(value)
