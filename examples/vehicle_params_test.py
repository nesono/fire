"""Test for vehicle parameters in Python."""

# Import the generated parameters using repository-relative path
from examples.vehicle_params import (
    braking_distance_table,
    BrakingDistanceTableRow,
    debug_mode,
    maximum_vehicle_velocity,
    vehicle_name,
    wheel_count,
)


def test_simple_parameters():
    """Test simple parameter access with version check."""
    assert maximum_vehicle_velocity(1) == 55.0
    assert wheel_count(1) == 4
    assert vehicle_name(1) == "TestVehicle"
    assert debug_mode(1) == False


def test_table_parameters():
    """Test table parameter access with version check."""
    # Check we have the expected number of rows
    table_data = braking_distance_table(1)
    assert len(table_data) == 6

    # Check first row
    first_row = table_data[0]
    assert isinstance(first_row, BrakingDistanceTableRow)
    assert first_row.velocity == 10.0
    assert first_row.friction_coefficient == 0.7
    assert first_row.braking_distance == 7.1

    # Check that we can iterate over the table
    velocities = [row.velocity for row in table_data]
    assert 10.0 in velocities
    assert 20.0 in velocities
    assert 30.0 in velocities


def test_table_immutability():
    """Test that table rows are immutable (frozen dataclass)."""
    table_data = braking_distance_table(1)
    first_row = table_data[0]

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
