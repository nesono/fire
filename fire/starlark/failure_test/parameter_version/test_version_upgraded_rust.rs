// Test that using v1 when v2 exists emits deprecation warning.

use test_params_rs::*;

fn main() {
    // v1 still works but has #[deprecated] attribute
    // Using it without #[allow(deprecated)] triggers a warning
    println!("Value: {}", TEST_VALUE_MPS_V1);
}
