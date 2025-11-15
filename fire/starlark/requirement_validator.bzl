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

def _parse_yaml_block(section_content):
    """Parse YAML code block from requirement section.

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
    """Parse a single requirement section (YAML block format).

    Expected format:
    ```yaml
    sil: ASIL-D
    sec: false
    version: 1
    ```

    Description text follows after YAML block...

    Args:
        section_content: Content of one requirement section

    Returns:
        Dictionary with requirement fields or None if invalid
    """
    req = {}

    # Parse YAML block
    yaml_dict, remaining_content = _parse_yaml_block(section_content)

    if not yaml_dict:
        # No YAML block found - return empty (invalid requirement)
        return None

    # Extract fields from YAML
    if "sil" in yaml_dict:
        req["sil"] = yaml_dict["sil"]

    if "sec" in yaml_dict:
        req["sec"] = yaml_dict["sec"]

    if "version" in yaml_dict:
        req["version"] = yaml_dict["version"]

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
