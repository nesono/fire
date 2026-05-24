#!/usr/bin/env python3
"""Unit tests for parameter_models."""

import pytest
from pydantic import ValidationError

from fire.starlark.parameter_models import (
    BoolParameter,
    Column,
    F64Parameter,
    I64Parameter,
    ParameterFile,
    StringParameter,
    TableParameter,
    infer_parameter_type,
    infer_type_from_value,
)


# ---------------------------------------------------------------------------
# infer_type_from_value
# ---------------------------------------------------------------------------


class TestInferTypeFromValue:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (True, "bool"),
            (False, "bool"),
            (1, "i64"),
            (-1, "i64"),
            (1.5, "f64"),
            (-3.14, "f64"),
            ("hello", "string"),
            ("", "string"),
        ],
    )
    def test_recognized_types(self, value, expected):
        assert infer_type_from_value(value) == expected

    def test_none_raises(self):
        with pytest.raises(ValueError, match="None"):
            infer_type_from_value(None)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="list"):
            infer_type_from_value([1, 2])


# ---------------------------------------------------------------------------
# infer_parameter_type
# ---------------------------------------------------------------------------


class TestInferParameterType:
    def test_table_passes_through(self):
        assert infer_parameter_type({"type": "table"}) == "table"

    def test_scalar_explicit_type_rejected(self):
        with pytest.raises(ValueError, match="not allowed"):
            infer_parameter_type({"type": "i64", "value": 1})

    def test_missing_value_raises(self):
        with pytest.raises(ValueError, match="value"):
            infer_parameter_type({})

    def test_infers_from_value(self):
        assert infer_parameter_type({"value": 42}) == "i64"
        assert infer_parameter_type({"value": 1.5}) == "f64"
        assert infer_parameter_type({"value": True}) == "bool"
        assert infer_parameter_type({"value": "ok"}) == "string"


# ---------------------------------------------------------------------------
# Scalar parameter models
# ---------------------------------------------------------------------------


class TestI64Parameter:
    def test_valid(self):
        p = I64Parameter(type="i64", value=42, unit="m", description="length")
        assert p.value == 42

    def test_float_rejected_due_to_strict(self):
        with pytest.raises(ValidationError):
            I64Parameter(type="i64", value=1.5, unit="m", description="length")

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            I64Parameter(
                type="i64",
                value=1,
                unit="m",
                description="length",
                extra="not allowed",
            )


class TestF64Parameter:
    def test_valid_float(self):
        p = F64Parameter(type="f64", value=1.5, unit="m/s", description="speed")
        assert p.value == 1.5

    def test_int_rejected_due_to_strict(self):
        with pytest.raises(ValidationError):
            F64Parameter(type="f64", value=1, unit="m/s", description="speed")


class TestStringParameter:
    def test_valid(self):
        p = StringParameter(type="string", value="ok", unit="x", description="d")
        assert p.value == "ok"

    def test_int_rejected(self):
        with pytest.raises(ValidationError):
            StringParameter(type="string", value=1, unit="x", description="d")


class TestBoolParameter:
    def test_valid(self):
        p = BoolParameter(type="bool", value=True, unit="x", description="d")
        assert p.value is True

    def test_int_rejected_due_to_strict(self):
        with pytest.raises(ValidationError):
            BoolParameter(type="bool", value=1, unit="x", description="d")


# ---------------------------------------------------------------------------
# Column
# ---------------------------------------------------------------------------


class TestColumn:
    def test_valid(self):
        c = Column(name="speed", type="f64", unit="m/s")
        assert c.name == "speed"

    def test_capital_name_rejected(self):
        with pytest.raises(ValidationError):
            Column(name="Speed", type="f64", unit="m/s")

    def test_empty_unit_rejected(self):
        with pytest.raises(ValidationError):
            Column(name="speed", type="f64", unit="")


# ---------------------------------------------------------------------------
# TableParameter
# ---------------------------------------------------------------------------


class TestTableParameter:
    def test_valid(self):
        p = TableParameter(
            type="table",
            description="d",
            columns=[Column(name="a", type="i64", unit="x")],
            rows=[[1], [2]],
        )
        assert len(p.rows) == 2

    def test_empty_columns_rejected(self):
        with pytest.raises(ValidationError):
            TableParameter(type="table", description="d", columns=[], rows=[[1]])

    def test_empty_rows_rejected(self):
        with pytest.raises(ValidationError):
            TableParameter(
                type="table",
                description="d",
                columns=[Column(name="a", type="i64", unit="x")],
                rows=[],
            )


