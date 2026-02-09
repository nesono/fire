#pragma once

/// Brake controller component.
///
/// Calculates required brake force based on vehicle state and publishes
/// brake commands at 50 Hz.  See brake_controller.swreq.md for the
/// full set of software requirements this component implements.

namespace brake_control {

struct VehicleState {
    double speed_mps;
    double acceleration_mps2;
    double friction_coefficient;
};

struct BrakeCommand {
    double force_percent;
    bool emergency_mode;
};

/// Calculate the brake force for the given vehicle state.
BrakeCommand calculate_brake_force(const VehicleState& state,
                                   double target_deceleration);

/// Validate that all input values are within their allowed ranges.
bool validate_inputs(const VehicleState& state);

/// Clamp brake force to [0, 100] percent.
double clamp_force(double force_percent);

}  // namespace brake_control
