"""Requirement validation logic."""

def _split_by_h2_sections(body):
    """Split markdown body by ## level-2 headers.

    Args:
        body: Markdown body content

    Returns:
        List of (header_text, section_content) tuples
    """
    lines = body.split("\n")
    sections = []
    current_header = None
    current_lines = []

    for line in lines:
        if line.startswith("## "):
            # Save previous section
            if current_header != None:
                sections.append((current_header, "\n".join(current_lines)))

            # Start new section
            current_header = line[3:].strip()
            current_lines = []
        elif current_header != None:
            current_lines.append(line)

    # Save last section
    if current_header != None:
        sections.append((current_header, "\n".join(current_lines)))

    return sections

def _parse_inline_metadata(section_content):
    """Parse pipe-separated inline metadata from requirement section.

    Expects format: Key1: value1 | Key2: value2 | Parent: [REQ-ID](path)

    Args:
        section_content: Content of one requirement section

    Returns:
        Tuple of (metadata_dict, remaining_content) or (None, section_content) if no metadata line
    """
    lines = section_content.split("\n")

    # Find FIRST non-empty line - check if it's metadata
    # Metadata must be on the first line after heading (not inside YAML blocks)
    metadata_line = None
    metadata_line_idx = -1

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue  # Skip empty lines

        # This is the first non-empty line
        # Check if it's pipe-separated metadata or starts with a YAML block
        if stripped == "```yaml" or stripped.startswith("```"):
            # It's a YAML block, not inline metadata
            return (None, section_content)

        # Check for pipe-separated format OR single Key: value
        if "|" in stripped:
            metadata_line = stripped
            metadata_line_idx = i
            break
        elif ":" in stripped and not stripped.startswith("#"):
            # Check if it's a known metadata field
            parts = stripped.split(":", 1)
            key = parts[0].strip().lower()
            known_fields = ["sil", "sec", "version", "parent"]
            if len(parts) == 2 and key in known_fields:
                metadata_line = stripped
                metadata_line_idx = i
                break

        # First non-empty line is not metadata
        return (None, section_content)

    if not metadata_line:
        return (None, section_content)

    # Parse pipe-separated fields
    metadata_dict = {}
    fields = metadata_line.split("|")

    for field in fields:
        field = field.strip()
        if not field or ":" not in field:
            continue

        # Split by first colon
        colon_idx = field.find(":")
        key = field[:colon_idx].strip().lower()  # Normalize to lowercase
        value = field[colon_idx + 1:].strip()

        # Keep markdown links as-is (for parent references)
        if value.startswith("[") and "](" in value:
            metadata_dict[key] = value
            continue

        # Convert booleans
        if value.lower() == "true":
            metadata_dict[key] = True
        elif value.lower() == "false":
            metadata_dict[key] = False
        elif value.lower() == "none":
            metadata_dict[key] = None
            # Try to parse as integer

        elif value.isdigit():
            metadata_dict[key] = int(value)
        else:
            metadata_dict[key] = value

    # Return metadata dict and remaining content without the metadata line
    remaining_lines = lines[:metadata_line_idx] + lines[metadata_line_idx + 1:]
    remaining_content = "\n".join(remaining_lines)

    return (metadata_dict, remaining_content)

