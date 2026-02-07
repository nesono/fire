// Test that using a version that doesn't exist causes build error.
// TEST_VALUE_V3 does not exist (max version is v2), so this should fail.

use test_params_rs::*;

fn main() {
    println!("Value: {}", TEST_VALUE_V3);
}
