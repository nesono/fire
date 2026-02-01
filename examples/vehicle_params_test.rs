// Test for generated Rust parameter library

// Include per-parameter-version modules
#[path = "vehicle_params_rs/maximum_vehicle_velocity_v1.rs"]
mod maximum_vehicle_velocity_v1;

#[path = "vehicle_params_rs/wheel_count_v1.rs"]
mod wheel_count_v1;

#[path = "vehicle_params_rs/vehicle_name_v1.rs"]
mod vehicle_name_v1;

#[path = "vehicle_params_rs/debug_mode_v1.rs"]
mod debug_mode_v1;

#[path = "vehicle_params_rs/braking_distance_table_v1.rs"]
mod braking_distance_table_v1;

#[test]
fn test_scalar_parameters() {
    assert_eq!(maximum_vehicle_velocity_v1::MAXIMUM_VEHICLE_VELOCITY, 55.0);
    assert_eq!(wheel_count_v1::WHEEL_COUNT, 4);
    assert_eq!(vehicle_name_v1::VEHICLE_NAME, "TestVehicle");
    assert_eq!(debug_mode_v1::DEBUG_MODE, false);
}

#[test]
fn test_table_parameter() {
    assert_eq!(braking_distance_table_v1::BRAKING_DISTANCE_TABLE_SIZE, 6);

    let table = &braking_distance_table_v1::BRAKING_DISTANCE_TABLE;
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
    let table = &braking_distance_table_v1::BRAKING_DISTANCE_TABLE;
    let row = table[0];
    let row_copy = row;
    assert_eq!(row.velocity, row_copy.velocity);

    // Test that the struct can be debugged
    let debug_str = format!("{:?}", row);
    assert!(debug_str.contains("BrakingDistanceTableRow"));
}
