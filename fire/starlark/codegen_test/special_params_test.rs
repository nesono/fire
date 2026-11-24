// Compiles and checks generated Rust for special characters in values and units.

use special_params_rs::*;

const EXPECTED: &str = "say \"hi\" \\ back\\\\slash\ttab\nline2 é {x} %s $y 'q' /* c */ // not a comment \\u000a \\n ??/ \x01\x7fend\\";

#[test]
fn test_string_value() {
    assert_eq!(SPECIAL_STRING_V1, EXPECTED);
}

#[test]
fn test_table_cells_and_columns() {
    assert_eq!(SPECIAL_TABLE_V1_SIZE, 2);
    assert_eq!(SPECIAL_TABLE_V1[0].label, EXPECTED);
    assert_eq!(SPECIAL_TABLE_V1[1].label, "plain");
    assert_eq!(SPECIAL_TABLE_V1[0].temp_degc, -40.5);
    assert_eq!(SPECIAL_TABLE_V1[0].ratio_percent, 12.5);
    assert_eq!(SPECIAL_TABLE_V1[0].accel_mps2, 9.81);
    assert_eq!(SPECIAL_TABLE_V1[0].level_dba, 85.0);
}

#[test]
fn test_units_in_identifiers() {
    assert_eq!(TEMPERATURE_DEGC_V1, 21.5);
    assert_eq!(RATIO_PERCENT_V1, 12.5);
    assert_eq!(ACCELERATION_MPS2_V1, 9.81);
    assert_eq!(NOISE_LEVEL_DBA_V1, 85.0);
    assert_eq!(THICKNESS_UM_V1, 3.0);
    assert_eq!(RESISTANCE_OHM_V1, 4.7);
    assert_eq!(VOLUME_M3_V1, 1.5);
    assert_eq!(ERROR_RATE_PERMILLE_V1, 2.5);
    assert_eq!(TURN_RATE_DEGPS_V1, 90.0);
}
