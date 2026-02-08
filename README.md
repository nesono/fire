# Fire - Fully Integrated Requirements Engineering

A Requirements Management System for Bazel

[![CI](https://github.com/nesono/fire/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/nesono/fire/actions/workflows/ci.yaml)

Fire is a Bazel module for managing safety-critical system requirements,
parameters, and their relationships with support by Bazel's dependency graph.

It is based on the following basic concepts:

- **Parameters** (e.g. max speed) are defined in YAML files
- **System** or **Software Component Requirements** are specified in Markdown files
- **References** from Markdown files are all using Markdown link syntax
- References support **versioning**, to flag affected downstream consumers
- Parameters can be **consumed from source code** through code generated libraries
- Support for **reporting**, e.g. for collaterals for notified bodies

## Usage

### Consume Fire

Add Fire to your `MODULE.bazel`:

```starlark
bazel_dep(name = "fire", version = "0.2.1")

# Add language rules for the languages you want to use (optional)
bazel_dep(name = "rules_cc", version = "0.2.16")      # For C++ code generation
bazel_dep(name = "rules_python", version = "1.7.0")   # For Python code generation
# Add rules_rust, rules_go, rules_java as needed
```

**Important**: Fire provides code generation functions that output source files
(no Bazel targets). The reason is mostly to not clutter the consumers
dependency tree with languages they might not need. The consumer is responsible
for wrapping these source files into language's library targets or binaries.
This keeps Fire's dependencies minimal - Fire itself only depends on
`rules_python` (for YAML validation).

### Define Parameter Libraries

Add parameters to a YAML file, e.g. like the following:

In file `vehicle_params.yaml`

```yaml
maximum_vehicle_velocity_v1:
  value: 55.0 # Type inferred as f64 from YAML float
  unit: m/s
  description: Maximum design velocity for the vehicle

wheel_count_v1:
  value: 4 # Type inferred as i64 from YAML integer
  description: Number of wheels on the vehicle

braking_distance_table_v1:
  type: table # Tables require explicit type declaration
  description: Braking distances under various conditions
  columns:
    - name: velocity
      type: f64 # Column types are explicit
      unit: m/s
    - name: friction_coefficient
      type: f64
      unit: dimensionless
    - name: braking_distance
      type: f64
      unit: m
  rows:
    - [10.0, 0.7, 7.1]
    - [20.0, 0.7, 28.6]
    - [30.0, 0.7, 64.3]
```

**Type Inference**: Types are automatically inferred from YAML native types:

- YAML integer (e.g., `42`) → `i64` (64-bit signed integer)
- YAML float (e.g., `42.0`) → `f64` (64-bit double)
- YAML boolean (e.g., `true`, `false`) → `bool`
- YAML string (e.g., `"text"`) → `string`
- Tables require explicit `type: table` and typed columns

**Versioning**: Parameter keys use a `_vN` suffix to encode the version (e.g., `maximum_vehicle_velocity_v1`).
When a parameter is updated, add a new key with the next version while keeping the old one
(e.g., `maximum_vehicle_velocity_v1` + `maximum_vehicle_velocity_v2`). Versions must be
consecutive starting from 1.

### Generated Directory Structure

Code generation produces a directory (TreeArtifact) of per-parameter-version files:

```text
vehicle_params/              # TreeArtifact produced by codegen rule
  wheel_count_v1.py          # One file per parameter per version
  maximum_vehicle_velocity_v1.py
  maximum_vehicle_velocity_v2.py
  braking_distance_table_v1.py
```

**Go uses sub-packages** (since Go packages = directories):

```text
vehicle_params/
  wheel_count_v1/
    wheel_count_v1.go        # package wheel_count_v1
  maximum_vehicle_velocity_v1/
    maximum_vehicle_velocity_v1.go
```

**Java uses PascalCase class names:**

```text
vehicle_params/
  WheelCountV1.java
  MaximumVehicleVelocityV1.java
```

Each file exposes a simple constant (no accessor functions, no version dispatch).
Version is encoded in the import/include path. Old versions that coexist with
newer versions contain deprecation warnings. Non-existent versions produce natural
build errors (file not found).

### Create Bazel Targets For the Parameters

In your `BUILD.bazel` file (e.g., in `vehicle/dynamics/`):

```starlark
load("@fire//fire/starlark:parameters.bzl", "parameter_library")
load("@fire//fire/starlark:codegen.bzl", "generate_cc_parameters")
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")

# Step 1: Validate parameters from YAML file
parameter_library(
    name = "vehicle_params",
    srcs = "vehicle_params.yaml",
)

# Step 2: Generate C++ header directory
generate_cc_parameters(
    name = "vehicle_params_h",
    parameter_library = ":vehicle_params",
    namespace = "vehicle::dynamics",  # Optional namespace
)

# Step 3: Wrap in cc_library (you control this)
cc_library(
    name = "vehicle_params_cc",
    hdrs = [":vehicle_params_h"],
)

# Step 4: Use generated parameters in C++ code
cc_test(
    name = "dynamics_test",
    srcs = ["dynamics_test.cc"],
    deps = [":vehicle_params_cc"],
)
```

### Consumption in Code

All imports/includes are **repository-relative** (e.g., `vehicle/dynamics/vehicle_params/...`).

**C++ usage**

```cpp
#include "vehicle/dynamics/vehicle_params/maximum_vehicle_velocity_v1.h"
#include "vehicle/dynamics/vehicle_params/wheel_count_v1.h"
#include "vehicle/dynamics/vehicle_params/braking_distance_table_v1.h"

int main() {
    double max_vel = MAXIMUM_VEHICLE_VELOCITY;
    int wheels = WHEEL_COUNT;

    // Access table data
    auto table = braking_distance_table();
    for (size_t i = 0; i < BRAKING_DISTANCE_TABLE_SIZE; ++i) {
        double velocity = table[i].velocity;
        double friction = table[i].friction_coefficient;
        double distance = table[i].braking_distance;
    }

    return 0;
}
```

**Python usage**

```python
from vehicle.dynamics.vehicle_params.maximum_vehicle_velocity_v1 import MAXIMUM_VEHICLE_VELOCITY
from vehicle.dynamics.vehicle_params.wheel_count_v1 import WHEEL_COUNT
from vehicle.dynamics.vehicle_params.braking_distance_table_v1 import BRAKING_DISTANCE_TABLE

def test_parameters():
    assert MAXIMUM_VEHICLE_VELOCITY == 55.0
    assert WHEEL_COUNT == 4

    for row in BRAKING_DISTANCE_TABLE:
        print(f"v={row.velocity}, d={row.braking_distance}")
```

**Go usage**

```go
import (
    velocity "yourproject/vehicle/dynamics/vehicle_params/maximum_vehicle_velocity_v1"
    wheels "yourproject/vehicle/dynamics/vehicle_params/wheel_count_v1"
    braking "yourproject/vehicle/dynamics/vehicle_params/braking_distance_table_v1"
)

func TestParameters(t *testing.T) {
    if velocity.MaximumVehicleVelocity != 55.0 {
        t.Error("Unexpected velocity")
    }

    for _, row := range braking.BrakingDistanceTable {
        // Access row.Velocity, row.FrictionCoefficient, row.BrakingDistance
    }
}
```

**Rust usage**

```rust
use vehicle_params_rs::*;

#[test]
fn test_parameters() {
    assert_eq!(MAXIMUM_VEHICLE_VELOCITY_V1, 55.0);
    assert_eq!(BRAKING_DISTANCE_TABLE_V1_SIZE, 6);

    for row in &BRAKING_DISTANCE_TABLE_V1 {
        println!("v={}, d={}", row.velocity, row.braking_distance);
    }
}
```

**Java usage**

```java
import static com.example.VehicleParams.*;

public class DynamicsTest {
    @Test
    public void testParameters() {
        // Simple parameters accessed directly
        assertEquals(55.0, MaximumVehicleVelocityV1, 0.001);
        assertEquals(4, WheelCountV1);

        // Tables accessed through nested classes
        for (var row : BrakingDistanceTableV1.TABLE) {
            // Access row.velocity(), row.frictionCoefficient(), row.brakingDistance()
        }
    }
}
```

### Multi-Language Support

Generate parameters for Python, Java, Go, and Rust (in `vehicle/dynamics/`):

```starlark
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")
load("@rules_go//go:def.bzl", "go_library", "go_test")
load("@rules_java//java:defs.bzl", "java_library", "java_test")
load("@rules_python//python:defs.bzl", "py_library", "py_test")
load("@rules_rust//rust:defs.bzl", "rust_test")
load("//fire/starlark:codegen.bzl", "generate_cc_parameters", "generate_go_parameters", "generate_java_parameters", "generate_python_parameters", "generate_rust_parameters")
load("//fire/starlark:parameters.bzl", "parameter_library")

# Validate and create parameter library from YAML file
parameter_library(
    name = "vehicle_params",
    srcs = "vehicle_params.yaml",
)

# Generate C++ headers (directory of per-param-version .h files)
generate_cc_parameters(
    name = "vehicle_params_h",
    base_name = "vehicle_params",
    parameter_library = ":vehicle_params",
)

cc_library(
    name = "vehicle_params_cc",
    hdrs = [":vehicle_params_h"],
)

# Generate Python modules (directory of per-param-version .py files)
generate_python_parameters(
    name = "vehicle_params_py_src",
    base_name = "vehicle_params",
    parameter_library = ":vehicle_params",
)

py_library(
    name = "vehicle_params_py",
    data = [":vehicle_params_py_src"], # note that we need to use `data` here
)

# Generate Java classes (directory of per-param-version .java files)
generate_java_parameters(
    name = "vehicle_params_java_src",
    package_prefix = "com.example",
    parameter_library = ":vehicle_params",
)

java_library(
    name = "vehicle_params_java",
    srcs = [":vehicle_params_java_src"],
)

# Generate Go source (directory of sub-packages)
generate_go_parameters(
    name = "vehicle_params_go_src",
    base_name = "vehicle_params",
    parameter_library = ":vehicle_params",
)

# Go needs per-sub-package go_library targets
go_library(
    name = "wheel_count_v1_go",
    srcs = [":vehicle_params_go_src"],
    importpath = "vehicle/dynamics/vehicle_params/wheel_count_v1",
)

# Generate Rust modules (directory of per-param-version .rs files)
generate_rust_parameters(
    name = "vehicle_params_rs",
    base_name = "vehicle_params",
    parameter_library = ":vehicle_params",
)
```

### Defining System Requirements

System requirements are written in Markdown with a specific structure (that is
validated by Fire). Requirements are collected in Bazel targets as follows:

```starlark
load("//fire/starlark:requirements.bzl", "requirement_library")

requirement_library(
  name = "vehicle_requirements",
  srcs = glob(["*.md"]),
  deps = [":vehicle_params"],
)
```

## Requirements Format

Requirements use section-based Markdown. The H1 header (`#`) can be chosen
freely - we recommend to use a human readable title.
Each requirement in the requirements file is identified by an H2 header (`##`)
followed by blank line and then a line containing some structured data.

### System Requirements (`.sysreq.md`)

Note that the important part here is the header 2 (`##`), that includes the ID
of the requirement and must be followed by a line containing SIL, Sec, and
Version separated by `|` characters. The header 3 (`###`) sections are free
text for now, even though we highly recommend you to use a fixed format for it.
Note that a requirement file can contain multiple of such requirements.

**Format:**

- H2 headers (`##`) for requirement IDs
- Text line with 3 fields: `SIL`, `Sec`, `Version`
- Bold text (`**Title**`) for human readable requirement title (recommended)
- Markdown links for all references (parameters, standards)

**Text Fields:**

- `SIL`: Safety/Assurance Classification - supports multiple industry standards:
  - `ASIL-A/B/C/D`: ISO 26262 (Automotive Safety Integrity Level)
  - `SIL-1/2/3/4`: IEC 61508 (General Industrial Safety Integrity Level)
  - `DAL-A/B/C/D/E`: DO-178C/DO-254 (Aviation Design Assurance Level)
  - `QM`: Quality Management (no safety classification)
- `Sec`: Security-related flag - `true` or `false`
- `Version`: Positive integer version number (1, 2, 3, ...)

**Example**:

```markdown
# Velocity Requirements

## REQ-VEL-001

SIL: ASIL-D | Sec: false | Version: 2

**Maximum Vehicle Velocity**

The vehicle SHALL NOT exceed the maximum design velocity defined by [@maximum_vehicle_velocity](/examples/vehicle_params.yaml?version=1#maximum_vehicle_velocity) (55.0 m/s) under any operating conditions.

### Rationale

This requirement is derived from [ISO 26262:2018, Part 3, Section 7](https://www.iso.org/standard/68383.html) safety analysis for ASIL-D classification. The maximum velocity is constrained by:

- Mechanical stress limits on drivetrain components
- Tire rating specifications
- Braking system performance envelope
- Control system response time requirements

### Verification

- Static analysis of control algorithms
- Hardware-in-the-loop testing with velocity limiting scenarios
- Vehicle dynamics simulation at boundary conditions
- Track testing with instrumentation

### Changelog

- **Version 2**: Added parent requirement version tracking support
- **Version 1**: Initial maximum velocity requirement definition
```

### Software Component Requirements (`.swreq.md`)

Software component requirements are derived from system requirements and follow a similar minimal format.

**Format:**

- H2 headers (`##`) for requirement IDs (e.g., `REQ_BC_CALCULATE_FORCE`)
- Text line with 4 fields: `SIL`, `Sec`, `Version`, `Parent`
- Bold text (`**Title**`) for human readable requirement title (recommended)
- Markdown links for all references (parameters, tests, standards)

**Example:**

```markdown
# Software Requirements: Brake Controller

## REQ_BC_CALCULATE_FORCE

SIL: ASIL-D | Sec: false | Version: 2 | Parent: [REQ-BRK-001](/examples/requirements/braking_requirements.sysreq.md?version=1#REQ-BRK-001)

The brake controller component shall calculate the required brake force...
```

**Aviation Example (DAL):**

```markdown
# Flight Control Requirements

## REQ-FCS-001

SIL: DAL-A | Sec: false | Version: 1

**Flight Control Update Rate**

The flight control system SHALL maintain the update rate defined by [@fcs_update_rate](/avionics/params.yaml?version=1#fcs_update_rate) to ensure deterministic real-time performance per DO-178C Level A requirements.

### Verification

- Timing analysis with worst-case execution time (WCET) analysis
- Real-time operating system (RTOS) scheduler verification
- Hardware-in-the-loop testing with flight scenarios
```

Note that all requirement files can contain multiple requirements separated by

```markdown
---
```

### Markdown References

All cross-references use standard Markdown links with repository-relative paths:

- **Parameter Reference**: `[@param_name](/path/to/file.yaml?version=1#param_name)`
  - Uses `@` prefix to distinguish from regular links
  - Link name needs to correspond to the target name
  - Example: `[@maximum_vehicle_velocity](/examples/vehicle_params.yaml?version=1#maximum_vehicle_velocity)`

- **Requirement Reference**: `[REQ-ID](/path/to/file.sysreq.md?version=N#REQ-ID)`
  - Includes `?version=N` query parameter to track parent version
  - Needs to start with a `/`
  - Needs to be repository-relative
  - Link name needs to correspond to the target name
  - Example: `[REQ-VEL-001](/examples/requirements/velocity_requirements.sysreq.md?version=2#REQ-VEL-001)`

- **Standard Reference**: `[text](https://url)`
  - Standard Markdown links for external standards and specifications
  - Example: `[ISO 26262:2018, Part 3](https://www.iso.org/standard/68383.html)`

### Version Tracking

System requirements track their own versions in text line. Software requirements track parent versions in Markdown links.

**Detecting Stale Requirements:**

When a parent requirement version changes (e.g., REQ-VEL-001 v2 -> v3), any child requirement still referencing `?version=2` is flagged as potentially needing review.

### Generating Reports with Bazel

Fire provides a `generate_report` Bazel rule to create reports at build time:

```python
load("//fire/starlark:reports.bzl", "generate_report")

# Generate traceability matrix
generate_report(
    name = "traceability_matrix",
    srcs = glob(["requirements/*.md"]),
    report_type = "traceability",
    out = "TRACEABILITY_MATRIX.md",
)

# Generate coverage report
generate_report(
    name = "coverage_report",
    srcs = glob(["requirements/*.md"]),
    report_type = "coverage",
    out = "COVERAGE_REPORT.md",
)

# Generate change impact analysis
generate_report(
    name = "change_impact_report",
    srcs = glob(["requirements/*.md"]),
    report_type = "change_impact",
    out = "CHANGE_IMPACT.md",
)

# Generate compliance report
generate_report(
    name = "compliance_report",
    srcs = glob(["requirements/*.md"]),
    report_type = "compliance",
    standard = "ISO 26262",  # or "IEC 61508", etc.
    critical_type = "safety",  # Optional: highlight critical requirements
    out = "COMPLIANCE_ISO26262.md",
)
```

Build reports:

```bash
# Build specific report
bazel build //path/to:traceability_matrix

# View generated report
cat bazel-bin/path/to/TRACEABILITY_MATRIX.md

# Build all reports
bazel build //path/to:traceability_matrix //path/to:coverage_report //path/to:change_impact_report //path/to:compliance_report
```

**Available Report Types**:

- `traceability`: Full traceability matrix with Requirements -> Parameters, Requirements -> Requirements (with versions), Requirements -> Standards
- `coverage`: Metrics showing percentage of requirements with parameter references and standard references
- `change_impact`: Identifies requirements with stale parent version references
- `compliance`: Compliance report for a specific standard
  - Attributes: `standard` (required, e.g., "ISO 26262", "IEC 61508"), `critical_type` (optional, e.g., "safety", "security")
  - Shows breakdown by requirement type, status distribution, and compliance gaps
  - Highlights critical requirement type if specified

## Contributing

1. PRs are welcome, even though we are at a very early stage
2. Write tests for your features, both good path and bad path
3. Use `pre-commit.com` and adhere to the checks
4. Provide integration tests where appropriate
