---
id: REQ-VEL-001
title: Maximum Vehicle Velocity
type: safety
status: approved
priority: critical
owner: safety-team
tags: [velocity, safety, ASIL-D]
version: 2
changelog:
  - version: 2
    description: Added parent requirement version tracking support
  - version: 1
    description: Initial maximum velocity requirement definition
references:
  parameters:
    - maximum_vehicle_velocity
  requirements:
    - REQ-BRK-001
  standards:
    - ISO 26262:2018, Part 3, Section 7
  tests:
    - //examples:vehicle_params_test
---

# REQ-VEL-001: Maximum Vehicle Velocity

## Description

The vehicle SHALL NOT exceed the maximum design velocity defined by [@maximum_vehicle_velocity](examples/vehicle_params.bzl#maximum_vehicle_velocity) (55.0 m/s) under any operating conditions.

## Rationale

This requirement is derived from [ISO 26262:2018, Part 3, Section 7](https://www.iso.org/standard/68383.html) safety analysis for ASIL-D classification. The maximum velocity is constrained by:

- Mechanical stress limits on drivetrain components
- Tire rating specifications
- Braking system performance envelope (see [REQ-BRK-001](examples/requirements/REQ-BRK-001.md))
- Control system response time requirements

## Verification

- Static analysis of control algorithms
- Hardware-in-the-loop testing with velocity limiting scenarios
- Vehicle dynamics simulation at boundary conditions
- Track testing with instrumentation (see [vehicle_params_test](//examples:vehicle_params_test))

## Notes

Version 2: Updated to track parent requirement versions

Last reviewed: 2024-01-15
Review period: Quarterly
