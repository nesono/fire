# Fire Examples

This directory contains example files demonstrating the complete traceability chain in Fire, from system requirements through software components.

## Directory Structure

```text
examples/
├── requirements/          # System requirements (.sysreq.md)
├── system_functions/      # System function specifications with DFDs (.sysarch.md)
├── brake_control/doc/     # Brake controller techspec and software requirements
├── vehicle_status/doc/    # Vehicle status techspec and software requirements
└── brake_actuator/doc/    # Brake actuator techspec and software requirements
```

Each software component directory contains:

- `.techspec.md` - Technical specification with architecture and algorithms
- `.swreq.md` - Software requirements derived from system requirements

## Traceability Chain Example

This example demonstrates the complete traceability from system to software:

```text
System Requirement (REQ-BRK-001, REQ-VEL-001)
    ↓ implements via
System Function (BRAKING_CONTROL_SYSTEM)
    ↓ composed of
Software Components (brake_control, vehicle_status, brake_actuator)
    ↓ defines
Software Requirements (REQ_BC_*, REQ_VS_*, REQ_BA_*)
    ↓ verified by
Tests (component_tests)
```

### 1. System Requirement: REQ-BRK-001

**File**: `requirements/REQ-BRK-001.sysreq.md`

Defines the system-level requirement for vehicle braking distance at various speeds and friction conditions. Uses the `@braking_distance_table` parameter.

**Key attributes**:

- Type: `functional`
- SIL: `ASIL-D`
- References: Parameter `braking_distance_table`, Test `vehicle_params_test`

### 2. System Function: BRAKING_CONTROL_SYSTEM

**File**: `system_functions/braking_control.sysarch.md`

Defines the system function that implements REQ-BRK-001 using a data flow diagram (DFD) showing component interactions.

**Key attributes**:

- Implements: `REQ-BRK-001`
- Composed of: `brake_control`, `vehicle_status`, `brake_actuator` components
- Includes: Mermaid DFD, communication links table

### 3. Software Components

The braking system function is implemented by three software components working together:

#### A. Brake Controller (`brake_control/`)

Contains the complete specification for the main brake control logic component:

**Technical Specification**: `brake_control/doc/brake_controller.techspec.md`

Detailed design document including:

- PID control algorithm with feed-forward compensation
- Architecture diagram (Mermaid)
- Interface specifications (inputs, outputs, constraints)
- Component logic (50 Hz control loop)
- Emergency braking mode
- Security considerations and resource requirements

**Software Requirements**: `brake_control/doc/brake_controller.swreq.md` (8 requirements)

Software-level requirements derived from REQ-BRK-001:

- `REQ_BC_CALCULATE_FORCE` - Brake force calculation with PID
- `REQ_BC_MONITOR_DECELERATION` - Deceleration monitoring at 50 Hz
- `REQ_BC_USE_BRAKING_TABLE` - Parameter table usage with interpolation
- `REQ_BC_EMERGENCY_BRAKE` - Emergency braking logic
- `REQ_BC_OUTPUT_RATE` - Output timing requirements (50 Hz)
- `REQ_BC_INPUT_VALIDATION` - Input range validation
- `REQ_BC_FORCE_LIMITS` - Safety limits [0, 100]%
- `REQ_BC_INITIALIZATION` - Startup behavior

#### B. Vehicle Status (`vehicle_status/`)

Provides current vehicle state information from sensors:

**Technical Specification**: `vehicle_status/doc/vehicle_status.techspec.md`

Key features:

- Reads 4 wheel speed sensors via CAN bus at 100 Hz
- Calculates vehicle linear speed by averaging wheel speeds
- Calculates acceleration with low-pass filtering
- Performs sensor plausibility checks and cross-validation
- Publishes vehicle status at 100 Hz

**Software Requirements**: `vehicle_status/doc/vehicle_status.swreq.md` (5 requirements)

Requirements derived from REQ-VEL-001:

- `REQ_VS_READ_SENSORS` - Read wheel speeds at 100 Hz
- `REQ_VS_CALCULATE_SPEED` - Convert RPM to linear velocity
- `REQ_VS_CALCULATE_ACCELERATION` - Calculate and filter acceleration
- `REQ_VS_PUBLISH_STATUS` - Publish status at 100 Hz
- `REQ_VS_VALIDATE_SENSORS` - Sensor plausibility checking

#### C. Brake Actuator (`brake_actuator/`)

Interfaces with physical brake hardware:

**Technical Specification**: `brake_actuator/doc/brake_actuator.techspec.md`

Key features:

- Receives brake force commands at 50 Hz
- Converts force percentage to hydraulic pressure (0-120 bar)
- PI controller running at 1000 Hz for pressure control
- Controls electro-hydraulic valve via PWM
- Monitors actual pressure feedback
- Enforces safety limits and timeout protection

**Software Requirements**: `brake_actuator/doc/brake_actuator.swreq.md` (5 requirements)

Requirements derived from REQ-BRK-001:

- `REQ_BA_RECEIVE_COMMANDS` - Receive brake commands at 50 Hz
- `REQ_BA_CONVERT_FORCE` - Convert force % to pressure (bar)
- `REQ_BA_CONTROL_HYDRAULICS` - PI controller at 1000 Hz
- `REQ_BA_MONITOR_PRESSURE` - Read pressure sensor at 1000 Hz
- `REQ_BA_SAFETY_LIMITS` - Enforce pressure and rate limits

All requirements reference appropriate parent system requirements.

## Building and Testing

```bash
# Run all tests including swreq validation
bazel test //fire/starlark:swreq_validator_test

# Build all example targets
bazel build //examples/...

# Run parameter tests
bazel test //examples:vehicle_params_test

# Generate reports (when implemented)
bazel build //examples:traceability_report
bazel build //examples:compliance_report
```

## File Format Conventions

### System Requirements (`.sysreq.md`)

- YAML frontmatter with metadata (id, title, type, status, priority, sil, etc.)
- Markdown body with description, rationale, verification
- Cross-references to parameters, tests, standards

### System Functions (`.sysarch.md`)

- YAML frontmatter (id, title, type, sil, implements_requirements, composed_of)
- Mermaid DFD diagram
- Links table showing data flows
- Behavior description

### Software Requirements (`.swreq.md`)

- YAML frontmatter (component, version, sil, security_related, system_function)
- List-based requirements format with sections for each requirement
- Each requirement has: ID, Parent, SIL, Sec, Description

### Technical Specifications (`.techspec.md`)

- YAML frontmatter (component, version, sil, security_related, system_function, implements_requirements)
- Sections: Introduction, Requirements, Architecture, Component Logic, Interfaces, Security

## Standards Support

The examples demonstrate support for multiple safety standards:

- **ISO 26262** (Automotive): ASIL-A/B/C/D
- **IEC 61508** (Industrial): SIL-1/2/3/4
- **DO-178C** (Avionics): DAL-A/B/C/D/E

In this example, the braking system uses **ASIL-D** (highest automotive safety level).

## Cross-Reference Validation

Fire validates cross-references at build time:

- System requirements → Parameters (via `@parameter_name` syntax)
- System requirements → Tests (via Bazel labels)
- System functions → System requirements
- Software components → System functions
- Software requirements → Parent system requirements
- Technical specifications → Software requirements

All references use **repository-relative paths** for consistency.
