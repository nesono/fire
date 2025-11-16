"""Test parameters for integration test."""

TEST_PARAMS = [
    {
        "description": "Maximum allowed speed in m/s",
        "name": "max_speed",
        "type": "float",
        "value": 30.0,
    },
    {
        "description": "Minimum braking distance in meters",
        "name": "min_braking_distance",
        "type": "float",
        "value": 50.0,
    },
    {
        "description": "System update rate in Hz",
        "name": "update_rate",
        "type": "integer",
        "value": 100,
    },
]
