// Test that including a version that doesn't exist causes build error.
// test_value_v3.rs does not exist (max version is v2), so this should fail.

#[path = "test_params_rs/test_value_v3.rs"]
mod test_value_v3;

fn main() {
    println!("Value: {}", test_value_v3::TEST_VALUE);
}
