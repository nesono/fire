---
id: REQ-BRK-001
title: Emergency Braking Distance
type: functional
status: approved
priority: high
owner: dynamics-team
tags: [braking, safety, performance]
---

# REQ-BRK-001: Emergency Braking Distance

## Description

The vehicle SHALL be capable of performing emergency braking from any velocity up to maximum design velocity, achieving deceleration according to the braking distance table parameters.

## Rationale

Emergency braking performance is critical for collision avoidance and overall vehicle safety. The braking distances are calculated based on:
- Maximum tire-road friction coefficients under various conditions
- Maximum allowable deceleration (passenger comfort and safety)
- System response time and actuator dynamics

## Acceptance Criteria

For each velocity and friction coefficient pair in the `braking_distance_table`:
1. Vehicle SHALL achieve full stop within specified distance ±5%
2. Deceleration SHALL be smooth and controlled (no wheel lock)
3. Braking SHALL be repeatable across 100 consecutive tests

## Verification

- Brake dynamometer testing
- Proving ground testing on various surfaces (dry, wet, low friction)
- Automated emergency braking (AEB) system integration tests
- Tire friction coefficient measurement and validation

## References

- Parameter: `braking_distance_table`
- Standard: UN ECE R13-H (Heavy Vehicle Braking)
- Related: REQ-VEL-001 (Maximum Vehicle Velocity)
- Related: REQ-TCS-001 (Traction Control System)

## Dependencies

- Requires brake-by-wire system (REQ-ACT-003)
- Requires ABS functionality (REQ-ABS-001)
- Requires tire specification compliance (REQ-TIRE-001)

## Test Data

Expected test coverage:
- 30 km/h increments from 0 to maximum velocity
- Friction coefficients: 0.1, 0.3, 0.5, 0.7, 0.9
- Surface conditions: dry asphalt, wet asphalt, gravel, ice
