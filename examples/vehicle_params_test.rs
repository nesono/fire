// Test for generated Rust parameter library

// Include the generated parameters
// Note: In Bazel rust_test, both srcs are placed in the same directory (examples/),
// so the path is just the filename. The file is generated at examples/vehicle_params.rs
// in the repository, matching the repository-relative convention.
#[path = "vehicle_params.rs"]
mod vehicle_params;

use vehicle_params::*;

#[test]
fn test_scalar_parameters() {
    // Test float parameter with version check
    assert_eq!(maximum_vehicle_velocity::<1>(), 55.0);

    // Test integer parameter with version check
    assert_eq!(wheel_count::<1>(), 4);

    // Test string parameter with version check
    assert_eq!(vehicle_name::<1>(), "TestVehicle");

    // Test boolean parameter with version check
    assert_eq!(debug_mode::<1>(), false);
}

#[test]
fn test_table_parameter() {
    // Test table size constant
    assert_eq!(BRAKING_DISTANCE_TABLE_SIZE, 6);

    // Test table data with version check
    let table = braking_distance_table::<1>();
    assert_eq!(table.len(), 6);

    // Test first row
    let first_row = &table[0];
    assert_eq!(first_row.velocity, 10.0);
    assert_eq!(first_row.friction_coefficient, 0.7);
    assert_eq!(first_row.braking_distance, 7.1);

    // Test iteration
    for row in table {
        assert!(row.velocity > 0.0);
        assert!(row.friction_coefficient > 0.0);
        assert!(row.braking_distance > 0.0);
    }
}

#[test]
fn test_struct_derives() {
    // Test that the struct can be copied
    let table = braking_distance_table::<1>();
    let row = table[0];
    let row_copy = row;
    assert_eq!(row.velocity, row_copy.velocity);

    // Test that the struct can be debugged
    let debug_str = format!("{:?}", row);
    assert!(debug_str.contains("BrakingDistanceTableRow"));
}