# ---------------------------------------------------------------------------
# ParameterFile
# ---------------------------------------------------------------------------


class TestParameterFile:
    def test_single_param_v1(self):
        data = {
            "speed_v1": {
                "value": 1.5,
                "unit": "m/s",
                "description": "speed",
            }
        }
        pf = ParameterFile.model_validate(data)
        assert "speed_v1" in pf.root

    def test_two_consecutive_versions_ok(self):
        data = {
            "speed_v1": {"value": 1.0, "unit": "m/s", "description": "a"},
            "speed_v2": {"value": 2.0, "unit": "m/s", "description": "b"},
        }
        pf = ParameterFile.model_validate(data)
        assert set(pf.root) == {"speed_v1", "speed_v2"}

    def test_three_versions_rejected(self):
        data = {
            "speed_v1": {"value": 1.0, "unit": "m/s", "description": "a"},
            "speed_v2": {"value": 2.0, "unit": "m/s", "description": "b"},
            "speed_v3": {"value": 3.0, "unit": "m/s", "description": "c"},
        }
        with pytest.raises(ValidationError, match="two entries"):
            ParameterFile.model_validate(data)

    def test_non_consecutive_versions_rejected(self):
        data = {
            "speed_v1": {"value": 1.0, "unit": "m/s", "description": "a"},
            "speed_v3": {"value": 3.0, "unit": "m/s", "description": "c"},
        }
        with pytest.raises(ValidationError, match="consecutive"):
            ParameterFile.model_validate(data)

    def test_missing_version_suffix_rejected(self):
        data = {
            "speed": {"value": 1.0, "unit": "m/s", "description": "a"},
        }
        with pytest.raises(ValidationError, match="pattern"):
            ParameterFile.model_validate(data)

    def test_empty_root_rejected(self):
        with pytest.raises(ValidationError):
            ParameterFile.model_validate({})

    def test_inject_inferred_types_int(self):
        data = {
            "wheel_count_v1": {
                "value": 4,
                "unit": "1",
                "description": "wheels",
            }
        }
        pf = ParameterFile.model_validate(data)
        assert isinstance(pf.root["wheel_count_v1"], I64Parameter)

    def test_inject_inferred_types_float(self):
        data = {
            "speed_v1": {
                "value": 1.5,
                "unit": "m/s",
                "description": "speed",
            }
        }
        pf = ParameterFile.model_validate(data)
        assert isinstance(pf.root["speed_v1"], F64Parameter)

    def test_inject_inferred_types_bool(self):
        data = {
            "enabled_v1": {
                "value": True,
                "unit": "x",
                "description": "flag",
            }
        }
        pf = ParameterFile.model_validate(data)
        assert isinstance(pf.root["enabled_v1"], BoolParameter)

    def test_inject_inferred_types_string(self):
        data = {
            "label_v1": {
                "value": "foo",
                "unit": "x",
                "description": "label",
            }
        }
        pf = ParameterFile.model_validate(data)
        assert isinstance(pf.root["label_v1"], StringParameter)

    def test_table_explicit_column_type_rejected(self):
        data = {
            "lookup_v1": {
                "type": "table",
                "description": "lookup",
                "columns": [
                    {"name": "x", "type": "i64", "unit": "1"},
                ],
                "rows": [[1]],
            }
        }
        with pytest.raises(ValidationError, match="Explicit 'type' field not allowed"):
            ParameterFile.model_validate(data)

    def test_table_inconsistent_row_types_rejected(self):
        data = {
            "lookup_v1": {
                "type": "table",
                "description": "lookup",
                "columns": [
                    {"name": "x", "unit": "1"},
                ],
                "rows": [[1], ["oops"]],
            }
        }
        with pytest.raises(ValidationError, match="Inconsistent type"):
            ParameterFile.model_validate(data)

    def test_table_inferred_column_types(self):
        data = {
            "lookup_v1": {
                "type": "table",
                "description": "lookup",
                "columns": [
                    {"name": "x", "unit": "1"},
                    {"name": "y", "unit": "m/s"},
                ],
                "rows": [[1, 2.5], [3, 4.5]],
            }
        }
        pf = ParameterFile.model_validate(data)
        table = pf.root["lookup_v1"]
        assert isinstance(table, TableParameter)
        assert table.columns[0].type == "i64"
        assert table.columns[1].type == "f64"
