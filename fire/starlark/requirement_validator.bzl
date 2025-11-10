"""Requirement validation logic."""

load(":markdown_parser.bzl", "markdown_parser")
load(":reference_validator.bzl", "reference_validator")
load(":version_validator.bzl", "version_validator")

def _is_valid_yaml_key(s):
    """Check if string is valid YAML dict key (alphanumeric with _ or -)."""
    if not s:
        return False
    for c in s.elems():
        if not (c.isalnum() or c in "_-"):
            return False
    return True

def _parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content.

    Handles complex YAML including dicts in lists.

    Args:
        content: Full markdown file content as string

    Returns:
        Tuple of (frontmatter_dict, body_content) or (None, content) if no frontmatter
    """
    if not content.startswith("---"):
        return (None, content)

    lines = content.split("\n")
    if len(lines) < 3:
        return (None, content)

    # Find closing ---
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return (None, content)

    # Parse frontmatter with support for nested structures
    frontmatter = {}
    current_key = None
    current_list_key = None
    current_dict = None
    base_indent = 0

    for i in range(1, end_idx):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip())

        # List item (starts with -)
        if stripped.startswith("-"):
            rest = stripped[1:].strip()

            # Check if this is a dict item (has key: value after -)
            is_dict_item = False
            if ":" in rest:
                # Check it's not a Bazel label (//...:...) or ISO standard
                if not rest.startswith("//") and not rest.startswith("ISO "):
                    parts = rest.split(":", 1)
                    key_part = parts[0].strip()

                    # Check if it looks like a dict key (alphanumeric with _ or -)
                    if _is_valid_yaml_key(key_part):
                        is_dict_item = True

            if is_dict_item:
                # Dict item in list
                parts = rest.split(":", 1)
                dict_key = parts[0].strip()
                dict_value = parts[1].strip() if len(parts) > 1 else ""

                # Convert dict_value to int if it looks like a number
                if dict_value and dict_value.isdigit():
                    dict_value = int(dict_value)

                # Start new dict
                current_dict = {dict_key: dict_value}
                if current_key and current_list_key:
                    if current_list_key not in frontmatter[current_key]:
                        frontmatter[current_key][current_list_key] = []
                    frontmatter[current_key][current_list_key].append(current_dict)
            else:
                # Simple string item or inline list [a, b, c]
                if rest.startswith("[") and rest.endswith("]"):
                    # Inline list
                    rest = rest[1:-1]
                    items = [item.strip() for item in rest.split(",")]
                    if current_key and type(frontmatter.get(current_key)) == "string":
                        frontmatter[current_key] = items
                else:
                    # Single item
                    if current_key and current_list_key:
                        if current_list_key not in frontmatter[current_key]:
                            frontmatter[current_key][current_list_key] = []
                        frontmatter[current_key][current_list_key].append(rest)
                current_dict = None

            # Key-value pair
        elif ":" in stripped:
            parts = stripped.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            if indent == 0 or indent == base_indent:
                # Top-level key
                current_key = key
                if value:
                    # Strip surrounding quotes from string values
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]

                    # Try to convert to int if it looks like a number
                    if value.isdigit():
                        frontmatter[key] = int(value)
                        # Handle booleans

                    elif value.lower() == "true":
                        frontmatter[key] = True
                    elif value.lower() == "false":
                        frontmatter[key] = False
                        # Handle inline lists [a, b, c]

                    elif value.startswith("[") and value.endswith("]"):
                        value = value[1:-1]
                        frontmatter[key] = [item.strip() for item in value.split(",")]
                    else:
                        frontmatter[key] = value
                else:
                    frontmatter[key] = {}
                    current_list_key = None
                base_indent = indent
                current_dict = None
            elif current_dict and indent > base_indent + 2:
                # Additional key in current dict item
                if value.isdigit():
                    current_dict[key] = int(value)
                else:
                    current_dict[key] = value
            elif current_key and indent > base_indent:
                # Nested key under current_key
                current_dict = None
                if value:
                    if value.isdigit():
                        frontmatter[current_key][key] = int(value)
                    else:
                        frontmatter[current_key][key] = value
                else:
                    frontmatter[current_key][key] = []
                    current_list_key = key

    body = "\n".join(lines[end_idx + 1:])
    return (frontmatter, body)

def _validate_requirement_id(req_id):
    """Validate requirement ID format.

    Args:
        req_id: Requirement ID string

    Returns:
        None if valid, error message if invalid
    """
    if not req_id:
        return "requirement ID cannot be empty"

    # Must start with letter or underscore
    if not req_id[0].isalpha() and req_id[0] != "_":
        return "requirement ID must start with letter or underscore"

    # Check valid characters
    for c in req_id.elems():
        if not (c.isalnum() or c in ["_", "-"]):
            return "requirement ID contains invalid character '{}'".format(c)

    return None

def _validate_requirement_type(req_type):
    """Validate requirement type.

    Args:
        req_type: Requirement type string

    Returns:
        None if valid, error message if invalid
    """
    valid_types = [
        "functional",
        "non-functional",
        "safety",
        "interface",
        "constraint",
        "performance",
    ]

    if req_type not in valid_types:
        return "invalid requirement type '{}'. Valid types: {}".format(
            req_type,
            ", ".join(valid_types),
        )

    return None

def _validate_requirement_status(status):
    """Validate requirement status.

    Args:
        status: Requirement status string

    Returns:
        None if valid, error message if invalid
    """
    valid_statuses = [
        "draft",
        "proposed",
        "approved",
        "implemented",
        "verified",
        "deprecated",
    ]

    if status not in valid_statuses:
        return "invalid requirement status '{}'. Valid statuses: {}".format(
            status,
            ", ".join(valid_statuses),
        )

    return None

def _validate_requirement_priority(priority):
    """Validate requirement priority.

    Args:
        priority: Requirement priority string

    Returns:
        None if valid, error message if invalid
    """
    valid_priorities = ["low", "medium", "high", "critical"]

    if priority not in valid_priorities:
        return "invalid requirement priority '{}'. Valid priorities: {}".format(
            priority,
            ", ".join(valid_priorities),
        )

    return None

def _validate_sil(sil):
    """Validate Safety Integrity Level (SIL).

    Args:
        sil: Safety Integrity Level string (e.g., "ASIL-D", "SIL-3", "DAL-A")

    Returns:
        None if valid, error message if invalid
    """

    # SIL can be any non-empty string to support various standards
    # Examples: ASIL-A/B/C/D (ISO 26262), SIL-1/2/3/4 (IEC 61508),
    # DAL-A/B/C/D/E (DO-178C), QM (Quality Management)
    if type(sil) != "string":
        return "SIL must be a string, got {}".format(type(sil))

    # In Starlark, empty string "" is truthy, so we need to check length
    if len(sil) == 0:
        return "SIL field cannot be empty"

    if len(sil.strip()) == 0:
        return "SIL cannot be whitespace only"

    return None

def _validate_security_related(security_related):
    """Validate security_related flag.

    Args:
        security_related: Boolean indicating if requirement is security-related

    Returns:
        None if valid, error message if invalid
    """
    if type(security_related) != "bool":
        return "security_related must be a boolean (true/false), got {}".format(type(security_related))

    return None

def _validate_frontmatter(frontmatter):
    """Validate requirement frontmatter.

    Args:
        frontmatter: Dictionary of frontmatter fields

    Returns:
        None if valid, error message if invalid
    """
    if not frontmatter:
        return "requirement must have frontmatter"

    # Check required fields
    required_fields = ["id", "title", "type", "status"]
    for field in required_fields:
        if field not in frontmatter:
            return "missing required field: {}".format(field)

    # Validate ID
    err = _validate_requirement_id(frontmatter["id"])
    if err:
        return err

    # Validate type
    err = _validate_requirement_type(frontmatter["type"])
    if err:
        return err

    # Validate status
    err = _validate_requirement_status(frontmatter["status"])
    if err:
        return err

    # Validate priority if present
    if "priority" in frontmatter:
        err = _validate_requirement_priority(frontmatter["priority"])
        if err:
            return err

    # Validate SIL if present
    if "sil" in frontmatter:
        err = _validate_sil(frontmatter["sil"])
        if err:
            return err

    # Validate security_related if present
    if "security_related" in frontmatter:
        err = _validate_security_related(frontmatter["security_related"])
        if err:
            return err

    # Validate title is not empty
    if not frontmatter["title"]:
        return "requirement title cannot be empty"

    return None

def _validate_body(body, req_id):
    """Validate requirement body content.

    Args:
        body: Markdown body content
        req_id: Requirement ID for context

    Returns:
        None if valid, error message if invalid
    """
    if not body or not body.strip():
        return "requirement '{}' has empty body".format(req_id)

    # Body should contain some description
    if len(body.strip()) < 10:
        return "requirement '{}' body is too short (minimum 10 characters)".format(req_id)

    return None

def validate_requirement(content):
    """Validate a requirement document.

    Args:
        content: Full markdown content as string

    Returns:
        None if valid, error message if invalid
    """

    # Parse frontmatter
    frontmatter, body = _parse_frontmatter(content)

    # Validate frontmatter
    err = _validate_frontmatter(frontmatter)
    if err:
        return err

    # Validate references
    err = reference_validator.validate(frontmatter)
    if err:
        return err

    # Validate versioning and change management
    err = version_validator.validate(frontmatter)
    if err:
        return err

    # Validate markdown references in body
    frontmatter_refs = frontmatter.get("references", None)
    err = markdown_parser.validate_references(body, frontmatter_refs)
    if err:
        return err

    # Validate body
    err = _validate_body(body, frontmatter["id"])
    if err:
        return err

    return None

# Export validation function
requirement_validator = struct(
    validate = validate_requirement,
    parse_frontmatter = _parse_frontmatter,
)
