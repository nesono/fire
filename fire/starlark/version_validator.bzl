"""Simple version tracking for requirement derivation."""

def _validate_version(version):
    """Validate version is a positive integer.

    Args:
        version: Version value

    Returns:
        None if valid, error message if invalid
    """
    if type(version) != "int":
        return "version must be an integer, got {}".format(type(version))

    if version < 1:
        return "version must be a positive integer (>= 1), got {}".format(version)

    return None

def _validate_changelog_entry(entry, index):
    """Validate a single changelog entry.

    Args:
        entry: Dictionary containing changelog entry fields
        index: Index of the entry (for error messages)

    Returns:
        None if valid, error message if invalid
    """
    if type(entry) != "dict":
        return "changelog entry {} must be a dictionary".format(index)

    # Required fields
    required = ["version", "description"]
    for field in required:
        if field not in entry:
            return "changelog entry {} missing required field: {}".format(index, field)

    # Validate version
    err = _validate_version(entry["version"])
    if err:
        return "changelog entry {}: {}".format(index, err)

    # Validate description is not empty
    if type(entry["description"]) != "string":
        return "changelog entry {}: description must be a string".format(index)

    if not entry["description"]:
        return "changelog entry {}: description cannot be empty".format(index)

    return None

def _validate_changelog(changelog):
    """Validate changelog.

    Args:
        changelog: List of changelog entry dictionaries

    Returns:
        None if valid, error message if invalid
    """
    if type(changelog) != "list":
        return "changelog must be a list"

    if len(changelog) == 0:
        return "changelog cannot be empty"

    # Validate each entry
    for i, entry in enumerate(changelog):
        err = _validate_changelog_entry(entry, i)
        if err:
            return err

    # Check versions are in descending order (newest first)
    for i in range(len(changelog) - 1):
        curr_version = changelog[i]["version"]
        next_version = changelog[i + 1]["version"]

        if curr_version <= next_version:
            return "changelog versions must be in descending order (newest first), but {} comes before {}".format(
                curr_version,
                next_version,
            )

    return None

def _validate_requirement_reference_with_version(ref):
    """Validate a requirement reference that may include version tracking.

    Args:
        ref: Either a string (simple ref) or dict with 'id' and 'version'

    Returns:
        None if valid, error message if invalid
    """
    if type(ref) == "string":
        # Simple string reference (backward compatible)
        return None
    elif type(ref) == "dict":
        # Reference with version tracking
        if "id" not in ref:
            return "requirement reference dict must have 'id' field"

        req_id = ref["id"]
        if type(req_id) != "string":
            return "requirement reference 'id' must be a string"

        # Validate requirement ID format
        if not req_id:
            return "requirement reference 'id' cannot be empty"

        if not req_id[0].isalpha() and req_id[0] != "_":
            return "requirement reference '{}' must start with letter or underscore".format(req_id)

        for c in req_id.elems():
            if not (c.isalnum() or c in ["_", "-"]):
                return "requirement reference '{}' contains invalid character '{}'".format(req_id, c)

        # Validate version if present
        if "version" in ref:
            err = _validate_version(ref["version"])
            if err:
                return "requirement reference '{}': {}".format(req_id, err)

        return None
    else:
        return "requirement reference must be string or dict, got {}".format(type(ref))

def validate_versioning(frontmatter):
    """Validate simple integer versioning.

    Args:
        frontmatter: Dictionary of requirement frontmatter

    Returns:
        None if valid, error message if invalid
    """

    # Validate top-level version if present
    if "version" in frontmatter:
        err = _validate_version(frontmatter["version"])
        if err:
            return err

    # Validate changelog if present
    if "changelog" in frontmatter:
        err = _validate_changelog(frontmatter["changelog"])
        if err:
            return err

        # If both version and changelog are present, version must match the first changelog entry
        if "version" in frontmatter:
            if frontmatter["version"] != frontmatter["changelog"][0]["version"]:
                return "version {} does not match latest changelog entry version {}".format(
                    frontmatter["version"],
                    frontmatter["changelog"][0]["version"],
                )

    # Validate requirement references with version tracking
    if "references" in frontmatter:
        refs = frontmatter.get("references", {})
        if type(refs) == "dict" and "requirements" in refs:
            req_refs = refs["requirements"]
            if type(req_refs) == "list":
                for ref in req_refs:
                    err = _validate_requirement_reference_with_version(ref)
                    if err:
                        return err

    return None

# Export validation functions
version_validator = struct(
    validate = validate_versioning,
    validate_version = _validate_version,
)