def _parse_yaml_block(section_content):
    """Parse YAML code block from requirement section.

    TODO: DEPRECATED - YAML blocks are replaced by pipe-separated inline metadata.
    Remove this function after updating to parse inline metadata format.

    Looks for ```yaml ... ``` block and parses key:value pairs.

    Args:
        section_content: Content of one requirement section

    Returns:
        Tuple of (yaml_dict, remaining_content) or (None, section_content) if no YAML block
    """
    lines = section_content.split("\n")

    # Find ```yaml block
    yaml_start = -1
    yaml_end = -1

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "```yaml" and yaml_start == -1:
            yaml_start = i
        elif stripped == "```" and yaml_start != -1 and yaml_end == -1:
            yaml_end = i
            break

    if yaml_start == -1 or yaml_end == -1:
        return (None, section_content)

    # Parse YAML content (simple key: value format)
    yaml_dict = {}
    for i in range(yaml_start + 1, yaml_end):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            continue

        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            # Strip quotes
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            # Convert booleans
            if value.lower() == "true":
                yaml_dict[key] = True
            elif value.lower() == "false":
                yaml_dict[key] = False
            elif value.lower() == "none":
                yaml_dict[key] = None
                # Try to parse as integer

            elif value.isdigit():
                yaml_dict[key] = int(value)
            else:
                yaml_dict[key] = value

    # Return YAML dict and remaining content after the block
    remaining_lines = lines[:yaml_start] + lines[yaml_end + 1:]
    remaining_content = "\n".join(remaining_lines)

    return (yaml_dict, remaining_content)

def _parse_requirement_section(section_content):
    """Parse a single requirement section.

    Supports two formats:
    1. NEW: Pipe-separated inline metadata: SIL: ASIL-D | Sec: false | Parent: [REQ-ID](path)
    2. OLD (TODO: DEPRECATED): YAML block format

    Args:
        section_content: Content of one requirement section

    Returns:
        Dictionary with requirement fields or None if invalid
    """
    req = {}

    # Try to parse inline metadata first (new format)
    metadata_dict, remaining_content = _parse_inline_metadata(section_content)

    # TODO: Fallback to YAML block format (deprecated) - remove after migration
    if not metadata_dict:
        yaml_dict, remaining_content = _parse_yaml_block(section_content)
        metadata_dict = yaml_dict

    if not metadata_dict:
        # No metadata found - return empty (invalid requirement)
        return None

    # Extract fields from metadata
    if "sil" in metadata_dict:
        req["sil"] = metadata_dict["sil"]

    if "sec" in metadata_dict:
        req["sec"] = metadata_dict["sec"]

    if "version" in metadata_dict:
        req["version"] = metadata_dict["version"]

    # Extract parent if present (in new inline format)
    if "parent" in metadata_dict:
        req["parent"] = metadata_dict["parent"]

    # Extract description from remaining content
    description_lines = []
    for line in remaining_content.split("\n"):
        stripped = line.strip()

        # Skip empty lines and horizontal rules
        if not stripped or stripped == "---":
            continue
        description_lines.append(stripped)

    # Combine description lines
    if description_lines:
        req["description"] = " ".join(description_lines)

    return req if req else None

def parse_requirements(content):
    """Parse system requirements document.

    Expects format:
    ```
    # System Requirements: Component Name

    ## REQ-ID-1

    ```yaml
    sil: ASIL-D
    sec: false
    version: 1
    ```

    **Title**

    Description text...

    ---

    ## REQ-ID-2

    ```yaml
    sil: ASIL-C
    sec: true
    version: 1
    ```

    Description text for REQ-ID-2...
    ```

    Args:
        content: Full markdown content as string

    Returns:
        List of requirement dicts
    """

    # Split body by ## sections (no frontmatter)
    sections = _split_by_h2_sections(content)

    # Parse each requirement section
    requirements = []
    for header, section_content in sections:
        req = _parse_requirement_section(section_content)
        if req:
            # Use header as the requirement ID
            req["id"] = header
            requirements.append(req)

    return requirements

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

