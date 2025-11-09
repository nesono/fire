"""Cross-reference validation logic."""

def _validate_parameter_reference(param_ref):
    """Validate a parameter reference.

    Args:
        param_ref: Parameter reference string (repository-relative path with #anchor)

    Returns:
        None if valid, error message if invalid
    """
    if not param_ref:
        return "parameter reference cannot be empty"

    # Repository-relative path format: path/to/file.bzl#parameter_name
    if "#" not in param_ref:
        return "parameter reference '{}' must include #anchor".format(param_ref)

    parts = param_ref.split("#")
    if len(parts) != 2:
        return "parameter reference '{}' must have exactly one #".format(param_ref)

    file_path = parts[0]
    param_name = parts[1]

    # Validate file path ends with .bzl
    if not file_path.endswith(".bzl"):
        return "parameter reference '{}' must reference a .bzl file".format(param_ref)

    # Validate parameter name is valid identifier
    if not param_name:
        return "parameter reference '{}' has empty parameter name".format(param_ref)

    if not param_name[0].isalpha() and param_name[0] != "_":
        return "parameter name in '{}' must start with letter or underscore".format(param_ref)

    for c in param_name.elems():
        if not (c.isalnum() or c == "_"):
            return "parameter name in '{}' contains invalid character '{}'".format(param_ref, c)

    return None

def _validate_requirement_reference(req_ref):
    """Validate a requirement reference.

    Args:
        req_ref: Requirement reference dict with 'path' and 'version' keys

    Returns:
        None if valid, error message if invalid
    """

    # Must be dict with path and version
    if type(req_ref) == "string":
        return "requirement reference must use dict format with 'path' and 'version' keys, got string '{}'".format(req_ref)

    if type(req_ref) != "dict":
        return "requirement reference must be dict, got {}".format(type(req_ref))

    # Require both path and version
    if "path" not in req_ref:
        return "requirement reference missing required 'path' key"

    if "version" not in req_ref:
        return "requirement reference missing required 'version' key"

    req_path = req_ref["path"]
    req_version = req_ref["version"]

    if type(req_path) != "string":
        return "requirement reference 'path' must be a string"

    if not req_path:
        return "requirement reference 'path' cannot be empty"

    # Path should end with .md
    if not req_path.endswith(".md"):
        return "requirement reference path '{}' must end with .md".format(req_path)

    # Validate version is positive integer
    if type(req_version) != "int":
        return "requirement reference 'version' must be an integer"

    if req_version < 1:
        return "requirement reference 'version' must be >= 1"

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

        # Extract sortable items for lexicographic check
        sortable = []

        # Validate each reference
        for ref in refs:
            # Type-specific validation
            if ref_type == "parameters":
                if type(ref) != "string":
                    return "parameter reference must be a string, got {}".format(type(ref))
                err = _validate_parameter_reference(ref)
                if err:
                    return err
                sortable.append(ref)

            elif ref_type == "requirements":
                # Requirements must be dicts
                if type(ref) != "dict":
                    err = _validate_requirement_reference(ref)
                    if err:
                        return err
                else:
                    err = _validate_requirement_reference(ref)
                    if err:
                        return err
                    if "path" in ref:
                        sortable.append(ref["path"])

            elif ref_type == "tests":
                if type(ref) != "string":
                    return "test reference must be a string, got {}".format(type(ref))
                err = _validate_test_reference(ref)
                if err:
                    return err
                sortable.append(ref)

            elif ref_type == "standards":
                if type(ref) != "string":
                    return "standard reference must be a string, got {}".format(type(ref))
                err = _validate_standard_reference(ref)
                if err:
                    return err
                sortable.append(ref)

        # Check lexicographic sorting
        if sortable:
            sorted_items = sorted(sortable)
            if sortable != sorted_items:
                return "references.{} not sorted lexicographically (expected: {})".format(
                    ref_type,
                    sorted_items,
                )

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
