"""Test for vehicle parameters in Python."""

# Import the generated parameters
# Note: In actual use, you would import from the Bazel-generated package
# For this example, we'll show how the generated code can be used in tests

def test_simple_parameters():
    """Test simple parameter access."""
    # These values would be imported from the generated module
    from vehicle_params_py import (
        DEBUG_MODE,
        MAXIMUM_VEHICLE_VELOCITY,
        VEHICLE_NAME,
        WHEEL_COUNT,
    )

    assert MAXIMUM_VEHICLE_VELOCITY == 55.0
    assert WHEEL_COUNT == 4
    assert VEHICLE_NAME == "TestVehicle"
    assert DEBUG_MODE == False


def test_table_parameters():
    """Test table parameter access."""
    from vehicle_params_py import BRAKING_DISTANCE_TABLE_DATA, BrakingDistanceTableRow

    # Check we have the expected number of rows
    assert len(BRAKING_DISTANCE_TABLE_DATA) == 6

    # Check first row
    first_row = BRAKING_DISTANCE_TABLE_DATA[0]
    assert isinstance(first_row, BrakingDistanceTableRow)
    assert first_row.velocity == 10.0
    assert first_row.friction_coefficient == 0.7
    assert first_row.braking_distance == 7.1

    # Check that we can iterate over the table
    velocities = [row.velocity for row in BRAKING_DISTANCE_TABLE_DATA]
    assert 10.0 in velocities
    assert 20.0 in velocities
    assert 30.0 in velocities


def test_table_immutability():
    """Test that table rows are immutable (frozen dataclass)."""
    from vehicle_params_py import BRAKING_DISTANCE_TABLE_DATA

    first_row = BRAKING_DISTANCE_TABLE_DATA[0]

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
