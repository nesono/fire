# Fire - Requirements Management System for Bazel

[![CI](https://github.com/nesono/fire/workflows/CI/badge.svg)](https://github.com/nesono/fire/actions)

Fire is a Bazel module for managing safety-critical system requirements, parameters, and their relationships through Bazel's dependency graph.

**Pure Starlark implementation** - no runtime dependencies, validation at load time, type-safe code generation.

## Features

### Parameter System

- **Load-Time Validation**: Parameters validated when BUILD files load
- **Type System**: Support for `float`, `integer`, `string`, `boolean`, and `table` types
- **Units**: Associate physical units with parameters
- **Tables**: Define multi-column tabular data with typed columns
- **Bazel Integration**: Native Starlark rules for seamless integration
- **No Dependencies**: Zero runtime dependencies

### Requirements Management

- **Markdown Requirements**: Requirements documents with YAML frontmatter
- **Requirement Validation**: Enforce structure, types, and mandatory fields at build time
- **Requirement Metadata**: ID, title, type, status, priority, owner, tags
- **Template System**: Predefined requirement types (functional, safety, interface, etc.)
- **Pure Starlark Validation**: All validation logic in Starlark (testable and reusable)

### Cross-References & Traceability

- **Cross-References**: Link requirements to parameters, other requirements, tests, and standards
- **Repository-Relative Paths**: Explicit paths that work across the repository
- **Parameter References**: `[@parameter_name](path/to/file.bzl#parameter_name)` syntax
- **Requirement References**: `[REQ-ID](path/to/REQ-ID.md)` with mandatory version tracking
- **Test References**: `[test_name](//package:target)` syntax (Bazel labels)
- **Reference Validation**: Format validation, existence checking, and link text matching
- **Bi-directional Validation**: Body markdown references must match frontmatter declarations
- **Lexicographic Sorting**: References sorted alphabetically for consistency
- **Traceability Matrix**: Generate matrices showing requirement relationships
- **Coverage Reports**: Track which requirements have parameter references, linked tests, and standard references

### Version Tracking & Change Management

- **Simple Integer Versioning**: Requirements track version with positive integers (1, 2, 3, ...)
- **Optional Changelog**: Track version changes with integer + description
- **Parent Version Tracking**: Derived requirements must track parent requirement version
- **Stale Requirement Detection**: Immediately identify when parent requirement changes
- **Mandatory Version References**: All requirement references must include version
- **Git for Full History**: Complete change history in Git (changelog just summarizes versions)

### Multi-Language Code Generation

- **C++ Generation**: `constexpr` headers with strong typing
- **Python Generation**: Dataclasses with type hints and frozen immutability
- **Java Generation**: Records with immutable data structures
- **Go Generation**: Constants and structs with type safety
- **Auto-derived Namespaces**: Namespaces automatically derived from Bazel package paths
- **Java Package Prefix**: Optional package prefix for Java reverse-domain naming
- **Source Label Traceability**: All generated files include Bazel source labels
- **Unified Validation**: Single parameter source validated for all target languages

### Reporting & Compliance

- **Compliance Reports**: Standard-agnostic reports (ISO 26262, IEC 61508, DO-178C, etc.)
- **Critical Type Highlighting**: Configurable highlighting for safety, security, regulatory requirements
- **Coverage Reports**: Linked tests and standard references for each requirement
- **Change Impact Analysis**: Identifies requirements with stale parent version references
- **Requirements Not Yet Verified**: Table showing all non-verified requirements
- **Compliance Gap Analysis**: Critical requirements without tests or standards

### Testing

- **93 Unit Tests**: Comprehensive Starlark unit tests using Skylib's unittest framework
- **Validation Tests**: Tests for parameters, requirements, references, versions, and markdown parsing
- **Code Generation Tests**: Test examples in all supported languages (C++, Python, Java, Go)
- **Traceability Tests**: Verify matrix generation and reporting functionality

## Quick Start

### 1. Define Parameters

Parameters are defined in Starlark (either inline in BUILD files or in separate .bzl files):

**vehicle_params.bzl**:

```python
"""Vehicle parameter definitions."""

VEHICLE_PARAMS = [
    {
        "name": "maximum_vehicle_velocity",
        "type": "float",
        "unit": "m/s",
        "value": 55.0,
        "description": "Maximum design velocity for the vehicle",
    },
    {
        "name": "wheel_count",
        "type": "integer",
        "value": 4,
        "description": "Number of wheels on the vehicle",
    },
    {
        "name": "braking_distance_table",
        "type": "table",
        "description": "Braking distances under various conditions",
        "columns": [
            {"name": "velocity", "type": "float", "unit": "m/s"},
            {"name": "friction_coefficient", "type": "float", "unit": "dimensionless"},
            {"name": "braking_distance", "type": "float", "unit": "m"},
        ],
        "rows": [
            [10.0, 0.7, 7.1],
            [20.0, 0.7, 28.6],
            [30.0, 0.7, 64.3],
        ],
    },
]
```

### 2. Create Bazel Targets

In your `BUILD.bazel` file (e.g., in `vehicle/dynamics/`):

```python
load("@fire//fire/starlark:parameters.bzl", "parameter_library", "cc_parameter_library")
load("@rules_cc//cc:defs.bzl", "cc_test")
load(":vehicle_params.bzl", "VEHICLE_PARAMS")

# Validate parameters and generate header
# Namespace auto-derived from package path: vehicle/dynamics -> vehicle::dynamics
parameter_library(
    name = "vehicle_params_header",
    parameters = VEHICLE_PARAMS,
)

# Or explicitly specify namespace if needed
# parameter_library(
#     name = "vehicle_params_header",
#     namespace = "vehicle.dynamics",
#     parameters = VEHICLE_PARAMS,
# )

# Create C++ library from parameters
cc_parameter_library(
    name = "vehicle_params_cc",
    parameter_library = ":vehicle_params_header",
)

# Use generated parameters in C++ code
cc_test(
    name = "dynamics_test",
    srcs = ["dynamics_test.cc"],
    deps = [":vehicle_params_cc"],
)
```

### 3. Use in C++ Code

The generated header provides type-safe access to parameters:

```cpp
#include "vehicle_params_header.h"

int main() {
    using namespace vehicle::dynamics;

    // Access simple parameters
    double max_vel = maximum_vehicle_velocity;  // 55.0
    int wheels = wheel_count;                   // 4

    // Access table data
    for (size_t i = 0; i < braking_distance_table_size; ++i) {
        double velocity = braking_distance_table[i].velocity;
        double friction = braking_distance_table[i].friction_coefficient;
        double distance = braking_distance_table[i].braking_distance;
        // ... use the values
    }

    return 0;
}
```

### 4. Multi-Language Support

Generate parameters for Python, Java, and Go tests (in `vehicle/dynamics/`):

```python
load(
    "//fire/starlark:parameters.bzl",
    "python_parameter_library",
    "java_parameter_library",
    "go_parameter_library",
)

# Generate Python parameters
# Namespace auto-derived: vehicle/dynamics -> vehicle.dynamics
python_parameter_library(
    name = "vehicle_params_py",
    parameters = VEHICLE_PARAMS,
)

# Generate Java parameters with package prefix
# Namespace auto-derived: vehicle/dynamics -> com.example.vehicle.dynamics
java_parameter_library(
    name = "vehicle_params_java",
    package_prefix = "com.example",  # Optional prefix for Java packages
    class_name = "VehicleParams",
    parameters = VEHICLE_PARAMS,
)

# Generate Go parameters
# Package name auto-derived: vehicle/dynamics -> package dynamics
go_parameter_library(
    name = "vehicle_params_go",
    parameters = VEHICLE_PARAMS,
)
```

**Python usage:**

```python
from vehicle_params_py import (
    MAXIMUM_VEHICLE_VELOCITY,
    WHEEL_COUNT,
    BRAKING_DISTANCE_TABLE_DATA,
    BrakingDistanceTableRow,
)

def test_parameters():
    assert MAXIMUM_VEHICLE_VELOCITY == 55.0
    assert WHEEL_COUNT == 4

    for row in BRAKING_DISTANCE_TABLE_DATA:
        print(f"v={row.velocity}, μ={row.friction_coefficient}, d={row.braking_distance}")
```

**Java usage:**

```java
import com.example.vehicle.dynamics.VehicleParams;

public class DynamicsTest {
    @Test
    public void testParameters() {
        assertEquals(55.0, VehicleParams.MAXIMUM_VEHICLE_VELOCITY);
        assertEquals(4, VehicleParams.WHEEL_COUNT);

        for (var row : VehicleParams.BRAKING_DISTANCE_TABLE) {
            // Access row.velocity(), row.frictionCoefficient(), row.brakingDistance()
        }
    }
}
```

**Go usage:**

```go
import dynamics "yourproject/vehicle/dynamics"

func TestParameters(t *testing.T) {
    if dynamics.MaximumVehicleVelocity != 55.0 {
        t.Error("Unexpected velocity")
    }

    for _, row := range dynamics.BrakingDistanceTable {
        // Access row.Velocity, row.FrictionCoefficient, row.BrakingDistance
    }
}
```

### 5. Define Requirements

Requirements are written in Markdown with YAML frontmatter:

**requirements/REQ-VEL-001.md**:

```markdown
---
id: REQ-VEL-001
title: Maximum Vehicle Velocity
type: safety
status: approved
priority: critical
owner: safety-team
tags: [velocity, safety, ASIL-D]
references:
  parameters:
    - examples/vehicle_params.bzl#maximum_vehicle_velocity
  requirements:
    - path: examples/requirements/REQ-BRK-001.md
      version: 1
  standards:
    - ISO 26262:2018, Part 3, Section 7
  tests:
    - //examples:vehicle_params_test
---

# REQ-VEL-001: Maximum Vehicle Velocity

## Description

The vehicle SHALL NOT exceed the maximum design velocity defined by
[@maximum_vehicle_velocity](examples/vehicle_params.bzl#maximum_vehicle_velocity) (55.0 m/s)
under any operating conditions.

## Rationale

This requirement is derived from [ISO 26262:2018, Part 3, Section 7](https://www.iso.org/standard/68383.html)
safety analysis for ASIL-D classification. The requirement relates to braking
performance (see [REQ-BRK-001](examples/requirements/REQ-BRK-001.md)).

## Verification

Testing is performed according to [vehicle_params_test](//examples:vehicle_params_test).
```

### 5. Validate Requirements

In your `BUILD.bazel`:

```python
load("@fire//fire/starlark:requirements.bzl", "requirement_library")

requirement_library(
    name = "safety_requirements",
    srcs = glob(["requirements/*.md"]),
)
```

## Parameter Format

### Namespace

Namespaces are **auto-derived from the Bazel package path** for consistency with your build structure:

```python
# In package vehicle/dynamics/braking/BUILD.bazel
parameter_library(
    name = "my_params_header",
    parameters = [...],  # Namespace auto-derived as vehicle::dynamics::braking
)
```

This generates:

```cpp
namespace vehicle {
namespace dynamics {
namespace braking {
    // parameters here
}
}
}
```

You can also **explicitly specify** a namespace if needed:

```python
parameter_library(
    name = "my_params_header",
    namespace = "custom.namespace",
    parameters = [...],
)
```

### Simple Parameters

Parameters are defined as dictionaries with the following fields:

- `name` (required): Identifier for the parameter
- `type` (required): One of `float`, `integer`, `string`, `boolean`, `table`
- `value` (required for non-table types): The parameter value
- `description` (required): Human-readable description
- `unit` (optional): Physical unit for the parameter

Example:

```python
{
    "name": "max_temperature",
    "type": "float",
    "unit": "celsius",
    "value": 85.0,
    "description": "Maximum operating temperature",
}
```

### Table Parameters

Tables define multi-column tabular data:

```python
{
    "name": "gear_ratios",
    "type": "table",
    "description": "Gear ratios by gear number",
    "columns": [
        {"name": "gear", "type": "integer"},
        {"name": "ratio", "type": "float"},
        {"name": "max_speed", "type": "float", "unit": "km/h"},
    ],
    "rows": [
        [1, 3.5, 40.0],
        [2, 2.1, 70.0],
        [3, 1.4, 110.0],
        [4, 1.0, 160.0],
    ],
}
```

Generated C++ code:

```cpp
struct GearRatiosRow {
    int gear;
    double ratio;
    double max_speed;  // Unit: km/h
};

constexpr GearRatiosRow gear_ratios[] = {
    {1, 3.5, 40.0},
    {2, 2.1, 70.0},
    {3, 1.4, 110.0},
    {4, 1.0, 160.0},
};

constexpr size_t gear_ratios_size = 4;
```

## Requirement Format

Requirements are Markdown documents with YAML frontmatter.

### Required Fields

- `id`: Unique identifier (letters, numbers, hyphens, underscores)
- `title`: Human-readable title
- `type`: One of `functional`, `non-functional`, `safety`, `interface`, `constraint`, `performance`
- `status`: One of `draft`, `proposed`, `approved`, `implemented`, `verified`, `deprecated`

### Optional Fields

- `priority`: One of `low`, `medium`, `high`, `critical`
- `owner`: Team or individual responsible
- `tags`: List of tags for categorization
- `version`: Simple integer version number (1, 2, 3, ...)
- `changelog`: List of version changes with `{version, description}` (optional)
- `references`: Cross-references to other entities
  - `parameters`: List of parameter names
  - `requirements`: List of requirement IDs (string) or dicts with `{id, version}`
  - `tests`: List of Bazel test targets
  - `standards`: List of standard references

### Markdown References

Requirements can use markdown links to reference parameters, other requirements, tests, and standards.
These links render properly in web UIs (GitHub, GitLab, etc.) and are validated against frontmatter.

**Reference Syntax:**

- **Parameter Reference**: `[@parameter_name](repo/relative/path/file.bzl#parameter_name)`
  - Uses `@` prefix to distinguish from regular links
  - Uses repository-relative path for clickable links
  - Example: `[@maximum_vehicle_velocity](examples/vehicle_params.bzl#maximum_vehicle_velocity)`

- **Requirement Reference**: `[REQ-ID](repo/relative/path/REQ-ID.md)`
  - Uses repository-relative path for clickable links in GitHub/GitLab
  - Example: `[REQ-BRK-001](examples/requirements/REQ-BRK-001.md)`

- **Test Reference**: `[test_name](//package:target)`
  - Uses Bazel label format for test references
  - Example: `[vehicle_params_test](//examples:vehicle_params_test)`

- **External Reference**: `[text](https://url)`
  - Standard markdown links for standards, specifications, etc.

**Validation**: All markdown references in the body must be declared in the frontmatter `references` section using the same
repository-relative format. Bi-directional validation ensures frontmatter and body stay in sync. References must be sorted
alphabetically within each section.

### Parent Requirement Version Tracking

When a requirement is derived from a parent requirement, track the parent's version to detect when the parent changes.

**Simple Integer Versioning**:

```yaml
version: 2  # Just increment when requirement changes
```

**Optional Changelog** (no dates needed - Git has those):

```yaml
changelog:
  - version: 2
    description: Added new safety constraint
  - version: 1
    description: Initial requirement definition
```

**Track Parent Versions** (derived requirements):

```yaml
references:
  requirements:
    # Required format (tracks parent version)
    - path: examples/requirements/REQ-VEL-001.md
      version: 2  # This requirement was derived from version 2 of REQ-VEL-001
```

**Detecting Stale Requirements**:

When `REQ-VEL-001` changes to version 3, any child requirement still referencing version 2 is flagged as potentially needing review.

**Why Simple Integers**:

- Easy to understand and maintain
- Git already tracks full history (who, when, why)
- Just need to know "did parent change?"
- No complex versioning rules
- Changelog optional for quick summary

**Example**:

Parent requirement `REQ-VEL-001.md`:

```yaml
id: REQ-VEL-001
version: 2
changelog:
  - version: 2
    description: Added parent requirement version tracking support
  - version: 1
    description: Initial maximum velocity requirement definition
```

Derived requirement `REQ-BRK-001.md`:

```yaml
id: REQ-BRK-001
version: 1
changelog:
  - version: 1
    description: Initial emergency braking requirement, derived from REQ-VEL-001 v2
references:
  requirements:
    - path: examples/requirements/REQ-VEL-001.md
      version: 2  # Tracks which parent version this was derived from
```

If `REQ-VEL-001` changes to version 3, you can immediately identify that `REQ-BRK-001` needs review.

## Reporting & Compliance

Fire provides built-in reporting functions in `traceability.bzl` to generate compliance and analysis reports.

### Traceability Matrix

Generate comprehensive traceability matrices with version information:

```python
load("@fire//fire/starlark:traceability.bzl", "traceability")

# In your Starlark code
requirements_data = [
    ("REQ-VEL-001", frontmatter_dict),
    ("REQ-BRK-001", frontmatter_dict),
]

matrix = traceability.generate_matrix_markdown(requirements_data)
# Generates markdown with Requirements → Parameters, Requirements → Requirements (with versions),
# Requirements → Tests, and Requirements → Standards sections
```

### Change Impact Analysis

Identify requirements that need review due to parent changes:

```python
impact_report = traceability.generate_change_impact_markdown(requirements_data)
# Shows which requirements have stale parent version references
# Example output:
# ⚠️ Requirements with Stale Parent References
# REQ-BRK-001 (v1): Tracking REQ-VEL-001 v2, but current version is v3
```

### Compliance Reports

Generate compliance reports for safety standards (ISO 26262, IEC 61508, etc.):

```python
# Standard-agnostic compliance report
compliance_report = traceability.generate_compliance_markdown(requirements_data, "ISO 26262")

# With critical requirement type highlighting
compliance_report = traceability.generate_compliance_markdown(
    requirements_data,
    "ISO 26262",
    critical_type="safety"  # or "security", "regulatory", etc.
)
# Includes:
# - Summary statistics (breakdown by requirement type, standard references, linked tests)
# - Requirements by status (draft, approved, verified, etc.)
# - Critical type requirements detail (if specified)
# - Compliance gaps (critical reqs without linked tests or standard references)
# - Unverified requirements
```

**Note**: Reports show "Linked Tests" not "Test Coverage" - this refers to requirements with test references in their frontmatter, not verified test execution.

### Coverage Dashboard

Generate coverage reports showing traceability completeness:

```python
coverage_report = traceability.generate_coverage_markdown(requirements_data)
# Shows percentage of requirements with:
# - Parameter coverage
# - Test coverage
# - Standard references
# Lists requirements missing coverage in each category
```

**Available Functions**:

- `traceability.generate_matrix_markdown(requirements_data)` - Full traceability matrix
- `traceability.generate_change_impact_markdown(requirements_data)` - Stale requirement detection
- `traceability.generate_compliance_markdown(requirements_data, standard_name)` - Compliance report
- `traceability.generate_coverage_markdown(requirements_data)` - Coverage metrics

All reports are generated in Markdown format for easy viewing in GitHub/GitLab and integration into documentation pipelines.

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

### Example

```markdown
---
id: REQ-BRK-001
title: Emergency Braking Distance
type: functional
status: approved
priority: high
owner: dynamics-team
tags: [braking, safety, performance]
references:
  parameters:
    - examples/vehicle_params.bzl#braking_distance_table
  requirements:
    - path: examples/requirements/REQ-VEL-001.md
      version: 2
  standards:
    - UN ECE R13-H
  tests:
    - //examples:vehicle_params_test
---

# REQ-BRK-001: Emergency Braking Distance

## Description

The vehicle SHALL achieve emergency braking according to
[@braking_distance_table](examples/vehicle_params.bzl#braking_distance_table).
This requirement relates to [REQ-VEL-001](examples/requirements/REQ-VEL-001.md).

## Verification

Testing performed by [vehicle_params_test](//examples:vehicle_params_test).
Compliance verified against [UN ECE R13-H](https://unece.org/r13h).
```

## Bazel Rules

### `parameter_library()`

Validates parameters and generates a C++ header file.

**Attributes:**

- `name`: Name of the target (generates `<name>.h`)
- `namespace`: C++ namespace for parameters (optional, auto-derived from package path if not provided)
- `parameters`: List of parameter dictionaries (required)
- `schema_version`: Schema version (optional, defaults to "1.0")

**Example:**

```python
# Namespace auto-derived from package path
parameter_library(
    name = "my_params_header",
    parameters = [
        {"name": "value1", "type": "float", "value": 1.0, "description": "..."},
    ],
)

# Or explicitly specify namespace
parameter_library(
    name = "my_params_header",
    namespace = "my.namespace",
    parameters = [
        {"name": "value1", "type": "float", "value": 1.0, "description": "..."},
    ],
)
```

### `cc_parameter_library()`

Creates a `cc_library` from a parameter library for easy inclusion in C++ targets.

**Attributes:**

- `name`: Name of the `cc_library`
- `parameter_library`: Label of the `parameter_library` target (the generated `.h` file)
- Additional `cc_library` attributes supported

**Example:**

```python
cc_parameter_library(
    name = "my_params_cc",
    parameter_library = ":my_params_header",
)
```

### `python_parameter_library()`

Generates a Python module with parameters.

**Attributes:**

- `name`: Name of the generated module (creates `name.py`)
- `namespace`: Python module namespace (optional, auto-derived from package path if not provided)
- `parameters`: List of parameter dictionaries
- `schema_version`: Schema version (optional, defaults to "1.0")

**Example:**

```python
# Namespace auto-derived from package path
python_parameter_library(
    name = "vehicle_params_py",
    parameters = VEHICLE_PARAMS,
)

# Or explicitly specify namespace
python_parameter_library(
    name = "vehicle_params_py",
    namespace = "vehicle.dynamics",
    parameters = VEHICLE_PARAMS,
)
```

### `java_parameter_library()`

Generates a Java class with parameters.

**Attributes:**

- `name`: Name of the generated class file
- `namespace`: Java package namespace (optional, auto-derived from package path if not provided)
- `package_prefix`: Optional prefix for Java packages (e.g., "com.example")
- `class_name`: Name of the generated class (optional, defaults to "Parameters")
- `parameters`: List of parameter dictionaries
- `schema_version`: Schema version (optional, defaults to "1.0")

**Example:**

```python
# Namespace auto-derived from package path with prefix
java_parameter_library(
    name = "vehicle_params_java",
    package_prefix = "com.example",  # Results in: com.example.<package_path>
    class_name = "VehicleParams",
    parameters = VEHICLE_PARAMS,
)

# Or explicitly specify full namespace
java_parameter_library(
    name = "vehicle_params_java",
    namespace = "com.example.vehicle.dynamics",
    class_name = "VehicleParams",
    parameters = VEHICLE_PARAMS,
)
```

### `go_parameter_library()`

Generates a Go package with parameters.

**Attributes:**

- `name`: Name of the generated Go file (creates `name.go`)
- `namespace`: Go package path (optional, auto-derived from package path if not provided)
- `package_name`: Go package name (optional, auto-derived from last component of namespace if not provided)
- `parameters`: List of parameter dictionaries
- `schema_version`: Schema version (optional, defaults to "1.0")

**Example:**

```python
# Package name auto-derived from package path
go_parameter_library(
    name = "vehicle_params_go",
    parameters = VEHICLE_PARAMS,  # vehicle/dynamics -> package dynamics
)

# Or explicitly specify package name
go_parameter_library(
    name = "vehicle_params_go",
    package_name = "dynamics",
    parameters = VEHICLE_PARAMS,
)
```

### `requirement_library()`

Creates a filegroup containing requirement documents.

**Attributes:**

- `name`: Name of the target
- `srcs`: List of requirement Markdown files

**Example:**

```python
requirement_library(
    name = "safety_requirements",
    srcs = glob(["requirements/safety/*.md"]),
)
```

## Project Structure

```text
fire/
├── MODULE.bazel              # Bazel module definition
├── BUILD.bazel               # Root build file
├── README.md                 # This file
├── fire/
│   └── starlark/             # Starlark implementation
│       ├── validator.bzl     # Parameter validation logic
│       ├── validator_test.bzl # Validator unit tests
│       ├── cpp_generator.bzl # C++ code generation
│       ├── python_generator.bzl # Python code generation
│       ├── java_generator.bzl # Java code generation
│       ├── go_generator.bzl  # Go code generation
│       ├── cpp_generator_test.bzl # Generator unit tests
│       ├── parameters.bzl    # Multi-language parameter library rules
│       ├── requirement_validator.bzl # Requirement validation logic
│       ├── requirement_validator_test.bzl # Requirement validator tests
│       ├── reference_validator.bzl # Cross-reference validation
│       ├── reference_validator_test.bzl # Reference validator tests
│       ├── version_validator.bzl # Versioning and change management validation
│       ├── version_validator_test.bzl # Version validator tests (17 tests)
│       ├── markdown_parser.bzl # Markdown link parsing and validation
│       ├── markdown_parser_test.bzl # Markdown parser tests (15 tests)
│       ├── traceability.bzl  # Traceability, compliance, and reporting
│       ├── traceability_test.bzl # Traceability tests (10 tests)
│       ├── requirements.bzl  # requirement_library rule
│       └── BUILD.bazel
└── examples/                 # Example usage
    ├── vehicle_params.bzl    # Example parameter definitions
    ├── vehicle_params_test.cc  # Integration test
    ├── requirements/         # Example requirements
    │   ├── REQ-VEL-001.md    # (parent requirement with version)
    │   ├── REQ-BRK-001.md    # (derived requirement tracking parent version)
    │   └── REQ-WHEEL-001.md  # (with cross-references)
    └── BUILD.bazel
```

## Development

### Pre-commit Hooks

Fire uses [pre-commit](https://pre-commit.com) to ensure code quality. To set up:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# Optionally, run on all files
pre-commit run --all-files
```

Pre-commit hooks include:

- **Buildifier**: Bazel and Starlark file formatting
- **Markdownlint**: Markdown linting with auto-fix
- **General**: Trailing whitespace, EOF fixers, file checks

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Testing

Run all tests:

```bash
bazel test //...
```

Run specific test suites:

```bash
# Starlark unit tests
bazel test //fire/starlark:validator_test
bazel test //fire/starlark:cpp_generator_test
bazel test //fire/starlark:requirement_validator_test
bazel test //fire/starlark:reference_validator_test
bazel test //fire/starlark:version_validator_test
bazel test //fire/starlark:markdown_parser_test
bazel test //fire/starlark:traceability_test

# Integration tests
bazel test //examples:vehicle_params_test
```

## Validation Rules

### Parameter Validation

1. **Required Fields**: `namespace` and `parameters` in `parameter_library()`
2. **Namespace Format**: Must be dot-separated identifiers (e.g., `vehicle.dynamics`)
3. **Parameter Types**: Only `float`, `integer`, `string`, `boolean`, `table` are valid
4. **Type Checking**: Values must match their declared types
5. **Table Consistency**: All rows must have the same number of columns as defined
6. **Unique Names**: Parameter names must be unique
7. **Required Parameter Fields**: Each parameter needs `name`, `type`, `description`

### Requirement Validation

1. **Required Fields**: `id`, `title`, `type`, `status` in frontmatter
2. **ID Format**: Letters, numbers, hyphens, underscores; must start with letter/underscore
3. **Type Values**: `functional`, `non-functional`, `safety`, `interface`, `constraint`, `performance`
4. **Status Values**: `draft`, `proposed`, `approved`, `implemented`, `verified`, `deprecated`
5. **Priority Values** (optional): `low`, `medium`, `high`, `critical`
6. **Body Content**: Must be at least 10 characters
7. **Frontmatter**: Must be valid YAML between `---` markers

### Cross-Reference Validation

1. **Parameter References**: Valid parameter identifiers (letters, numbers, underscores)
2. **Requirement References**: Valid requirement IDs
3. **Test References**: Valid Bazel labels (start with `//` or `:`)
4. **Standard References**: Minimum 3 characters
5. **Reference Types**: Only `parameters`, `requirements`, `tests`, `standards` allowed
6. **Reference Format**: Must be lists of strings

### Markdown Reference Validation

1. **Parameter Links**: `[@parameter_name](repo/relative/path/file.bzl#parameter_name)` syntax with repository-relative path
2. **Requirement Links**: `[REQ-ID](repo/relative/path/REQ-ID.md)` syntax with repository-relative path
3. **Test Links**: `[test_name](//package:target)` syntax using Bazel labels
4. **Body-Frontmatter Match**: Bi-directional validation ensures all body references are declared in frontmatter, and all frontmatter references are used in body
5. **Frontmatter Format**: Frontmatter references use the same repository-relative paths as body references
6. **Link Text Match**: Link text must match the actual reference name (no typos allowed)
7. **Lexicographic Sorting**: References within each frontmatter section (parameters, requirements, tests, standards) must be sorted alphabetically
8. **Validation Timing**: Checked at build time during requirement validation

### Version Tracking Validation

1. **Integer Version**: Must be positive integer (>= 1)
2. **Changelog Format**: List of `{version, description}` in descending order (newest first)
3. **Version Consistency**: If both `version` and `changelog` present, version must match latest changelog entry
4. **Requirement Reference Format**: MUST use dict format with both `path` and `version` keys (e.g., `{path: "examples/requirements/REQ-VEL-001.md", version: 2}`)
5. **Version Field**: Optional for the requirement itself - only needed if tracking changes or using changelog
6. **Changelog Field**: Optional - use for quick summary of changes
7. **Parent Version**: When referencing parent requirements, version must be positive integer
8. **Backward Compatibility**: All versioning and changelog fields for the requirement itself are optional, but requirement references MUST always include version

## Design Philosophy

Fire follows these principles:

- **Test-Driven Development**: Every implementation file has a corresponding test file
- **Type Safety**: Generate compile-time checked code where possible
- **Bazel Integration**: Leverage Bazel's dependency graph for traceability
- **Validation First**: Catch errors at build time, not runtime
- **Clear Separation**: Implementation and test files colocated for clarity

## Future Work

- IDE integration for enhanced developer experience
- Additional language targets (Rust, TypeScript, etc.)
- Performance optimization for large requirement sets
- Interactive compliance dashboards

## Contributing

This project follows Test-Driven Development practices:

1. Write tests first:
   - Starlark unit tests in `*_test.bzl` files using Skylib's `unittest`
   - C++ integration tests in `*_test.cc` files
2. Implement functionality to make tests pass
3. Refactor while keeping tests green
4. Ensure Buildifier passes on all Starlark code

## License

TBD

## Contact

TBD
