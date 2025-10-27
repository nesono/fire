"""Vehicle parameter definitions."""

VEHICLE_PARAMS = [
    {
        "description": "Maximum design velocity for the vehicle",
        "name": "maximum_vehicle_velocity",
        "type": "float",
        "unit": "m/s",
        "value": 55.0,
    },
    {
        "description": "Number of wheels on the vehicle",
        "name": "wheel_count",
        "type": "integer",
        "value": 4,
    },
    {
        "description": "Vehicle identifier for testing",
        "name": "vehicle_name",
        "type": "string",
        "value": "TestVehicle",
    },
    {
        "description": "Enable debug output",
        "name": "debug_mode",
        "type": "boolean",
        "value": False,
    },
    {
        "columns": [
            {"name": "velocity", "type": "float", "unit": "m/s"},
            {"name": "friction_coefficient", "type": "float", "unit": "dimensionless"},
            {"name": "braking_distance", "type": "float", "unit": "m"},
        ],
        "description": "Braking distances under various conditions",
        "name": "braking_distance_table",
        "rows": [
            [10.0, 0.7, 7.1],
            [20.0, 0.7, 28.6],
            [30.0, 0.7, 64.3],
            [10.0, 0.3, 16.7],
            [20.0, 0.3, 66.7],
            [30.0, 0.3, 150.0],
        ],
        "type": "table",
    },
]
