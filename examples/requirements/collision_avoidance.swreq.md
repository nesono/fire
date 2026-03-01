# Collision Avoidance Software Requirements

This document contains software requirements for the collision avoidance system,
which integrates emergency braking and velocity control to prevent accidents.

## REQ-CA-EMERGENCY-BRAKE

SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-BRK-001](/examples/requirements/braking_requirements.sysreq.md?version=4#REQ-BRK-001) |
Parent: [REQ-VEL-001](/examples/requirements/velocity_requirements.sysreq.md?version=2#REQ-VEL-001)

**Velocity-Aware Emergency Braking**

The collision avoidance system SHALL calculate emergency braking distance based on
current vehicle velocity and initiate braking when an obstacle is detected within
the calculated stopping distance plus a safety margin of 2 meters.

### Rationale

This requirement derives from both:

- **REQ-BRK-001**: Provides the emergency braking capability and distance parameters
- **REQ-VEL-001**: Provides the current velocity measurement required for distance calculation

The integration of these two system requirements ensures that braking decisions
account for both the vehicle's current speed and its physical braking capabilities.

### Implementation Details

The software shall:

1. Subscribe to velocity measurements from the speed sensor at 100 Hz
2. Query braking distance parameters from [@braking_distance_table] based on:
   - Current velocity
   - Estimated road friction coefficient
3. Calculate required stopping distance with safety margin
4. Compare against obstacle detection distance from sensor fusion
5. Trigger emergency braking when threshold is exceeded

### Acceptance Criteria

1. Velocity readings SHALL be sampled at ≥100 Hz
2. Braking distance calculation SHALL complete within 5 ms
3. Emergency brake command SHALL be issued within 10 ms of threshold detection
4. System SHALL correctly interpolate between discrete velocity values in braking table
5. Safety margin SHALL be configurable between 1-5 meters

### Verification

- Unit tests for distance calculation algorithm
- Integration tests with simulated velocity and obstacle inputs
- Hardware-in-the-loop testing on vehicle test bench
- Track testing at various speeds and road conditions

### Reference-Style Link Definitions

[@braking_distance_table]: /examples/vehicle_params.yaml?version=1#braking_distance_table

---

## REQ-CA-ADAPTIVE-CRUISE

SIL: ASIL-B | Sec: false | Version: 1 | Parent: [REQ-VEL-001](/examples/requirements/velocity_requirements.sysreq.md?version=2#REQ-VEL-001)

**Adaptive Cruise Control Velocity Management**

The collision avoidance system SHALL maintain a safe following distance by
modulating the target cruise velocity based on the distance to the leading vehicle.

### Rationale

This requirement derives from REQ-VEL-001 which establishes the maximum safe
velocity constraints. The adaptive cruise control ensures the vehicle operates
within these constraints while maintaining safe spacing.

### Implementation Details

The software shall:

1. Monitor distance to leading vehicle using forward radar
2. Calculate safe following distance as: `velocity * 2.0 seconds + 10 meters`
3. Reduce target cruise velocity when following distance < safe distance
4. Gradually restore cruise velocity when following distance > safe distance

### Acceptance Criteria

1. Target velocity SHALL NOT exceed maximum velocity from [REQ-VEL-001]
2. Following distance calculation SHALL update at ≥50 Hz
3. Velocity adjustments SHALL be smooth (max jerk ≤ 2 m/s³)
4. System SHALL disengage and alert driver if radar data is invalid

---

## REQ-CA-BRAKE-VELOCITY-COORDINATION

SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-BRK-001](/examples/requirements/braking_requirements.sysreq.md?version=4#REQ-BRK-001) |
Parent: [REQ-VEL-001](/examples/requirements/velocity_requirements.sysreq.md?version=2#REQ-VEL-001)

**Coordinated Braking and Velocity Control**

The collision avoidance system SHALL coordinate emergency braking activation with
velocity controller deactivation to prevent control conflicts.

### Rationale

This requirement derives from both parent requirements because:

- **REQ-BRK-001**: Defines emergency braking activation requirements
- **REQ-VEL-001**: Defines velocity control requirements

When emergency braking activates, the velocity controller must be smoothly
disengaged to prevent conflicting throttle and brake commands.

### Implementation Details

When emergency braking is triggered:

1. Immediately disable cruise control velocity tracking
2. Ramp down throttle command to 0% over 100 ms
3. Enable emergency brake controller
4. Monitor brake effectiveness and velocity reduction
5. Re-enable velocity control only after:
   - Emergency condition cleared
   - Driver explicitly re-engages cruise control

### Acceptance Criteria

1. Velocity controller SHALL disengage within 50 ms of brake trigger
2. Throttle SHALL reach 0% within 100 ms
3. No overlapping throttle and brake commands (exclusive control)
4. System SHALL NOT automatically re-enable cruise after emergency stop
5. Diagnostic logging SHALL record all mode transitions

### Test Cases

1. Emergency brake at various cruise velocities (30, 60, 90 km/h)
2. Rapid successive emergency brake events
3. Emergency brake during acceleration
4. Emergency brake during deceleration
5. Cruise re-engagement after emergency brake

---
