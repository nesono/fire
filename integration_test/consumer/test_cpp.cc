#include <iostream>
#include "test_params.h"  // Root package - no prefix needed

int main() {
    // Test that generated constants are accessible
    std::cout << "Max Speed: " << root::MAX_SPEED << " m/s" << std::endl;
    std::cout << "Min Braking Distance: " << root::MIN_BRAKING_DISTANCE << " m" << std::endl;
    std::cout << "Update Rate: " << root::UPDATE_RATE << " Hz" << std::endl;

    // Basic validation
    if (root::MAX_SPEED != 30.0) {
        std::cerr << "ERROR: MAX_SPEED has wrong value!" << std::endl;
        return 1;
    }
    if (root::MIN_BRAKING_DISTANCE != 50.0) {
        std::cerr << "ERROR: MIN_BRAKING_DISTANCE has wrong value!" << std::endl;
        return 1;
    }
    if (root::UPDATE_RATE != 100) {
        std::cerr << "ERROR: UPDATE_RATE has wrong value!" << std::endl;
        return 1;
    }

    std::cout << "C++ integration test PASSED" << std::endl;
    return 0;
}
