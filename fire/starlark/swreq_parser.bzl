"""Parser for software requirements documents."""

def _parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content.

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

    # Parse frontmatter (simple key: value format)
    frontmatter = {}
    for i in range(1, end_idx):
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
                frontmatter[key] = True
            elif value.lower() == "false":
                frontmatter[key] = False
            else:
                frontmatter[key] = value

    body = "\n".join(lines[end_idx + 1:])
    return (frontmatter, body)

def _extract_list_value(line, prefix):
    """Extract value after a list item prefix like '- **ID**:'.

    Args:
        line: Line containing the list item
        prefix: The prefix to extract (e.g., "- **ID**:")

    Returns:
        Extracted value or None
    """
    if not line.strip().startswith(prefix):
        return None

    # Extract everything after the prefix
    value = line[line.index(prefix) + len(prefix):].strip()
    return value if value else None

def _parse_bool(value):
    """Parse boolean value from string.

    Args:
        value: String value ("true", "false", "True", "False", etc.)

    Returns:
        Boolean value or None if not parseable
    """
    if not value:
        return None

    lower_value = value.lower().strip()
    if lower_value == "true":
        return True
    elif lower_value == "false":
        return False
    elif lower_value == "none":
        return None
    else:
        return None

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

def _parse_requirement_section(section_content):
    """Parse a single requirement section (list format).

    Args:
        section_content: Content of one requirement section

    Returns:
        Dictionary with requirement fields or None if invalid
    """
    req = {}
    lines = section_content.split("\n")

    # Accumulate multi-line description
    description_lines = []
    in_description = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines and horizontal rules
        if not stripped or stripped == "---":
            continue

        # Parse list items
        if stripped.startswith("- **ID**:"):
            req["id"] = _extract_list_value(line, "- **ID**:")
            in_description = False
        elif stripped.startswith("- **Parent**:"):
            req["parent"] = _extract_list_value(line, "- **Parent**:")
            in_description = False
        elif stripped.startswith("- **SIL**:"):
            sil_value = _extract_list_value(line, "- **SIL**:")

            # "None" as string should become None
            if sil_value and sil_value.lower() == "none":
                req["sil"] = None
            else:
                req["sil"] = sil_value
            in_description = False
        elif stripped.startswith("- **Sec**:"):
            sec_value = _extract_list_value(line, "- **Sec**:")
            req["sec"] = _parse_bool(sec_value)
            in_description = False
        elif stripped.startswith("- **Description**:"):
            desc_value = _extract_list_value(line, "- **Description**:")
            if desc_value:
                description_lines.append(desc_value)
            in_description = True
        elif in_description:
            # Continue multi-line description
            # Check if it's the start of a new field
            if stripped.startswith("- **"):
                in_description = False

                # Don't process this line, it's a new field
                continue
            else:
                description_lines.append(stripped)

    # Combine description lines
    if description_lines:
        req["description"] = " ".join(description_lines)

    return req if req else None

def parse_swreq(content):
    """Parse software requirements document.

    Expects format:
    ```
    ---
    component: hazard_zone
    version: 1
    sil: SIL-2
    security_related: true
    system_function: path/to/sysarch.md
    ---

    # Software Requirements: Component Name

    ## REQ_ID_1

    - **ID**: REQ_ID_1
    - **Parent**: path/to/sysreq.md#SYSREQ_ID
    - **SIL**: SIL-2
    - **Sec**: true
    - **Description**: The component shall...

    ---

    ## REQ_ID_2

    ...
    ```

    Args:
        content: Full markdown content as string

    Returns:
        Tuple of (frontmatter_dict, requirements_list)
        where requirements_list is a list of requirement dicts
    """

    # Parse frontmatter
    frontmatter, body = _parse_frontmatter(content)

    # Split body by ## sections
    sections = _split_by_h2_sections(body)

    # Parse each requirement section
    requirements = []
    for header, section_content in sections:
        req = _parse_requirement_section(section_content)
        if req:
            # Validate that header matches ID
            if "id" in req and req["id"] != header:
                # Header should match ID, but we'll be lenient and just use the ID from the list
                pass
            requirements.append(req)

    return (frontmatter, requirements)

# Export parser
swreq_parser = struct(
    parse = parse_swreq,
    parse_requirement_section = _parse_requirement_section,
)
