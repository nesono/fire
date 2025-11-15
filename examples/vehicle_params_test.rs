// Test for generated Rust parameter library

#[path = "vehicle_params_rust.rs"]
mod vehicle_params_rust;

use vehicle_params_rust::*;

#[test]
fn test_scalar_parameters() {
    // Test float parameter
    assert_eq!(MAXIMUM_VEHICLE_VELOCITY, 55.0);

    // Test integer parameter
    assert_eq!(WHEEL_COUNT, 4);

    // Test string parameter
    assert_eq!(VEHICLE_NAME, "TestVehicle");

    // Test boolean parameter
    assert_eq!(DEBUG_MODE, false);
}

#[test]
fn test_table_parameter() {
    // Test table size constant
    assert_eq!(BRAKING_DISTANCE_TABLE_SIZE, 6);

    // Test table data
    assert_eq!(BRAKING_DISTANCE_TABLE.len(), 6);

    // Test first row
    let first_row = &BRAKING_DISTANCE_TABLE[0];
    assert_eq!(first_row.velocity, 10.0);
    assert_eq!(first_row.friction_coefficient, 0.7);
    assert_eq!(first_row.braking_distance, 7.1);

    // Test iteration
    for row in BRAKING_DISTANCE_TABLE {
        assert!(row.velocity > 0.0);
        assert!(row.friction_coefficient > 0.0);
        assert!(row.braking_distance > 0.0);
    }
}

#[test]
fn test_struct_derives() {
    // Test that the struct can be copied
    let row = BRAKING_DISTANCE_TABLE[0];
    let row_copy = row;
    assert_eq!(row.velocity, row_copy.velocity);

    // Test that the struct can be debugged
    let debug_str = format!("{:?}", row);
    assert!(debug_str.contains("BrakingDistanceTableRow"));
}
