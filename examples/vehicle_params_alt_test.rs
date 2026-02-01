// Test for alternate Rust parameter library

#[path = "vehicle_params_rs_alt/maximum_vehicle_velocity_v1.rs"]
mod maximum_vehicle_velocity_v1;

#[path = "vehicle_params_rs_alt/wheel_count_v1.rs"]
mod wheel_count_v1;

#[path = "vehicle_params_rs_alt/vehicle_name_v1.rs"]
mod vehicle_name_v1;

#[path = "vehicle_params_rs_alt/debug_mode_v1.rs"]
mod debug_mode_v1;

#[path = "vehicle_params_rs_alt/braking_distance_table_v1.rs"]
mod braking_distance_table_v1;

#[test]
fn test_alt_scalar_parameters() {
    assert_eq!(maximum_vehicle_velocity_v1::MAXIMUM_VEHICLE_VELOCITY, 55.0);
    assert_eq!(wheel_count_v1::WHEEL_COUNT, 4);
    assert_eq!(vehicle_name_v1::VEHICLE_NAME, "TestVehicle");
    assert_eq!(debug_mode_v1::DEBUG_MODE, false);
}

#[test]
fn test_alt_table_parameter() {
    assert_eq!(braking_distance_table_v1::BRAKING_DISTANCE_TABLE_SIZE, 6);

    let table = &braking_distance_table_v1::BRAKING_DISTANCE_TABLE;
    assert_eq!(table.len(), 6);

    let first_row = &table[0];
    assert_eq!(first_row.velocity, 10.0);
    assert_eq!(first_row.friction_coefficient, 0.7);
    assert_eq!(first_row.braking_distance, 7.1);
}
