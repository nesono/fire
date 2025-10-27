"""Parameter validation logic in pure Starlark."""

def _is_valid_identifier_char(c, allow_dot = False):
    """Check if character is valid in an identifier."""
    if c.isalnum() or c == "_":
        return True
    if allow_dot and c == ".":
        return True
    return False

def _validate_namespace(namespace):
    """Validate namespace format.

    Args:
        namespace: String namespace to validate

    Returns:
        None if valid, error message if invalid
    """
    if not namespace:
        return "namespace cannot be empty"

    if not namespace[0].isalpha() and namespace[0] != "_":
        return "namespace must start with letter or underscore"

    # Check for valid characters
    for i, c in enumerate(namespace.elems()):
        if not _is_valid_identifier_char(c, allow_dot = True):
            return "namespace contains invalid character '{}' at position {}".format(c, i)

    # Check that dots are properly placed
    parts = namespace.split(".")
    for part in parts:
        if not part:
            return "namespace cannot have empty parts (double dots or trailing/leading dots)"
        if not part[0].isalpha() and part[0] != "_":
            return "namespace part '{}' must start with letter or underscore".format(part)

    return None

def _validate_type(param_type):
    """Validate parameter type.

    Args:
        param_type: Type string to validate

    Returns:
        None if valid, error message if invalid
    """
    valid_types = ["float", "integer", "string", "boolean", "table"]
    if param_type not in valid_types:
        return "invalid type '{}'. Valid types: {}".format(param_type, ", ".join(valid_types))
    return None

def _validate_value_type(value, expected_type, context):
    """Validate that a value matches its expected type.

    Args:
        value: The value to check
        expected_type: Expected type string
        context: Context string for error messages

    Returns:
        None if valid, error message if invalid
    """
    value_type = type(value)

    if expected_type == "float":
        if value_type not in ["int", "float"]:
            return "{} must be a number (got {})".format(context, value_type)
    elif expected_type == "integer":
        if value_type != "int":
            return "{} must be an integer (got {})".format(context, value_type)
    elif expected_type == "string":
        if value_type != "string":
            return "{} must be a string (got {})".format(context, value_type)
    elif expected_type == "boolean":
        if value_type != "bool":
            return "{} must be a boolean (got {})".format(context, value_type)

    return None

def _validate_table_parameter(param):
    """Validate a table parameter.

    Args:
        param: Parameter dictionary

    Returns:
        None if valid, error message if invalid
    """
    param_name = param.get("name", "<unknown>")

    if "columns" not in param:
        return "table parameter '{}' must have 'columns' field".format(param_name)

    if "rows" not in param:
        return "table parameter '{}' must have 'rows' field".format(param_name)

    columns = param["columns"]
    rows = param["rows"]

    if type(columns) != "list" or len(columns) == 0:
        return "table parameter '{}' must have at least one column".format(param_name)

    # Validate column definitions
    for col in columns:
        if "name" not in col or "type" not in col:
            return "table parameter '{}' has invalid column definition".format(param_name)

        col_type = col["type"]
        if col_type == "table":
            return "table parameter '{}' cannot have nested tables".format(param_name)

        err = _validate_type(col_type)
        if err:
            return "table parameter '{}': {}".format(param_name, err)

    # Validate rows
    if type(rows) != "list":
        return "table parameter '{}' rows must be a list".format(param_name)

    expected_cols = len(columns)
    for row_idx, row in enumerate(rows):
        if type(row) != "list":
            return "table parameter '{}' row {} must be a list".format(param_name, row_idx)

        if len(row) != expected_cols:
            return "table parameter '{}' row {} has {} columns but expected {}".format(
                param_name,
                row_idx,
                len(row),
                expected_cols,
            )

        # Validate each cell value
        for col_idx, (cell_value, col_def) in enumerate(zip(row, columns)):
            context = "table parameter '{}' row {} column {}".format(param_name, row_idx, col_idx)
            err = _validate_value_type(cell_value, col_def["type"], context)
            if err:
                return err

    return None

def _validate_parameter(param, index):
    """Validate a single parameter.

    Args:
        param: Parameter dictionary
        index: Index in parameters list (for error messages)

    Returns:
        None if valid, error message if invalid
    """

    # Check required fields
    required_fields = ["name", "type", "description"]
    for field in required_fields:
        if field not in param:
            return "parameter at index {} missing required field: {}".format(index, field)

    # Validate type
    param_type = param["type"]
    err = _validate_type(param_type)
    if err:
        return "parameter '{}': {}".format(param.get("name", "<unknown>"), err)

    # Type-specific validation
    if param_type == "table":
        return _validate_table_parameter(param)
    else:
        # Non-table parameters must have a value
        if "value" not in param:
            return "parameter '{}' must have a 'value' field".format(param["name"])

        context = "parameter '{}'".format(param["name"])
        return _validate_value_type(param["value"], param_type, context)

def validate_parameters(param_data):
    """Validate a parameter data structure.

    Args:
        param_data: Dictionary with parameter data

    Returns:
        None if valid, error message if invalid
    """

    # Check required top-level fields
    required_fields = ["schema_version", "namespace", "parameters"]
    for field in required_fields:
        if field not in param_data:
            return "missing required field: {}".format(field)

    # Validate namespace
    err = _validate_namespace(param_data["namespace"])
    if err:
        return err

    # Validate parameters list
    parameters = param_data["parameters"]
    if type(parameters) != "list":
        return "parameters must be a list"

    # Track parameter names for duplicate checking
    seen_names = {}

    for index, param in enumerate(parameters):
        err = _validate_parameter(param, index)
        if err:
            return err

        # Check for duplicate names
        param_name = param["name"]
        if param_name in seen_names:
            return "duplicate parameter name: {}".format(param_name)
        seen_names[param_name] = True

    return None

# Export validation function
validator = struct(
    validate = validate_parameters,
)
