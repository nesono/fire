"""Parameter file validation logic."""

import re
from typing import Any, Dict, List


class ValidationError(Exception):
    """Exception raised when parameter validation fails."""

    pass


class ParameterValidator:
    """Validates parameter files against the schema."""

    # Supported parameter types
    VALID_TYPES = {"float", "integer", "string", "boolean", "table"}

    # Namespace must be valid identifier-like format
    NAMESPACE_PATTERN = re.compile(
        r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$"
    )

    def validate(self, param_data: Dict[str, Any]) -> None:
        """Validate a parameter file data structure.

        Args:
            param_data: The parsed parameter file data

        Raises:
            ValidationError: If validation fails
        """
        self._validate_required_fields(param_data)
        self._validate_namespace(param_data["namespace"])
        self._validate_parameters(param_data["parameters"])

    def _validate_required_fields(self, param_data: Dict[str, Any]) -> None:
        """Validate that required top-level fields are present."""
        required_fields = ["schema_version", "namespace", "parameters"]
        for field in required_fields:
            if field not in param_data:
                raise ValidationError(f"Missing required field: {field}")

    def _validate_namespace(self, namespace: str) -> None:
        """Validate namespace format."""
        if not isinstance(namespace, str):
            raise ValidationError("namespace must be a string")

        if not self.NAMESPACE_PATTERN.match(namespace):
            raise ValidationError(
                f"Invalid namespace format: {namespace}. "
                "Namespace must be dot-separated identifiers (e.g., 'vehicle.dynamics')"
            )

    def _validate_parameters(self, parameters: List[Dict[str, Any]]) -> None:
        """Validate the parameters list."""
        if not isinstance(parameters, list):
            raise ValidationError("parameters must be a list")

        seen_names = set()

        for i, param in enumerate(parameters):
            self._validate_parameter(param, i)

            # Check for duplicate names
            name = param["name"]
            if name in seen_names:
                raise ValidationError(f"Duplicate parameter name: {name}")
            seen_names.add(name)

    def _validate_parameter(self, param: Dict[str, Any], index: int) -> None:
        """Validate a single parameter."""
        # Check required fields
        required_fields = ["name", "type", "description"]
        for field in required_fields:
            if field not in param:
                raise ValidationError(
                    f"Parameter at index {index} missing required field: {field}"
                )

        # Validate type
        param_type = param["type"]
        if param_type not in self.VALID_TYPES:
            raise ValidationError(
                f"Parameter '{param['name']}' has invalid type: {param_type}. "
                f"Valid types are: {', '.join(sorted(self.VALID_TYPES))}"
            )

        # Type-specific validation
        if param_type == "table":
            self._validate_table_parameter(param)
        else:
            # Non-table parameters must have a value
            if "value" not in param:
                raise ValidationError(
                    f"Parameter '{param['name']}' must have a 'value' field"
                )
            self._validate_parameter_value(param)

    def _validate_table_parameter(self, param: Dict[str, Any]) -> None:
        """Validate a table parameter."""
        if "columns" not in param:
            raise ValidationError(
                f"Table parameter '{param['name']}' must have 'columns' field"
            )

        if "rows" not in param:
            raise ValidationError(
                f"Table parameter '{param['name']}' must have 'rows' field"
            )

        columns = param["columns"]
        rows = param["rows"]

        if not isinstance(columns, list) or len(columns) == 0:
            raise ValidationError(
                f"Table parameter '{param['name']}' must have at least one column"
            )

        # Validate column definitions
        for col in columns:
            if "name" not in col or "type" not in col:
                raise ValidationError(
                    f"Table parameter '{param['name']}' has invalid column definition"
                )
            if col["type"] not in self.VALID_TYPES - {"table"}:
                raise ValidationError(
                    f"Table parameter '{param['name']}' has invalid "
                    f"column type: {col['type']}"
                )

        # Validate rows
        if not isinstance(rows, list):
            raise ValidationError(
                f"Table parameter '{param['name']}' rows must be a list"
            )

        expected_cols = len(columns)
        for row_idx, row in enumerate(rows):
            if not isinstance(row, list):
                raise ValidationError(
                    f"Table parameter '{param['name']}' row {row_idx} must be a list"
                )
            if len(row) != expected_cols:
                raise ValidationError(
                    f"Table parameter '{param['name']}' row {row_idx} has {len(row)} "
                    f"columns but expected {expected_cols}"
                )

            # Validate each cell value matches column type
            for col_idx, (cell_value, col_def) in enumerate(zip(row, columns)):
                self._validate_value_type(
                    cell_value,
                    col_def["type"],
                    f"Table parameter '{param['name']}' row {row_idx} column {col_idx}",
                )

    def _validate_parameter_value(self, param: Dict[str, Any]) -> None:
        """Validate a parameter's value matches its type."""
        self._validate_value_type(
            param["value"], param["type"], f"Parameter '{param['name']}'"
        )

    def _validate_value_type(
        self, value: Any, expected_type: str, context: str
    ) -> None:
        """Validate that a value matches the expected type."""
        if expected_type == "float":
            if not isinstance(value, (int, float)):
                raise ValidationError(f"{context} must be a number (float)")
        elif expected_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValidationError(f"{context} must be an integer")
        elif expected_type == "string":
            if not isinstance(value, str):
                raise ValidationError(f"{context} must be a string")
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                raise ValidationError(f"{context} must be a boolean")