def _validate_sil(sil):
    """Validate Safety Integrity Level (SIL).

    Args:
        sil: Safety Integrity Level string (e.g., "ASIL-D", "SIL-3", "DAL-A")

    Returns:
        None if valid, error message if invalid
    """

    # Valid SIL values supporting various standards
    # ASIL: Automotive Safety Integrity Level (ISO 26262)
    # SIL: Safety Integrity Level (IEC 61508)
    # DAL: Design Assurance Level (DO-178C)
    # QM: Quality Management (not safety-related)
    valid_sils = [
        "ASIL-A",
        "ASIL-B",
        "ASIL-C",
        "ASIL-D",
        "SIL-1",
        "SIL-2",
        "SIL-3",
        "SIL-4",
        "DAL-A",
        "DAL-B",
        "DAL-C",
        "DAL-D",
        "DAL-E",
        "QM",
    ]

    if type(sil) != "string":
        return "SIL must be a string, got {}".format(type(sil))

    # In Starlark, empty string "" is truthy, so we need to check length
    if len(sil) == 0:
        return "SIL field cannot be empty"

    if len(sil.strip()) == 0:
        return "SIL cannot be whitespace only"

    if sil not in valid_sils:
        return "invalid SIL value '{}', must be one of: {}".format(sil, ", ".join(valid_sils))

    return None

def _validate_sec(sec):
    """Validate security-related flag.

    Args:
        sec: Boolean indicating if requirement is security-related

    Returns:
        None if valid, error message if invalid
    """
    if type(sec) != "bool":
        return "sec must be a boolean (true/false), got {}".format(type(sec))

    return None

def _validate_version(version):
    """Validate version number.

    Args:
        version: Version number (should be positive integer)

    Returns:
        None if valid, error message if invalid
    """
    if type(version) != "int":
        return "version must be an integer, got {}".format(type(version))

    if version <= 0:
        return "version must be positive, got {}".format(version)

    return None

def _validate_description(description, req_id):
    """Validate requirement description.

    Args:
        description: Requirement description text
        req_id: Requirement ID for error context

    Returns:
        None if valid, error message if invalid
    """
    if not description:
        return "requirement '{}' has empty description".format(req_id)

    # Description should be substantial
    if len(description.strip()) < 10:
        return "requirement '{}' description is too short (minimum 10 characters)".format(req_id)

    # Check for title (bold text) in description
    if "**" not in description:
        return "requirement '{}' missing title (must have bold text like **Title**)".format(req_id)

    return None

def _validate_requirement(req, all_req_ids):
    """Validate a single system requirement.

    Args:
        req: Requirement dictionary
        all_req_ids: Set of all requirement IDs for duplicate checking

    Returns:
        None if valid, error message if invalid
    """

    # Check required fields
    required_fields = ["id", "sil", "sec", "version", "description"]
    for field in required_fields:
        if field not in req:
            return "requirement missing required field: {}".format(field)

    req_id = req["id"]

    # Validate ID format
    err = _validate_requirement_id(req_id)
    if err:
        return err

    # Check for duplicate IDs
    if req_id in all_req_ids:
        return "duplicate requirement ID: '{}'".format(req_id)
    all_req_ids[req_id] = True

    # Validate SIL
    err = _validate_sil(req["sil"])
    if err:
        return "requirement '{}': {}".format(req_id, err)

    # Validate Sec
    err = _validate_sec(req["sec"])
    if err:
        return "requirement '{}': {}".format(req_id, err)

    # Validate version
    err = _validate_version(req["version"])
    if err:
        return "requirement '{}': {}".format(req_id, err)

    # Validate description
    err = _validate_description(req["description"], req_id)
    if err:
        return err

    return None

def validate_requirement(content):
    """Validate a system requirements document.

    Args:
        content: Full markdown content as string

    Returns:
        None if valid, error message if invalid
    """

    # Parse document
    requirements = parse_requirements(content)

    # Check we have at least one requirement
    if len(requirements) == 0:
        return "system requirements document must contain at least one requirement"

    # Validate each requirement
    all_req_ids = {}
    for req in requirements:
        err = _validate_requirement(req, all_req_ids)
        if err:
            return err

    return None

# Export validation function
requirement_validator = struct(
    validate = validate_requirement,
    parse = parse_requirements,
    parse_yaml_block = _parse_yaml_block,
    validate_requirement_id = _validate_requirement_id,
    validate_sil = _validate_sil,
)
