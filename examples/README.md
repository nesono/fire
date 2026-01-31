# Fire Examples

This directory contains example files demonstrating the complete traceability chain in Fire, from system requirements through software components.

## Directory Structure

```text
examples/
├── requirements/          # System requirements (.sysreq.md)
├── brake_control/doc/     # Brake controller techspec and software requirements
├── vehicle_status/doc/    # Vehicle status techspec and software requirements
└── brake_actuator/doc/    # Brake actuator techspec and software requirements
```

Each software component directory contains a `.swreq.md` file which in turn
contains software requirements derived from system requirements

## Traceability Chain Example

This example demonstrates the complete traceability from system to software:

```text
System Requirement (REQ-BRK-001, REQ-VEL-001)
    ↓ implemented via
Software Components (brake_control, vehicle_status, brake_actuator)
    ↓ defines
Software Requirements (REQ_BC_*, REQ_VS_*, REQ_BA_*)
    ↓ verified by
Tests (component_tests)
```
