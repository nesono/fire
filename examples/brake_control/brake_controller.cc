#include "examples/brake_control/brake_controller.h"

#include <algorithm>

namespace brake_control {

BrakeCommand calculate_brake_force(const VehicleState& state,
                                   double target_deceleration) {
    BrakeCommand cmd;
    cmd.emergency_mode = !validate_inputs(state);

    if (cmd.emergency_mode) {
        cmd.force_percent = 100.0;
        return cmd;
    }

    double error = target_deceleration - state.acceleration_mps2;
    double raw_force = error * 10.0;  // simplified P-controller
    cmd.force_percent = clamp_force(raw_force);
    return cmd;
}

bool validate_inputs(const VehicleState& state) {
    if (state.speed_mps < 0.0 || state.speed_mps > 30.0) return false;
    if (state.acceleration_mps2 < -15.0 || state.acceleration_mps2 > 5.0)
        return false;
    if (state.friction_coefficient < 0.3 || state.friction_coefficient > 0.9)
        return false;
    return true;
}

double clamp_force(double force_percent) {
    return std::clamp(force_percent, 0.0, 100.0);
}

}  // namespace brake_control
