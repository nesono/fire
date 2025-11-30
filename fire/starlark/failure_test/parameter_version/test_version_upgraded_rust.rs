// Test that requesting an older version causes compile-time deprecation warning

#[path = "test_params.rs"]
mod test_params;

use test_params::*;

fn main() {
    // Parameter is at version 2, but we request version 1
    // This should cause a deprecation warning at compile time
    const VALUE: f64 = test_value::<1>();
    println!("Value: {}", VALUE);
}
