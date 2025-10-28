---
id: REQ-VEL-001
title: Maximum Vehicle Velocity
type: safety
status: approved
priority: critical
owner: safety-team
tags: [velocity, safety, ASIL-D]
---

# REQ-VEL-001: Maximum Vehicle Velocity

## Description

The vehicle SHALL NOT exceed the maximum design velocity of 55.0 m/s under any operating conditions.

## Rationale

This requirement is derived from ISO 26262:2018 safety analysis for ASIL-D classification. The maximum velocity is constrained by:
- Mechanical stress limits on drivetrain components
- Tire rating specifications
- Braking system performance envelope
- Control system response time requirements

## Verification

- Static analysis of control algorithms
- Hardware-in-the-loop testing with velocity limiting scenarios
- Vehicle dynamics simulation at boundary conditions
- Track testing with instrumentation

## References

- Parameter: `maximum_vehicle_velocity` (55.0 m/s)
- Standard: ISO 26262:2018, Part 3, Section 7
- Related: REQ-BRK-001 (Braking Performance)

## Notes

Last reviewed: 2024-01-15
Review period: Quarterly
