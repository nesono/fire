// Test that requesting a version newer than available causes compile error

#[path = "test_params.rs"]
mod test_params;

use test_params::*;

fn main() {
    // Parameter is at version 2, but we request version 3
    // This should cause a compile-time assert failure
    let value = test_value::<3>();
    println!("Value: {}", value);
}
