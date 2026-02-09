#include <iostream>
#include "test_params_cc/max_speed_v1.h"
#include "test_params_cc/min_braking_distance_v1.h"
#include "test_params_cc/update_rate_v1.h"

int main() {
    // Test that generated constants are accessible
    std::cout << "Max Speed: " << MAX_SPEED_MPS << " m/s" << std::endl;
    std::cout << "Min Braking Distance: " << MIN_BRAKING_DISTANCE << " m" << std::endl;
    std::cout << "Update Rate: " << UPDATE_RATE_HZ << " Hz" << std::endl;

    // Basic validation
    if (MAX_SPEED_MPS != 30.0) {
        std::cerr << "ERROR: MAX_SPEED_MPS has wrong value!" << std::endl;
        return 1;
    }
    if (MIN_BRAKING_DISTANCE != 50.0) {
        std::cerr << "ERROR: MIN_BRAKING_DISTANCE has wrong value!" << std::endl;
        return 1;
    }
    if (UPDATE_RATE_HZ != 100) {
        std::cerr << "ERROR: UPDATE_RATE_HZ has wrong value!" << std::endl;
        return 1;
    }

    std::cout << "C++ integration test PASSED" << std::endl;
    return 0;
}
