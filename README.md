# Fire - Requirements Management System for Bazel

[![CI](https://github.com/nesono/fire/actions/workflows/ci.yaml/badge.svg)](https://github.com/nesono/fire/actions/workflows/ci.yaml)

Fire is a Bazel module for managing safety-critical system requirements,
parameters, and their relationships through Bazel's dependency graph.

It is based on the following basic concepts:

- Parameters (e.g. max speed) are defined in YAML files
- System or Software Component Requirements are specified in Markdown files
- References from Markdown files are all using Markdown link syntax
- References support versioning, to flag affected downstream consumers
- Parameters can be consumed from source code through code generated libraries
- Support for reporting, e.g. for notified bodies

## Usage

### Consume Fire

Add Fire to your `MODULE.bazel`:

```starlark
bazel_dep(name = "fire", version = "0.2.1")

# Add language rules for the languages you want to use
bazel_dep(name = "rules_cc", version = "0.2.16")      # For C++ code generation
bazel_dep(name = "rules_python", version = "1.7.0")   # For Python code generation
# Add rules_rust, rules_go, rules_java as needed
```

**Important**: Fire provides code generation functions that output source
files. You are responsible for wrapping these in your language's library rules.
This keeps Fire's dependencies minimal - Fire only depends on rules_python (for
YAML validation).

### Define Parameter Libraries

Add parameters to a yaml file, e.g. like the following:

In file `vehicle_params.yaml`

```yaml
parameters:
  maximum_vehicle_velocity:
    type: f64
    unit: m/s
    value: 55.0
    description: Maximum design velocity for the vehicle

  wheel_count:
    type: i32
    value: 4
    description: Number of wheels on the vehicle

  braking_distance_table:
    type: table
    description: Braking distances under various conditions
    columns:
      - name: velocity
        type: f64
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

### Create Bazel Targets

In your `BUILD.bazel` file (e.g., in `vehicle/dynamics/`):

```starlark
load("@fire//fire/starlark:parameters.bzl", "parameter_library")
load("@fire//fire/starlark:codegen.bzl", "generate_cc_parameters")
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")

# Step 1: Validate parameters from YAML file
parameter_library(
    name = "vehicle_params",
    src = "vehicle_params.yaml",
)

# Step 2: Generate C++ header file
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

### Example Consumption in C++ Code

The generated header provides type-safe access to parameters:

```cpp
#include "vehicle/dynamics/vehicle_params.h"

int main() {
    // consume max velocity expecting version 1
    double max_vel = maximum_vehicle_velocity<1>();
    int wheels = wheel_count<1>;

    // Access table data
    auto table = braking_distance_table<1>();
    for (size_t i = 0; i < BRAKING_DISTANCE_TABLE_SIZE; ++i) {
        double velocity = table[i].velocity;
        double friction = table[i].friction_coefficient;
        double distance = table[i].braking_distance;
        // ... use the values
    }

    return 0;
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
# Namespace is auto-derived from package path: examples -> examples
parameter_library(
    name = "vehicle_params",
    src = "vehicle_params.yaml",
)

# Generate C++ header with parameters
# Consumes vehicle_params (validated YAML) and generates vehicle_params.h
generate_cc_parameters(
    name = "vehicle_params_h",
    base_name = "vehicle_params",
    parameter_library = ":vehicle_params",
)

# Wrap in cc_library
cc_library(
    name = "vehicle_params_cc",
    hdrs = [":vehicle_params_h"],
)

# Example: C++ header with custom namespace
generate_cc_parameters(
    name = "vehicle_params_custom_ns_h",
    base_name = "vehicle_params_custom_ns",
    namespace = "my_project::vehicle::params",
    parameter_library = ":vehicle_params",
)

# Wrap in cc_library
cc_library(
    name = "vehicle_params_cc_custom_ns",
    hdrs = [":vehicle_params_custom_ns_h"],
)

# Generate Python module with parameters
# Consumes vehicle_params (validated YAML) and generates vehicle_params.py
generate_python_parameters(
    name = "vehicle_params_py_src",
    base_name = "vehicle_params",
    parameter_library = ":vehicle_params",
)

# Wrap in py_library
py_library(
    name = "vehicle_params_py",
    srcs = [":vehicle_params_py_src"],
)

# Example: Second Python library (demonstrates multiple targets from same params)
generate_python_parameters(
    name = "vehicle_params_py_alt_src",
    base_name = "vehicle_params_py_alt",
    parameter_library = ":vehicle_params",
)

py_library(
    name = "vehicle_params_py_alt",
    srcs = [":vehicle_params_py_alt_src"],
)

# Generate Java class with parameters
# Consumes vehicle_params (validated YAML) and generates VehicleParams.java
generate_java_parameters(
    name = "vehicle_params_java_src",
    class_name = "VehicleParams",
    package_prefix = "com.example",
    parameter_library = ":vehicle_params",
)

# Wrap in java_library
java_library(
    name = "vehicle_params_java",
    srcs = [":vehicle_params_java_src"],
)

# Generate Go source with parameters
# Consumes vehicle_params (validated YAML) and generates vehicle_params.go
generate_go_parameters(
    name = "vehicle_params_go_src",
    base_name = "vehicle_params",
    parameter_library = ":vehicle_params",
)

# Wrap in go_library
go_library(
    name = "vehicle_params_go",
    srcs = [":vehicle_params_go_src"],
    importpath = "examples/vehicle_params",
)

# Example: Second Go library (demonstrates multiple targets from same params)
generate_go_parameters(
    name = "vehicle_params_go_alt_src",
    base_name = "vehicle_params_alt",
    parameter_library = ":vehicle_params",
)

go_library(
    name = "vehicle_params_go_alt",
    srcs = [":vehicle_params_go_alt_src"],
    importpath = "examples/vehicle_params_go_alt",
)

# Generate Rust module with parameters
# Consumes vehicle_params (validated YAML) and generates vehicle_params.rs
# Rust can use generated .rs files directly in srcs (no wrapper needed)
generate_rust_parameters(
    name = "vehicle_params_rs",
    base_name = "vehicle_params",
    parameter_library = ":vehicle_params",
)

# Example: Second Rust module (demonstrates multiple targets from same params)
generate_rust_parameters(
    name = "vehicle_params_rs_alt",
    base_name = "vehicle_params_rs_alt",
    parameter_library = ":vehicle_params",
)
```

**Python usage:**

```python
from vehicle_params_py import (
    maximum_vehicle_velocity,
    wheel_count,
    braking_distance_table_data,
    BrakingDistanceTableRow,
)

def test_parameters():
    assert maximum_vehicle_velocity(1) == 55.0
    assert wheel_count(1) == 4

    for row in braking_distance_table(1):
        print(f"v={row.velocity}, μ={row.friction_coefficient}, d={row.braking_distance}")
```

**Java usage:**

```java
import com.example.vehicle.dynamics.VehicleParams;

public class DynamicsTest {
    @Test
    public void testParameters() {
        assertEquals(55.0, VehicleParams.maximumVehicleVelocity(1));
        assertEquals(4, VehicleParams.wheelCount(1));

        for (var row : VehicleParams.brakingDistanceTable) {
            // Access row.velocity(), row.frictionCoefficient(), row.brakingDistance()
        }
    }
}
```

**Go usage:**

```go
import dynamics "yourproject/vehicle/dynamics"

func TestParameters(t *testing.T) {
    if dynamics.MaximumVehicleVelocity(1) != 55.0 {
        t.Error("Unexpected velocity")
    }

    for _, row := range dynamics.BrakingDistanceTable(1) {
        // Access row.Velocity, row.FrictionCoefficient, row.BrakingDistance
    }
}
```

**Rust usage:**

```rust
mod vehicle_params_rust;
use vehicle_params_rust::*;

#[test]
fn test_parameters() {
    assert_eq!(maximum_vehicle_velocity::<1>(), 55.0);
    assert_eq!(wheel_count::<1>(), 4);
    assert_eq!(BRAKING_DISTANCE_TABLE_SIZE, 6);

    for row in braking_distance_table::<1>() {
        // Access row.velocity, row.friction_coefficient, row.braking_distance
        println!("v={}, μ={}, d={}", row.velocity, row.friction_coefficient, row.braking_distance);
    }
}
```

### Define Requirements

Requirements are written in Markdown with a specific structure (that is validated), for instance

Let's say we have a requirement file `requirements/velocity_requirements.sysreq.md`:

```markdown
# Velocity Requirements

## REQ-VEL-001

SIL: ASIL-D | Sec: false | Version: 2

**Maximum Vehicle Velocity**

The vehicle SHALL NOT exceed the maximum design velocity defined by
[@maximum_vehicle_velocity](examples/vehicle_params.yaml#maximum_vehicle_velocity) (55.0 m/s)
under any operating conditions.

### Rationale

This requirement is derived from [ISO 26262:2018, Part 3, Section 7](https://www.iso.org/standard/68383.html)
safety analysis for ASIL-D classification. The maximum velocity is constrained by:

- Mechanical stress limits on drivetrain components
- Tire rating specifications
- Braking system performance envelope (see [REQ-BRK-001](examples/requirements/braking_requirements.sysreq.md?version=1#REQ-BRK-001))
- Control system response time requirements

### Verification

- Static analysis of control algorithms
- Hardware-in-the-loop testing with velocity limiting scenarios
- Vehicle dynamics simulation at boundary conditions
- Track testing with instrumentation (see [vehicle_params_test](//examples:vehicle_params_test))
- Potentially link to a test plan

### Changelog

- **Version 2**: Added parent requirement version tracking support
- **Version 1**: Initial maximum velocity requirement definition
```

Note that the important part here is the header 2 (`##`), that includes the ID of the requirement and must be followed by a line containing SIL, Sec, and Version separated by `|` characters.
The header 3 (`###`) sections are free text for now, even though we highly recomment you to use a fixed format for it.
Note that a requirement file can contain multiple of such requirements.

Requirements are collected in Bazel targets as follows

```starlark
load("//fire/starlark:requirements.bzl", "requirement_library")

requirement_library(
  name = "vehicle_requirements",
  srcs = glob(["*.md"]),
  deps = [":vehicle_params"],
)
```

## How Fire Works

- Validate requirement links between requirements
  - Checking existence
  - Checking version (disallow consuming an older version)
  - Checking if the consumption expects the right version
- Validating the parameter files for being well formed
- Validating links between parameters and
  - Requirements
  - Source code

### Table Parameters

Parameters are defined in YAML with the following fields:

- `type` (required): One of:
  - Integer types: `i32`, `i64` (signed), `u32`, `u64` (unsigned)
  - Floating-point types: `f32`, `f64`
  - Other types: `string`, `bool`, `table`
- `value` (required for non-table types): The parameter value
- `description` (required): Human-readable short description
- `unit` (optional): Physical unit for the parameter

## Requirement Format

Requirements use section-based markdown with YAML code blocks. Each requirement is identified by an H2 header (`##`), with a YAML block containing only essential structured data.

### System Requirements (`.sysreq.md`)

System requirements contain only essential structured data in YAML blocks, with all metadata in markdown prose.

**Format:**

- H2 headers (`##`) for requirement IDs
- Text line with 3 fields: `SIL`, `Sec`, `Version`
- Bold text (`**Title**`) for human readable requirement title
- Markdown links for all references (parameters, tests, standards)

**Text Fields:**

- `SIL`: Safety Integrity Level - `ASIL-A/B/C/D`, `SIL-1/2/3/4`, `DAL-A/B/C/D/E`, or `QM`
- `Sec`: Security-related flag - `true` or `false`
- `Version`: Positive integer version number (1, 2, 3, ...)

### Software Component Requirements (`.swreq.md`)

Software requirements are derived from system requirements and follow a similar minimal format.

**Format:**

- Optional frontmatter: `system_function` (path to `.sysarch.md` file)
- H2 headers (`##`) for requirement IDs (e.g., `REQ_BC_CALCULATE_FORCE`)
- Text line with 3 fields: `SIL`, `Sec`, `Version`
- Description starts with "Derived from [PARENT](path?version=N#PARENT)" link
- Markdown links for all references

**Example:**

```markdown
---
system_function: /examples/system_functions/braking_control.sysarch.md
---

# Software Requirements: Brake Controller

## REQ_BC_CALCULATE_FORCE

SIL: ASIL-D | Sec: false | Parent: [REQ-BRK-001](/examples/requirements/braking_requirements.sysreq.md?version=1#REQ-BRK-001)

The brake controller component shall calculate the required brake force...
```

### Markdown References

All cross-references use standard markdown links with repository-relative paths:

- **Parameter Reference**: `[@param_name](/path/to/file.yaml#param_name)`
  - Uses `@` prefix to distinguish from regular links
  - Example: `[@maximum_vehicle_velocity](/examples/vehicle_params.yaml#maximum_vehicle_velocity)`

- **Requirement Reference**: `[REQ-ID](/path/to/file.sysreq.md?version=N#REQ-ID)`
  - Includes `?version=N` query parameter to track parent version
  - Example: `[REQ-VEL-001](/examples/requirements/velocity_requirements.sysreq.md?version=2#REQ-VEL-001)`

- **Test Reference**: `[test_name](//package:target)`
  - Uses Bazel label format
  - Example: `[vehicle_params_test](//examples:vehicle_params_test)`

- **Standard Reference**: `[text](https://url)`
  - Standard markdown links for external standards and specifications
  - Example: `[ISO 26262:2018, Part 3](https://www.iso.org/standard/68383.html)`

### Version Tracking

System requirements track their own versions in text line. Software requirements track parent versions in markdown links.

**Detecting Stale Requirements:**

When a parent requirement version changes (e.g., REQ-VEL-001 v2 → v3), any child requirement still referencing `?version=2` is flagged as potentially needing review.

**Why This Format:**

- Minimal structured data (only fields we actually parse and validate)
- All metadata in markdown prose (title, rationale, changelog, etc.)
- Single source of truth for references (markdown links, not duplicated in YAML)
- Clean, readable format that renders well in GitHub/GitLab
- Version tracking via query parameters in links

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

- `traceability`: Full traceability matrix with Requirements → Parameters, Requirements → Requirements (with versions), Requirements → Tests, Requirements → Standards
- `coverage`: Metrics showing percentage of requirements with parameter references, linked tests, and standard references
- `change_impact`: Identifies requirements with stale parent version references
- `compliance`: Compliance report for a specific standard
  - Attributes: `standard` (required, e.g., "ISO 26262", "IEC 61508"), `critical_type` (optional, e.g., "safety", "security")
  - Shows breakdown by requirement type, status distribution, and compliance gaps
  - Highlights critical requirement type if specified

**Note**: "Linked Tests" refers to requirements with test references in frontmatter, not verified test execution.

## Contributing

1. PRs are welcome, even though we are at a very early stage
2. Write tests for your features, both good path and bad path
3. Use `pre-commit.com` and adhere to the checks
4. Provide integration tests where appropriate
