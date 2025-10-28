---
id: REQ-WHEEL-001
title: Wheel Count Configuration
type: constraint
status: approved
priority: medium
owner: platform-team
tags: [configuration, hardware]
references:
  parameters:
    - wheel_count
  tests:
    - //examples:vehicle_params_test
---

# REQ-WHEEL-001: Wheel Count Configuration

## Description

The vehicle SHALL be configured with exactly [@wheel_count](../vehicle_params.bzl#wheel_count) wheels as specified in the vehicle parameters.

## Rationale

The vehicle dynamics model, control algorithms, and safety systems are designed and validated for a 4-wheel configuration. Any deviation from this configuration would require:

- Complete re-validation of all dynamics and control models
- New safety analysis and certification
- Updates to all wheel-dependent algorithms (traction control, stability control, ABS)

## Constraints

- Physical wheel count MUST match parameter [@wheel_count](../vehicle_params.bzl#wheel_count)
- Each wheel MUST have independent sensor monitoring
- Wheel failure detection MUST account for all 4 wheels

## Verification

Testing is performed according to [vehicle_params_test](../BUILD.bazel#vehicle_params_test):

- Visual inspection during vehicle assembly
- Sensor count verification in startup diagnostics
- Configuration parameter cross-check at system initialization

## Design Notes

This is a configuration constraint rather than a functional requirement. While the code supports parameterization of wheel count, the current vehicle platform is
designed exclusively for 4-wheel operation. Future platforms (3-wheel, 6-wheel, etc.) would be separate variants with their own requirement sets.
