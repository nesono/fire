use test_params_rs::*;

fn main() {
    // Test that generated constants are accessible
    println!("Max Speed: {} m/s", MAX_SPEED_MPS_V1);
    println!("Min Braking Distance: {} m", MIN_BRAKING_DISTANCE_M_V1);
    println!("Update Rate: {} Hz", UPDATE_RATE_HZ_V1);

    // Basic validation
    assert_eq!(MAX_SPEED_MPS_V1, 30.0, "max_speed has wrong value!");
    assert_eq!(
        MIN_BRAKING_DISTANCE_M_V1, 50.0,
        "min_braking_distance has wrong value!"
    );
    assert_eq!(UPDATE_RATE_HZ_V1, 100, "update_rate has wrong value!");

    println!("Rust integration test PASSED");
}

#[test]
fn test_constants() {
    assert_eq!(MAX_SPEED_MPS_V1, 30.0);
    assert_eq!(MIN_BRAKING_DISTANCE_M_V1, 50.0);
    assert_eq!(UPDATE_RATE_HZ_V1, 100);
}
