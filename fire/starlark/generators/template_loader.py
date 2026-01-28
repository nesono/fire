"""Jinja2 template environment setup for code generation."""

from pathlib import Path
from typing import Callable

from jinja2 import Environment, FileSystemLoader


def pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def camel_case(name: str) -> str:
    """Convert snake_case to camelCase."""
    words = name.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


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
        "u32": "int",
        "u64": "long",
        "f32": "float",
        "f64": "double",
        "string": "String",
        "bool": "boolean",
    },
}


def get_type(language: str) -> Callable[[str], str]:
    """Return a filter function that maps param types to language types."""

    def type_filter(param_type: str) -> str:
        return TYPE_MAPS[language].get(param_type, param_type)

    return type_filter


def format_value(language: str) -> Callable:
    """Return a filter function that formats values for the target language."""

    def value_filter(value, param_type: str) -> str:
        if param_type == "string":
            return f'"{value}"'
        elif param_type == "bool":
            if language in ["cpp", "go", "rust", "java"]:
                return "true" if value else "false"
            else:
                return str(value)
        else:
            return str(value)

    return value_filter


def create_environment() -> Environment:
    """Create a Jinja2 environment configured for code generation."""
    templates_dir = Path(__file__).parent.parent / "templates"

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # Register custom filters
    env.filters["pascal_case"] = pascal_case
    env.filters["camel_case"] = camel_case
    env.filters["upper"] = str.upper
    env.filters["lower"] = str.lower

    # Language-specific type filters
    for lang in TYPE_MAPS:
        env.filters[f"{lang}_type"] = get_type(lang)
        env.filters[f"{lang}_value"] = format_value(lang)

    return env


def render_template(template_name: str, **context) -> str:
    """Render a template with the given context."""
    env = create_environment()
    template = env.get_template(template_name)
    return template.render(**context)
