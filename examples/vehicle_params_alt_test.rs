// Test for alternate Rust parameter library

#[path = "vehicle_params_rs_alt.rs"]
mod vehicle_params_rs_alt;

use vehicle_params_rs_alt::*;

#[test]
fn test_alt_scalar_parameters() {
    assert_eq!(maximum_vehicle_velocity::<1>(), 55.0);
    assert_eq!(wheel_count::<1>(), 4);
    assert_eq!(vehicle_name::<1>(), "TestVehicle");
    assert_eq!(debug_mode::<1>(), false);
}

#[test]
fn test_alt_table_parameter() {
    assert_eq!(BRAKING_DISTANCE_TABLE_SIZE, 6);

    let table = braking_distance_table::<1>();
    assert_eq!(table.len(), 6);

    let first_row = &table[0];
    assert_eq!(first_row.velocity, 10.0);
    assert_eq!(first_row.friction_coefficient, 0.7);
    assert_eq!(first_row.braking_distance, 7.1);
}
