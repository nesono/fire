// Include per-parameter-version modules
#[path = "../test_params_rs/max_speed_v1.rs"]
mod max_speed_v1;

#[path = "../test_params_rs/min_braking_distance_v1.rs"]
mod min_braking_distance_v1;

#[path = "../test_params_rs/update_rate_v1.rs"]
mod update_rate_v1;

fn main() {
    // Test that generated constants are accessible
    println!("Max Speed: {} m/s", max_speed_v1::MAX_SPEED);
    println!("Min Braking Distance: {} m", min_braking_distance_v1::MIN_BRAKING_DISTANCE);
    println!("Update Rate: {} Hz", update_rate_v1::UPDATE_RATE);

    // Basic validation
    assert_eq!(max_speed_v1::MAX_SPEED, 30.0, "max_speed has wrong value!");
    assert_eq!(min_braking_distance_v1::MIN_BRAKING_DISTANCE, 50.0, "min_braking_distance has wrong value!");
    assert_eq!(update_rate_v1::UPDATE_RATE, 100, "update_rate has wrong value!");

    println!("Rust integration test PASSED");
}

#[test]
fn test_constants() {
    assert_eq!(max_speed_v1::MAX_SPEED, 30.0);
    assert_eq!(min_braking_distance_v1::MIN_BRAKING_DISTANCE, 50.0);
    assert_eq!(update_rate_v1::UPDATE_RATE, 100);
}
