# Fire - Requirements Management System for Bazel

[![CI](https://github.com/nesono/fire/workflows/CI/badge.svg)](https://github.com/nesono/fire/actions)

Fire is a Bazel module for managing safety-critical system requirements, parameters, and their relationships through Bazel's dependency graph.

**Pure Starlark implementation** - no runtime dependencies, validation at load time, type-safe code generation.

## Status: Phase 1 - Parameter System ✓

Phase 1 is complete and provides parameter management with code generation capabilities.

## Features (Phase 1)

- **Load-Time Validation**: Parameters validated when BUILD files load
- **Type System**: Support for `float`, `integer`, `string`, `boolean`, and `table` types
- **Units**: Associate physical units with parameters
- **Tables**: Define multi-column tabular data with typed columns
- **C++ Code Generation**: Generate type-safe `constexpr` C++ headers from parameters
- **Bazel Integration**: Native Starlark rules for seamless integration
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

## Project Structure

```
fire/
├── MODULE.bazel              # Bazel module definition
├── BUILD.bazel               # Root build file
├── README.md                 # This file
├── fire/
│   └── starlark/             # Starlark implementation
│       ├── validator.bzl     # Parameter validation logic
│       ├── cpp_generator.bzl # C++ code generation
│       ├── parameters.bzl    # parameter_library and cc_parameter_library rules
│       └── BUILD.bazel
└── examples/                 # Example usage
    ├── vehicle_params.bzl    # Example parameter definitions
    ├── vehicle_params_test.cc  # Integration test
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
- **General**: Trailing whitespace, EOF fixers, file checks

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Testing

Run all tests:

```bash
bazel test //...
```

Run example tests:

```bash
bazel test //examples:vehicle_params_test
```

## Validation Rules

The parameter validator enforces:

1. **Required Fields**: `namespace` and `parameters` in `parameter_library()`
2. **Namespace Format**: Must be dot-separated identifiers (e.g., `vehicle.dynamics`)
3. **Parameter Types**: Only `float`, `integer`, `string`, `boolean`, `table` are valid
4. **Type Checking**: Values must match their declared types
5. **Table Consistency**: All rows must have the same number of columns as defined
6. **Unique Names**: Parameter names must be unique
7. **Required Parameter Fields**: Each parameter needs `name`, `type`, `description`

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

### Phase 2: Requirements & Templates (Planned)
- Markdown requirement documents
- Template validation
- Requirement metadata

### Phase 3: Cross-References & Traceability (Planned)
- References between requirements and parameters
- Dependency tracking via Bazel
- Traceability analysis

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

1. Write tests first (in `*_test.cc` files for integration tests)
2. Implement functionality to make tests pass
3. Refactor while keeping tests green
4. Ensure Buildifier passes on all Starlark code

## License

TBD

## Contact

TBD
