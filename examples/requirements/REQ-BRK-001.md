---
id: REQ-BRK-001
title: Emergency Braking Distance
type: functional
status: approved
priority: high
owner: dynamics-team
tags: [braking, safety, performance]
version: 1
changelog:
  - version: 1
    description: Initial emergency braking requirement, derived from REQ-VEL-001 v2
references:
  parameters:
    - braking_distance_table
  requirements:
    - id: REQ-VEL-001
      version: 2
  standards:
    - UN ECE R13-H
  tests:
    - //examples:vehicle_params_test
---

# REQ-BRK-001: Emergency Braking Distance

## Description

The vehicle SHALL be capable of performing emergency braking from any velocity up to maximum design velocity (see [REQ-VEL-001](REQ-VEL-001.md)), achieving deceleration
according to the [@braking_distance_table](../vehicle_params.bzl#braking_distance_table) parameters.

## Rationale

Emergency braking performance is critical for collision avoidance and overall vehicle safety. The braking distances are calculated based on:

- Maximum tire-road friction coefficients under various conditions
- Maximum allowable deceleration (passenger comfort and safety)
- System response time and actuator dynamics

Compliance with [UN ECE R13-H](https://unece.org/transport/documents/2021/03/standards/un-regulation-no-13-h-braking-heavy-vehicles) ensures international safety standards.

## Acceptance Criteria

For each velocity and friction coefficient pair in [@braking_distance_table](../vehicle_params.bzl#braking_distance_table):

1. Vehicle SHALL achieve full stop within specified distance ±5%
2. Deceleration SHALL be smooth and controlled (no wheel lock)
3. Braking SHALL be repeatable across 100 consecutive tests

## Verification

Testing is performed according to [vehicle_params_test](../BUILD.bazel#vehicle_params_test):

- Brake dynamometer testing
- Proving ground testing on various surfaces (dry, wet, low friction)
- Automated emergency braking (AEB) system integration tests
- Tire friction coefficient measurement and validation

## Dependencies

- Requires brake-by-wire system (REQ-ACT-003)
- Requires ABS functionality (REQ-ABS-001)
- Requires tire specification compliance (REQ-TIRE-001)

## Test Data

Expected test coverage:

- 30 km/h increments from 0 to maximum velocity
- Friction coefficients: 0.1, 0.3, 0.5, 0.7, 0.9
- Surface conditions: dry asphalt, wet asphalt, gravel, ice
