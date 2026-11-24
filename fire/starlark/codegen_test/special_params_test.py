"""Imports and checks generated Python for special characters in values and units."""

import sys

import pytest

from fire.starlark.codegen_test.special_params_py.acceleration_v1 import (
    ACCELERATION_MPS2,
)
from fire.starlark.codegen_test.special_params_py.error_rate_v1 import (
    ERROR_RATE_PERMILLE,
)
from fire.starlark.codegen_test.special_params_py.noise_level_v1 import NOISE_LEVEL_DBA
from fire.starlark.codegen_test.special_params_py.ratio_v1 import RATIO_PERCENT
from fire.starlark.codegen_test.special_params_py.resistance_v1 import RESISTANCE_OHM
from fire.starlark.codegen_test.special_params_py.special_string_v1 import (
    SPECIAL_STRING,
)
from fire.starlark.codegen_test.special_params_py.special_table_v1 import (
    SPECIAL_TABLE,
    SpecialTableRow,
)
from fire.starlark.codegen_test.special_params_py.temperature_v1 import TEMPERATURE_DEGC
from fire.starlark.codegen_test.special_params_py.thickness_v1 import THICKNESS_UM
from fire.starlark.codegen_test.special_params_py.turn_rate_v1 import TURN_RATE_DEGPS
from fire.starlark.codegen_test.special_params_py.volume_v1 import VOLUME_M3

EXPECTED = (
    "say \"hi\" \\ back\\\\slash\ttab\nline2 é {x} %s $y 'q' /* c */ "
    "// not a comment \\u000a \\n ??/ \x01\x7fend\\"
)
EXPECTED_DESCRIPTION = (
    'table description\nint injected = 1; //\n"""\n*/ int also = 2; /* \\u000a \\'
)


def test_string_value():
    assert SPECIAL_STRING == EXPECTED


def test_table_cells_and_columns():
    assert len(SPECIAL_TABLE) == 2
    assert SPECIAL_TABLE[0].label == EXPECTED
    assert SPECIAL_TABLE[1].label == "plain"
    assert SPECIAL_TABLE[0].temp_degc == -40.5
    assert SPECIAL_TABLE[0].ratio_percent == 12.5
    assert SPECIAL_TABLE[0].accel_mps2 == 9.81
    assert SPECIAL_TABLE[0].level_dba == 85.0


def test_table_description_survives_in_docstring():
    assert SpecialTableRow.__doc__ == EXPECTED_DESCRIPTION


def test_units_in_identifiers():
    assert TEMPERATURE_DEGC == 21.5
    assert RATIO_PERCENT == 12.5
    assert ACCELERATION_MPS2 == 9.81
    assert NOISE_LEVEL_DBA == 85.0
    assert THICKNESS_UM == 3.0
    assert RESISTANCE_OHM == 4.7
    assert VOLUME_M3 == 1.5
    assert ERROR_RATE_PERMILLE == 2.5
    assert TURN_RATE_DEGPS == 90.0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
