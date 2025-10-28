"""Requirement validation logic."""

def _parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown file content as string

    Returns:
        Tuple of (frontmatter_dict, body_content) or (None, content) if no frontmatter
    """
    if not content.startswith("---"):
        return (None, content)

    # Find the closing ---
    lines = content.split("\n")
    if len(lines) < 3:
        return (None, content)

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return (None, content)

    # Parse frontmatter (simple key: value parsing)
    frontmatter = {}
    for i in range(1, end_idx):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            continue

        parts = line.split(":", 1)
        key = parts[0].strip()
        value = parts[1].strip()

        # Handle lists [item1, item2]
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]
            items = [item.strip() for item in value.split(",")]
            frontmatter[key] = items
        else:
            frontmatter[key] = value

    # Body is everything after the closing ---
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
