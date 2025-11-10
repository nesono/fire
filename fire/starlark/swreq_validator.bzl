"""Validation logic for software requirements."""

load(":swreq_parser.bzl", "swreq_parser")

def _validate_requirement_id(req_id):
    """Validate software requirement ID format.

    Expected format: REQ_<COMPONENT>_<NAME>
    - Must start with REQ_
    - Use uppercase letters, digits, and underscores only

    Args:
        req_id: Requirement ID string

    Returns:
        None if valid, error message if invalid
    """
    if not req_id:
        return "requirement ID cannot be empty"

    if not req_id.startswith("REQ_"):
        return "software requirement ID must start with 'REQ_' (got '{}')".format(req_id)

    # Check valid characters (uppercase, digits, underscores)
    for c in req_id.elems():
        if not (c.isupper() or c.isdigit() or c == "_"):
            return "software requirement ID must use UPPER_CASE with underscores (invalid character '{}' in '{}')".format(c, req_id)

    # Check it has more than just "REQ_"
    if len(req_id) <= 4:
        return "software requirement ID too short: '{}'".format(req_id)

    return None

def _validate_parent_reference(parent):
    """Validate parent system requirement reference.

    Expected format: path/to/file.md#ANCHOR

    Args:
        parent: Parent reference string

    Returns:
        None if valid, error message if invalid
    """
    if not parent:
        return "parent reference cannot be empty"

    # Must contain # for anchor
    if "#" not in parent:
        return "parent reference must include anchor (e.g., 'path/to/sysreq.md#REQ_ID'), got '{}'".format(parent)

    parts = parent.split("#")
    if len(parts) != 2:
        return "parent reference must have exactly one '#' separator, got '{}'".format(parent)

    file_path = parts[0]
    anchor = parts[1]

    if not file_path:
        return "parent reference must have file path before '#', got '{}'".format(parent)

    if not anchor:
        return "parent reference must have anchor after '#', got '{}'".format(parent)

    # File path should end with .md
    if not file_path.endswith(".md"):
        return "parent reference file should end with '.md', got '{}'".format(file_path)

    return None

def _validate_sil(sil):
    """Validate Safety Integrity Level (SIL).

    Accepts: SIL-1/2/3/4, ASIL-A/B/C/D, DAL-A/B/C/D/E, QM, None

    Args:
        sil: Safety Integrity Level string or None

    Returns:
        None if valid, error message if invalid
    """

    # None is valid (no SIL requirement)
    if sil == None:
        return None

    if type(sil) != "string":
        return "SIL must be a string or None, got {}".format(type(sil))

    if len(sil) == 0:
        return "SIL field cannot be empty string (use None for no SIL)"

    if len(sil.strip()) == 0:
        return "SIL cannot be whitespace only"

    # Accept common formats but don't enforce strict list
    # This allows flexibility for different standards
    return None

def _validate_sec(sec):
    """Validate security_related flag.

    Args:
        sec: Boolean indicating if requirement is security-related

    Returns:
        None if valid, error message if invalid
    """
    if type(sec) != "bool":
        return "Sec (security_related) must be a boolean (true/false), got {}".format(type(sec))

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

    return None

