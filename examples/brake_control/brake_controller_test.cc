#include "examples/brake_control/brake_controller.h"

#include <cassert>
#include <cmath>
#include <iostream>

int main() {
    using namespace brake_control;

    // Normal braking
    VehicleState normal{.speed_mps = 20.0,
                        .acceleration_mps2 = -2.0,
                        .friction_coefficient = 0.7};
    auto cmd = calculate_brake_force(normal, -5.0);
    assert(!cmd.emergency_mode);
    assert(cmd.force_percent >= 0.0 && cmd.force_percent <= 100.0);

    // Emergency: speed out of range
    VehicleState too_fast{.speed_mps = 35.0,
                          .acceleration_mps2 = 0.0,
                          .friction_coefficient = 0.7};
    cmd = calculate_brake_force(too_fast, -5.0);
    assert(cmd.emergency_mode);
    assert(cmd.force_percent == 100.0);

    // Emergency: friction out of range
    VehicleState bad_friction{.speed_mps = 10.0,
                              .acceleration_mps2 = 0.0,
                              .friction_coefficient = 0.1};
    cmd = calculate_brake_force(bad_friction, -5.0);
    assert(cmd.emergency_mode);

    // Force clamping
    assert(clamp_force(150.0) == 100.0);
    assert(clamp_force(-10.0) == 0.0);
    assert(std::abs(clamp_force(50.0) - 50.0) < 1e-9);

    std::cout << "Brake controller tests PASSED" << std::endl;
    return 0;
}
