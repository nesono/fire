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
    ```

    Derived from [PARENT](/path/to/parent.md?version=2#PARENT).
    Description text follows after YAML block...

    Note: parent and parent_version fields are deprecated - use markdown links instead.

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
    if "parent" in yaml_dict:
        req["parent"] = yaml_dict["parent"]

    if "parent_version" in yaml_dict:
        req["parent_version"] = yaml_dict["parent_version"]

    if "sil" in yaml_dict:
        req["sil"] = yaml_dict["sil"]

    if "sec" in yaml_dict:
        req["sec"] = yaml_dict["sec"]

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

def parse_swreq(content):
    """Parse software requirements document.

    Expects format:
    ```
    ---
    system_function: /path/to/sysarch.md
    ---

    # Software Requirements: Component Name

    ## REQ_ID_1

    ```yaml
    sil: ASIL-D
    sec: false
    ```

    Derived from [REQ-PARENT](/path/to/sysreq.md?version=2#SYSREQ_ID).
    The component shall perform the required function...

    ---

    ## REQ_ID_2

    ```yaml
    sil: ASIL-C
    sec: true
    ```

    Derived from [REQ-ANOTHER](/path/to/sysreq.md?version=1#ANOTHER_ID).
    Description text for REQ_ID_2...
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
            # Use header as the requirement ID
            req["id"] = header
            requirements.append(req)

    return (frontmatter, requirements)

# Export parser
swreq_parser = struct(
    parse = parse_swreq,
    parse_requirement_section = _parse_requirement_section,
)
