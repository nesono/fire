"""Cross-reference validation logic."""

def _validate_parameter_reference(param_ref):
    """Validate a parameter reference.

    Args:
        param_ref: Parameter reference string

    Returns:
        None if valid, error message if invalid
    """
    if not param_ref:
        return "parameter reference cannot be empty"

    # Parameter name should be a valid identifier
    if not param_ref[0].isalpha() and param_ref[0] != "_":
        return "parameter reference '{}' must start with letter or underscore".format(param_ref)

    for c in param_ref.elems():
        if not (c.isalnum() or c == "_"):
            return "parameter reference '{}' contains invalid character '{}'".format(param_ref, c)

    return None

def _validate_requirement_reference(req_ref):
    """Validate a requirement reference.

    Args:
        req_ref: Requirement reference (string or dict with 'id' and optional 'version')

    Returns:
        None if valid, error message if invalid
    """

    # Support both string and dict formats
    if type(req_ref) == "string":
        req_id = req_ref
    elif type(req_ref) == "dict":
        if "id" not in req_ref:
            return "requirement reference dict must have 'id' field"
        req_id = req_ref["id"]
        if type(req_id) != "string":
            return "requirement reference 'id' must be a string"
    else:
        return "requirement reference must be string or dict, got {}".format(type(req_ref))

    if not req_id:
        return "requirement reference cannot be empty"

    # Requirement ID format (same as requirement ID validation)
    if not req_id[0].isalpha() and req_id[0] != "_":
        return "requirement reference '{}' must start with letter or underscore".format(req_id)

    for c in req_id.elems():
        if not (c.isalnum() or c in ["_", "-"]):
            return "requirement reference '{}' contains invalid character '{}'".format(req_id, c)

    return None

def _validate_test_reference(test_ref):
    """Validate a test reference (Bazel label).

    Args:
        test_ref: Test reference string (Bazel label)

    Returns:
        None if valid, error message if invalid
    """
    if not test_ref:
        return "test reference cannot be empty"

    # Bazel label should start with // for absolute or : for relative
    if not test_ref.startswith("//") and not test_ref.startswith(":"):
        return "test reference '{}' must be a Bazel label (start with // or :)".format(test_ref)

    # Should contain : to separate package from target
    if ":" not in test_ref:
        return "test reference '{}' must include target name after ':'".format(test_ref)

    return None

def _validate_standard_reference(std_ref):
    """Validate a standard reference.

    Args:
        std_ref: Standard reference string

    Returns:
        None if valid, error message if invalid
    """
    if not std_ref:
        return "standard reference cannot be empty"

    # Standard reference should have some minimum length
    if len(std_ref) < 3:
        return "standard reference '{}' is too short".format(std_ref)

    return None

def _validate_references(references):
    """Validate references section.

    Args:
        references: Dictionary of references

    Returns:
        None if valid, error message if invalid
    """
    if not references:
        return None  # References are optional

    if type(references) != "dict":
        return "references must be a dictionary"

    valid_ref_types = ["parameters", "requirements", "tests", "standards"]

    # Validate reference types
    for ref_type in references:
        if ref_type not in valid_ref_types:
            return "invalid reference type '{}'. Valid types: {}".format(
                ref_type,
                ", ".join(valid_ref_types),
            )

        refs = references[ref_type]
        if type(refs) != "list":
            return "references.{} must be a list".format(ref_type)

        # Validate each reference
        for ref in refs:
            if type(ref) != "string":
                return "reference in {} must be a string, got {}".format(ref_type, type(ref))

            # Type-specific validation
            if ref_type == "parameters":
                err = _validate_parameter_reference(ref)
                if err:
                    return err
            elif ref_type == "requirements":
                err = _validate_requirement_reference(ref)
                if err:
                    return err
            elif ref_type == "tests":
                err = _validate_test_reference(ref)
                if err:
                    return err
            elif ref_type == "standards":
                err = _validate_standard_reference(ref)
                if err:
                    return err

    return None

def validate_requirement_references(frontmatter):
    """Validate requirement references in frontmatter.

    Args:
        frontmatter: Requirement frontmatter dictionary

    Returns:
        None if valid, error message if invalid
    """
    if not frontmatter:
        return None

    if "references" not in frontmatter:
        return None  # References are optional

    return _validate_references(frontmatter["references"])

# Export validation function
reference_validator = struct(
    validate = validate_requirement_references,
)
