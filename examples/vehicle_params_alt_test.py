"""Test for alternate Python parameter library."""

# Import from the alternate library
from examples.vehicle_params_py_alt import (
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
    table_data = braking_distance_table(1)
    assert len(table_data) == 6

    first_row = table_data[0]
    assert isinstance(first_row, BrakingDistanceTableRow)
    assert first_row.velocity == 10.0
    assert first_row.friction_coefficient == 0.7
    assert first_row.braking_distance == 7.1


if __name__ == "__main__":
    test_simple_parameters()
    test_table_parameters()
    print("All Python alternate parameter tests passed!")
