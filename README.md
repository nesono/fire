# Fire - Requirements Management System for Bazel

Fire is a Bazel module for managing safety-critical system requirements, parameters, and their relationships through Bazel's dependency graph.

## Status: Phase 1 - Parameter System ✓

Phase 1 is complete and provides parameter management with code generation capabilities.

## Features (Phase 1)

- **Parameter Validation**: Validate parameter files against a well-defined schema
- **Type System**: Support for `float`, `integer`, `string`, `boolean`, and `table` types
- **Units**: Associate physical units with parameters
- **Tables**: Define multi-column tabular data with typed columns
- **C++ Code Generation**: Generate type-safe `constexpr` C++ headers from parameters
- **Bazel Integration**: Custom Bazel rules for seamless build integration
- **Test-Driven Development**: All components have comprehensive test coverage

## Quick Start

### 1. Define Parameters

Create a parameter file in YAML format (e.g., `vehicle_params.yaml`):

```yaml
schema_version: "1.0"
namespace: "vehicle.dynamics"

parameters:
  - name: maximum_vehicle_velocity
    type: float
    unit: m/s
    value: 55.0
    description: "Maximum design velocity for the vehicle"

  - name: wheel_count
    type: integer
    value: 4
    description: "Number of wheels on the vehicle"

  - name: braking_distance_table
    type: table
    description: "Braking distances under various conditions"
    columns:
      - name: velocity
        type: float
        unit: m/s
      - name: friction_coefficient
        type: float
        unit: dimensionless
      - name: braking_distance
        type: float
        unit: m
    rows:
      - [10.0, 0.7, 7.1]
      - [20.0, 0.7, 28.6]
      - [30.0, 0.7, 64.3]
```

### 2. Create Bazel Targets

In your `BUILD.bazel` file:

```python
load("@fire//fire/rules:parameters.bzl", "parameter_library", "cc_parameter_library")
load("@rules_cc//cc:defs.bzl", "cc_test")

# Validate the parameter file
parameter_library(
    name = "vehicle_params",
    src = "vehicle_params.yaml",
)

# Generate C++ header from parameters
cc_parameter_library(
    name = "vehicle_params_cc",
    parameter_library = ":vehicle_params",
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
#include "your/package/vehicle_params_cc.h"

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

## Parameter File Format

### Schema Version

Every parameter file must specify a schema version:

```yaml
schema_version: "1.0"
```

### Namespace

Parameters are generated within a C++ namespace (supports nested namespaces):

```yaml
namespace: "vehicle.dynamics.braking"
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

Parameters have the following fields:

- `name` (required): Identifier for the parameter
- `type` (required): One of `float`, `integer`, `string`, `boolean`, `table`
- `value` (required for non-table types): The parameter value
- `description` (required): Human-readable description
- `unit` (optional): Physical unit for the parameter

Example:

```yaml
parameters:
  - name: max_temperature
    type: float
    unit: celsius
    value: 85.0
    description: "Maximum operating temperature"
```

### Table Parameters

Tables define multi-column tabular data:

```yaml
parameters:
  - name: gear_ratios
    type: table
    description: "Gear ratios by gear number"
    columns:
      - name: gear
        type: integer
      - name: ratio
        type: float
      - name: max_speed
        type: float
        unit: km/h
    rows:
      - [1, 3.5, 40.0]
      - [2, 2.1, 70.0]
      - [3, 1.4, 110.0]
      - [4, 1.0, 160.0]
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

Validates a parameter YAML file.

**Attributes:**
- `src`: The YAML parameter file (`.yaml` or `.yml`)

**Example:**
```python
parameter_library(
    name = "my_params",
    src = "parameters.yaml",
)
```

### `cc_parameter_library()`

Generates a C++ header file from a validated parameter library.

**Attributes:**
- `parameter_library`: The `parameter_library` target to generate code from
- `namespace` (optional): Override the namespace from the parameter file

**Example:**
```python
cc_parameter_library(
    name = "my_params_cc",
    parameter_library = ":my_params",
    # namespace = "custom.namespace",  # Optional override
)
```

## Project Structure

```
fire/
├── MODULE.bazel              # Bazel module definition
├── BUILD.bazel               # Root build file
├── README.md                 # This file
├── fire/
│   ├── parameters/           # Parameter validation and code generation
│   │   ├── validator.py      # Parameter validation logic
│   │   ├── validator_test.py # Validation tests
│   │   ├── cpp_generator.py  # C++ code generator
│   │   ├── cpp_generator_test.py  # Generator tests
│   │   └── BUILD.bazel
│   ├── rules/                # Bazel rule definitions
│   │   ├── parameters.bzl    # parameter_library and cc_parameter_library rules
│   │   └── BUILD.bazel
│   └── tools/                # Command-line tools
│       ├── validate_parameters.py      # Validation tool
│       ├── generate_cpp_parameters.py  # C++ generation tool
│       └── BUILD.bazel
└── examples/                 # Example usage
    ├── vehicle_params.yaml   # Example parameter file
    ├── vehicle_params_test.cc  # Integration test
    └── BUILD.bazel
```

## Testing

Run all tests:

```bash
bazel test //...
```

Run specific test suites:

```bash
bazel test //fire/parameters:validator_test
bazel test //fire/parameters:cpp_generator_test
bazel test //examples:vehicle_params_test
```

## Validation Rules

The parameter validator enforces:

1. **Required Fields**: `schema_version`, `namespace`, `parameters` at top level
2. **Namespace Format**: Must be dot-separated identifiers (e.g., `vehicle.dynamics`)
3. **Parameter Types**: Only `float`, `integer`, `string`, `boolean`, `table` are valid
4. **Type Checking**: Values must match their declared types
5. **Table Consistency**: All rows must have the same number of columns as defined
6. **Unique Names**: Parameter names must be unique within a file
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
- Parameter file validation
- C++ code generation
- Bazel rules integration
- Comprehensive tests

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

1. Write tests first (in `*_test.py` or `*_test.cc` files)
2. Implement functionality to make tests pass
3. Refactor while keeping tests green
4. Keep implementation and test files together in the same directory

## License

TBD

## Contact

TBD
