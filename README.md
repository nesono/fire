# Fire - Requirements Management System for Bazel

[![CI](https://github.com/nesono/fire/workflows/CI/badge.svg)](https://github.com/nesono/fire/actions)

Fire is a Bazel module for managing safety-critical system requirements, parameters, and their relationships through Bazel's dependency graph.

**Pure Starlark implementation** - no runtime dependencies, validation at load time, type-safe code generation.

## Status

- **Phase 1: Parameter System** ✓ Complete
- **Phase 2: Requirements & Templates** ✓ Complete
- **Phase 3: Cross-References & Traceability** ✓ Complete

## Features

### Phase 1: Parameter System

- **Load-Time Validation**: Parameters validated when BUILD files load
- **Type System**: Support for `float`, `integer`, `string`, `boolean`, and `table` types
- **Units**: Associate physical units with parameters
- **Tables**: Define multi-column tabular data with typed columns
- **C++ Code Generation**: Generate type-safe `constexpr` C++ headers from parameters
- **Bazel Integration**: Native Starlark rules for seamless integration
- **Unit Tests**: Comprehensive Starlark unit tests using Skylib's unittest framework

### Phase 2: Requirements & Templates

- **Markdown Requirements**: Requirements documents with YAML frontmatter
- **Requirement Validation**: Enforce structure, types, and mandatory fields
- **Requirement Metadata**: ID, title, type, status, priority, owner, tags
- **Template System**: Predefined requirement types (functional, safety, interface, etc.)
- **Unit Tests**: Comprehensive validation tests for requirement documents

### Phase 3: Cross-References & Traceability

- **Cross-References**: Link requirements to parameters, other requirements, tests, and standards
- **Reference Validation**: Validate reference formats and integrity
- **Markdown Link Support**: Use proper markdown links that render in web UIs
- **Parameter References**: `[@parameter_name](path/file.bzl#parameter_name)` syntax
- **Requirement References**: `[REQ-ID](REQ-ID.md)` syntax
- **Test References**: `[test_name](BUILD.bazel#test_name)` syntax
- **Bi-directional Validation**: Body markdown references must match frontmatter declarations
- **Traceability Matrix**: Generate matrices showing requirement relationships
- **Coverage Reports**: Track which requirements have parameter/test coverage
- **Unit Tests**: Comprehensive tests for reference validation and markdown parsing

### General

- **No Dependencies**: Zero runtime dependencies

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

In your `BUILD.bazel` file:

```python
load("@fire//fire/starlark:parameters.bzl", "parameter_library", "cc_parameter_library")
load("@rules_cc//cc:defs.bzl", "cc_test")
load(":vehicle_params.bzl", "VEHICLE_PARAMS")

# Validate parameters and generate header
parameter_library(
    name = "vehicle_params_header",
    namespace = "vehicle.dynamics",
    parameters = VEHICLE_PARAMS,
)

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

### 4. Define Requirements

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

The vehicle SHALL NOT exceed the maximum design velocity defined by
[@maximum_vehicle_velocity](../vehicle_params.bzl#maximum_vehicle_velocity) (55.0 m/s)
under any operating conditions.

## Rationale

This requirement is derived from [ISO 26262:2018, Part 3, Section 7](https://www.iso.org/standard/68383.html)
safety analysis for ASIL-D classification. The requirement relates to braking
performance (see [REQ-BRK-001](REQ-BRK-001.md)).

## Verification

Testing is performed according to [vehicle_params_test](../BUILD.bazel#vehicle_params_test).
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

When defining a `parameter_library`, specify the C++ namespace (supports nested namespaces):

```python
parameter_library(
    name = "my_params_header",
    namespace = "vehicle.dynamics.braking",
    parameters = [...],
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
- `references`: Cross-references to other entities
  - `parameters`: List of parameter names
  - `requirements`: List of requirement IDs
  - `tests`: List of Bazel test targets
  - `standards`: List of standard references

### Markdown References

Requirements can use markdown links to reference parameters, other requirements, tests, and standards.
These links render properly in web UIs (GitHub, GitLab, etc.) and are validated against frontmatter.

**Reference Syntax:**

- **Parameter Reference**: `[@parameter_name](path/file.bzl#parameter_name)`
  - Uses `@` prefix to distinguish from regular links
  - Links to the parameter definition file

- **Requirement Reference**: `[REQ-ID](REQ-ID.md)`
  - Links to the requirement markdown file

- **Test Reference**: `[test_name](BUILD.bazel#test_name)`
  - Links to the Bazel BUILD file with anchor to test target

- **External Reference**: `[text](https://url)`
  - Standard markdown links for standards, specifications, etc.

**Validation**: All markdown references in the body must be declared in the frontmatter `references` section.

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
    - braking_distance_table
  requirements:
    - REQ-VEL-001
  standards:
    - UN ECE R13-H
  tests:
    - //examples:vehicle_params_test
---

# REQ-BRK-001: Emergency Braking Distance

## Description

The vehicle SHALL achieve emergency braking according to
[@braking_distance_table](../vehicle_params.bzl#braking_distance_table).
This requirement relates to [REQ-VEL-001](REQ-VEL-001.md).

## Verification

Testing performed by [vehicle_params_test](../BUILD.bazel#vehicle_params_test).
Compliance verified against [UN ECE R13-H](https://unece.org/r13h).
```

## Bazel Rules

### `parameter_library()`

Validates parameters and generates a C++ header file.

**Attributes:**

- `name`: Name of the target (generates `<name>.h`)
- `namespace`: C++ namespace for parameters (required)
- `parameters`: List of parameter dictionaries (required)
- `schema_version`: Schema version (optional, defaults to "1.0")

**Example:**

```python
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
│       ├── cpp_generator_test.bzl # Generator unit tests
│       ├── parameters.bzl    # parameter_library and cc_parameter_library rules
│       ├── requirement_validator.bzl # Requirement validation logic
│       ├── requirement_validator_test.bzl # Requirement validator tests
│       ├── reference_validator.bzl # Cross-reference validation
│       ├── reference_validator_test.bzl # Reference validator tests
│       ├── markdown_parser.bzl # Markdown link parsing and validation
│       ├── markdown_parser_test.bzl # Markdown parser tests
│       ├── traceability.bzl  # Traceability matrix and coverage generation
│       ├── requirements.bzl  # requirement_library rule
│       └── BUILD.bazel
└── examples/                 # Example usage
    ├── vehicle_params.bzl    # Example parameter definitions
    ├── vehicle_params_test.cc  # Integration test
    ├── requirements/         # Example requirements
    │   ├── REQ-VEL-001.md    # (with cross-references)
    │   ├── REQ-BRK-001.md    # (with cross-references)
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
bazel test //fire/starlark:markdown_parser_test

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

1. **Parameter Links**: `[@parameter_name](path)` syntax with valid parameter name
2. **Requirement Links**: `[REQ-ID](*.md)` syntax with valid requirement ID
3. **Test Links**: `[test_name](BUILD*)` syntax
4. **Body-Frontmatter Match**: All markdown references in body must be declared in frontmatter
5. **Validation Timing**: Checked at build time during requirement validation

## Design Philosophy

Fire follows these principles:

- **Test-Driven Development**: Every implementation file has a corresponding test file
- **Type Safety**: Generate compile-time checked code where possible
- **Bazel Integration**: Leverage Bazel's dependency graph for traceability
- **Validation First**: Catch errors at build time, not runtime
- **Clear Separation**: Implementation and test files colocated for clarity

## Roadmap

### ✅ Phase 1: Foundation & Parameter System (Complete)

- Starlark parameter validation
- C++ code generation
- Bazel rules integration
- Load-time validation
- Comprehensive unit tests

### ✅ Phase 2: Requirements & Templates (Complete)

- Markdown requirement documents with YAML frontmatter
- Requirement validation (structure, types, mandatory fields)
- Requirement metadata (ID, title, type, status, priority, owner, tags)
- Template system with predefined requirement types
- Comprehensive unit tests for requirement validation

### ✅ Phase 3: Cross-References & Traceability (Complete)

- Cross-reference system linking requirements to parameters, requirements, tests, and standards
- Reference validation with type-specific rules
- Traceability matrix generation (Markdown format)
- Coverage report generation
- Bi-directional traceability support
- Comprehensive unit tests for reference validation

### Phase 4: Multi-Language Code Generation (Planned)

- Python parameter libraries
- Additional language support

### Phase 5: Change Management & Review Tracking (Planned)

- Requirement versioning
- Change impact analysis
- Review status tracking

### Phase 6: Reporting & Compliance (Planned)

- Traceability matrices
- Compliance reports
- Multiple export formats

### Phase 7: Advanced Features & Polish (Planned)

- IDE integration
- Pre-commit hooks
- Performance optimization

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
