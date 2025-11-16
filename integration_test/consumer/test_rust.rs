// Include generated parameters
include!("../test_params.rs");

fn main() {
    // Test that generated constants are accessible
    println!("Max Speed: {} m/s", MAX_SPEED);
    println!("Min Braking Distance: {} m", MIN_BRAKING_DISTANCE);
    println!("Update Rate: {} Hz", UPDATE_RATE);

    // Basic validation
    assert_eq!(MAX_SPEED, 30.0, "MAX_SPEED has wrong value!");
    assert_eq!(MIN_BRAKING_DISTANCE, 50.0, "MIN_BRAKING_DISTANCE has wrong value!");
    assert_eq!(UPDATE_RATE, 100, "UPDATE_RATE has wrong value!");

    println!("Rust integration test PASSED");
}

#[cfg(test)]
mod tests {
    include!("../test_params.rs");

    #[test]
    fn test_constants() {
        assert_eq!(MAX_SPEED, 30.0);
        assert_eq!(MIN_BRAKING_DISTANCE, 50.0);
        assert_eq!(UPDATE_RATE, 100);
    }
}
