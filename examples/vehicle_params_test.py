"""Test for vehicle parameters in Python."""

# Import the generated per-parameter-version modules
from examples.vehicle_params_py.maximum_vehicle_velocity_v3 import (
    MAXIMUM_VEHICLE_VELOCITY_MPS,
)
from examples.vehicle_params_py.wheel_count_v1 import WHEEL_COUNT
from examples.vehicle_params_py.vehicle_name_v1 import VEHICLE_NAME
from examples.vehicle_params_py.debug_mode_v1 import DEBUG_MODE
from examples.vehicle_params_py.braking_distance_table_v1 import (
    BRAKING_DISTANCE_TABLE,
    BRAKING_DISTANCE_TABLE_SIZE,
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
    assert BRAKING_DISTANCE_TABLE_SIZE == 6

    # Check first row
    first_row = BRAKING_DISTANCE_TABLE[0]
    assert isinstance(first_row, BrakingDistanceTableRow)
    assert first_row.velocity == 10.0
    assert first_row.friction_coefficient == 0.7
    assert first_row.braking_distance == 7.1

    # Check that we can iterate over the table
    velocities = [row.velocity for row in BRAKING_DISTANCE_TABLE]
    assert 10.0 in velocities
    assert 20.0 in velocities
    assert 30.0 in velocities


def test_table_immutability():
    """Test that table rows are immutable (frozen dataclass)."""
    first_row = BRAKING_DISTANCE_TABLE[0]

    # Try to modify a field (should raise error due to frozen=True)
    try:
        first_row.velocity = 999.0
        assert False, "Should not be able to modify frozen dataclass"
    except AttributeError:
        pass  # Expected


if __name__ == "__main__":
    test_simple_parameters()
    test_table_parameters()
    test_table_immutability()
    print("All Python parameter tests passed!")
