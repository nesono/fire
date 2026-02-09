"""Test for alternate Python parameter library."""

# Import from the alternate library
from examples.vehicle_params_py_alt.maximum_vehicle_velocity_v3 import (
    MAXIMUM_VEHICLE_VELOCITY_MPS,
)
from examples.vehicle_params_py_alt.wheel_count_v1 import WHEEL_COUNT
from examples.vehicle_params_py_alt.vehicle_name_v1 import VEHICLE_NAME
from examples.vehicle_params_py_alt.debug_mode_v1 import DEBUG_MODE
from examples.vehicle_params_py_alt.braking_distance_table_v1 import (
    BRAKING_DISTANCE_TABLE,
    BrakingDistanceTableRow,
)


def test_simple_parameters():
    """Test simple parameter access."""
    assert MAXIMUM_VEHICLE_VELOCITY_MPS == 100.0
    assert WHEEL_COUNT == 4
    assert VEHICLE_NAME == "TestVehicle"
    assert not DEBUG_MODE


def test_table_parameters():
    """Test table parameter access."""
    assert len(BRAKING_DISTANCE_TABLE) == 6

    first_row = BRAKING_DISTANCE_TABLE[0]
    assert isinstance(first_row, BrakingDistanceTableRow)
    assert first_row.velocity_mps == 10.0
    assert first_row.friction_coefficient == 0.7
    assert first_row.braking_distance_m == 7.1


if __name__ == "__main__":
    test_simple_parameters()
    test_table_parameters()
    print("All Python alternate parameter tests passed!")
