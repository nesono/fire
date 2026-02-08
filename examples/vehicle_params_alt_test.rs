// Test for alternate Rust parameter library

use vehicle_params_rs_alt::*;

#[test]
fn test_alt_scalar_parameters() {
    assert_eq!(MAXIMUM_VEHICLE_VELOCITY_MPS_V3, 100.0);
    assert_eq!(WHEEL_COUNT_V1, 4);
    assert_eq!(VEHICLE_NAME_V1, "TestVehicle");
    assert_eq!(DEBUG_MODE_V1, false);
}

#[test]
fn test_alt_table_parameter() {
    assert_eq!(BRAKING_DISTANCE_TABLE_V1_SIZE, 6);

    let table = &BRAKING_DISTANCE_TABLE_V1;
    assert_eq!(table.len(), 6);

    let first_row = &table[0];
    assert_eq!(first_row.velocity_mps, 10.0);
    assert_eq!(first_row.friction_coefficient, 0.7);
    assert_eq!(first_row.braking_distance_m, 7.1);
}
