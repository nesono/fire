// Test that including v1 when v2 exists emits deprecation warning.

#[path = "test_params_rs/test_value_v1.rs"]
mod test_value_v1;

fn main() {
    // v1 still works but has #[deprecated] attribute on sentinel
    // Using the deprecated sentinel without #[allow(deprecated)] triggers a warning
    let _ = test_value_v1::_DEPRECATED_SENTINEL;
    println!("Value: {}", test_value_v1::TEST_VALUE);
}