def _validate_frontmatter(frontmatter):
    """Validate software requirements frontmatter.

    Required fields:
    - component: string
    - version: positive integer (as string)
    - sil: SIL level string
    - security_related: boolean

    Optional fields:
    - system_function: path to system function document

    Args:
        frontmatter: Dictionary of frontmatter fields

    Returns:
        None if valid, error message if invalid
    """
    if not frontmatter:
        return "software requirements document must have frontmatter"

    # Check required fields
    required_fields = ["component", "version", "sil", "security_related"]
    for field in required_fields:
        if field not in frontmatter:
            return "missing required frontmatter field: {}".format(field)

    # Validate component name
    component = frontmatter["component"]
    if not component or len(component.strip()) == 0:
        return "component name cannot be empty"

    # Validate version (should be positive integer as string)
    version = frontmatter["version"]
    if type(version) == "string":
        if not version.isdigit():
            return "version must be a positive integer, got '{}'".format(version)
    elif type(version) == "int":
        if version <= 0:
            return "version must be a positive integer, got {}".format(version)
    else:
        return "version must be an integer, got {}".format(type(version))

    # Validate SIL
    sil = frontmatter["sil"]
    if sil != None:  # Allow None for no SIL
        if type(sil) != "string":
            return "sil must be a string or None"
        err = _validate_sil(sil)
        if err:
            return err

    # Validate security_related
    security_related = frontmatter["security_related"]
    if type(security_related) != "bool":
        return "security_related must be a boolean (true/false), got {}".format(type(security_related))

    # Validate optional system_function if present
    if "system_function" in frontmatter:
        system_function = frontmatter["system_function"]
        if system_function and not system_function.endswith(".md"):
            return "system_function path should end with '.md', got '{}'".format(system_function)

    return None

def _validate_requirement(req, all_req_ids):
    """Validate a single software requirement.

    Args:
        req: Requirement dictionary
        all_req_ids: Set of all requirement IDs for duplicate checking

    Returns:
        None if valid, error message if invalid
    """

    # Check required fields
    required_fields = ["id", "parent", "sil", "sec", "description"]
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

    # Validate parent reference
    err = _validate_parent_reference(req["parent"])
    if err:
        return "requirement '{}': {}".format(req_id, err)

    # Validate SIL
    err = _validate_sil(req["sil"])
    if err:
        return "requirement '{}': {}".format(req_id, err)

    # Validate Sec
    err = _validate_sec(req["sec"])
    if err:
        return "requirement '{}': {}".format(req_id, err)

    # Validate description
    err = _validate_description(req["description"], req_id)
    if err:
        return err

    return None

def _validate_internal_references(requirements):
    """Validate internal references between requirements.

    Check that any requirement ID mentioned in descriptions exists.

    Args:
        requirements: List of requirement dictionaries

    Returns:
        None if valid, error message if invalid
    """

    # Build set of all requirement IDs
    req_ids = {}
    for req in requirements:
        req_ids[req["id"]] = True

    # Check each requirement's description for references
    for req in requirements:
        description = req["description"]

        # Look for REQ_ patterns in description
        # This is a simple heuristic - we look for REQ_ followed by uppercase/underscore
        parts = description.split("REQ_")
        for i in range(1, len(parts)):
            # Extract the referenced ID
            ref_id = "REQ_"
            for c in parts[i].elems():
                if c.isupper() or c.isdigit() or c == "_":
                    ref_id += c
                else:
                    break

            # Check if this looks like a valid requirement reference
            if len(ref_id) > 4:  # More than just "REQ_"
                if ref_id not in req_ids:
                    return "requirement '{}' references unknown requirement '{}' in description".format(
                        req["id"],
                        ref_id,
                    )

    return None

def validate_swreq(content):
    """Validate a software requirements document.

    Args:
        content: Full markdown content as string

    Returns:
        None if valid, error message if invalid
    """

    # Parse document
    frontmatter, requirements = swreq_parser.parse(content)

    # Validate frontmatter
    err = _validate_frontmatter(frontmatter)
    if err:
        return err

    # Check we have at least one requirement
    if len(requirements) == 0:
        return "software requirements document must contain at least one requirement"

    # Validate each requirement
    all_req_ids = {}
    for req in requirements:
        err = _validate_requirement(req, all_req_ids)
        if err:
            return err

    # Validate internal references
    err = _validate_internal_references(requirements)
    if err:
        return err

    return None

# Export validator
swreq_validator = struct(
    validate = validate_swreq,
    validate_requirement_id = _validate_requirement_id,
    validate_parent_reference = _validate_parent_reference,
    validate_sil = _validate_sil,
)
