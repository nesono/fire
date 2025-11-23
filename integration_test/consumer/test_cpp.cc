#include <iostream>
#include "test_params.h"  // Root package - no prefix needed

int main() {
    // Test that generated constants are accessible via version-checked functions
    std::cout << "Max Speed: " << root::max_speed<1>() << " m/s" << std::endl;
    std::cout << "Min Braking Distance: " << root::min_braking_distance<1>() << " m" << std::endl;
    std::cout << "Update Rate: " << root::update_rate<1>() << " Hz" << std::endl;

    // Basic validation
    if (root::max_speed<1>() != 30.0) {
        std::cerr << "ERROR: max_speed has wrong value!" << std::endl;
        return 1;
    }
    if (root::min_braking_distance<1>() != 50.0) {
        std::cerr << "ERROR: min_braking_distance has wrong value!" << std::endl;
        return 1;
    }
    if (root::update_rate<1>() != 100) {
        std::cerr << "ERROR: update_rate has wrong value!" << std::endl;
        return 1;
    }

    std::cout << "C++ integration test PASSED" << std::endl;
    return 0;
}
