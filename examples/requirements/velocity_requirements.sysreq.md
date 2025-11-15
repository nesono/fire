# Velocity Requirements

## REQ-VEL-001

```yaml
sil: ASIL-D
sec: false
version: 2
```

**Maximum Vehicle Velocity**

The vehicle SHALL NOT exceed the maximum design velocity defined by [@maximum_vehicle_velocity](/examples/vehicle_params.bzl#maximum_vehicle_velocity) (55.0 m/s) under any operating conditions.

### Rationale

This requirement is derived from [ISO 26262:2018, Part 3, Section 7](https://www.iso.org/standard/68383.html) safety analysis for ASIL-D classification. The maximum velocity is constrained by:

- Mechanical stress limits on drivetrain components
- Tire rating specifications
- Braking system performance envelope (see [REQ-BRK-001](/examples/requirements/braking_requirements.sysreq.md?version=1#REQ-BRK-001))
- Control system response time requirements

### Verification

- Static analysis of control algorithms
- Hardware-in-the-loop testing with velocity limiting scenarios
- Vehicle dynamics simulation at boundary conditions
- Track testing with instrumentation (see [vehicle_params_test](//examples:vehicle_params_test))

### Changelog

- **Version 2**: Added parent requirement version tracking support
- **Version 1**: Initial maximum velocity requirement definition

---
