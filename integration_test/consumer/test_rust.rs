// Include generated parameters
include!("../test_params.rs");

fn main() {
    // Test that generated constants are accessible via version-checked functions
    println!("Max Speed: {} m/s", max_speed::<1>());
    println!("Min Braking Distance: {} m", min_braking_distance::<1>());
    println!("Update Rate: {} Hz", update_rate::<1>());

    // Basic validation
    assert_eq!(max_speed::<1>(), 30.0, "max_speed has wrong value!");
    assert_eq!(min_braking_distance::<1>(), 50.0, "min_braking_distance has wrong value!");
    assert_eq!(update_rate::<1>(), 100, "update_rate has wrong value!");

    println!("Rust integration test PASSED");
}

#[cfg(test)]
mod tests {
    include!("../test_params.rs");

    #[test]
    fn test_constants() {
        assert_eq!(max_speed::<1>(), 30.0);
        assert_eq!(min_braking_distance::<1>(), 50.0);
        assert_eq!(update_rate::<1>(), 100);
    }
}
