# Using Fire in Your Project

This guide shows how to use Fire as a Bazel module in your own projects.

Fire provides **pure Starlark** parameter management with compile-time validation and C++ code generation.

## Adding Fire as a Dependency

### Step 1: Add to MODULE.bazel

In your project's `MODULE.bazel` file, add Fire as a dependency:

```python
bazel_dep(name = "fire", version = "0.1.0")

# If using a local checkout during development:
local_path_override(
    module_name = "fire",
    path = "../fire",  # Adjust path as needed
)
```

### Step 2: Import Rules in BUILD Files

In your `BUILD.bazel` files where you want to use Fire:

```python
load("@fire//fire/starlark:parameters_inline.bzl", "parameter_library", "cc_parameter_library")
```

## Quick Start Example

### Define Parameters

Parameters can be defined inline in BUILD.bazel or in separate .bzl files.

**Option 1: Separate .bzl file (recommended for larger parameter sets)**

`vehicle_params.bzl`:
```python
"""Vehicle parameter definitions."""

VEHICLE_PARAMS = [
    {
        "name": "max_velocity",
        "type": "float",
        "unit": "m/s",
        "value": 55.0,
        "description": "Maximum vehicle velocity",
    },
    {
        "name": "wheel_count",
        "type": "integer",
        "value": 4,
        "description": "Number of wheels",
    },
]
```

`BUILD.bazel`:
```python
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")
load("@fire//fire/starlark:parameters_inline.bzl", "parameter_library", "cc_parameter_library")
load(":vehicle_params.bzl", "VEHICLE_PARAMS")

# Define parameters (validated at load time!)
parameter_library(
    name = "vehicle_params_header",
    namespace = "vehicle.dynamics",
    parameters = VEHICLE_PARAMS,
)

# Create C++ library from parameters
cc_parameter_library(
    name = "vehicle_params",
    parameter_library = ":vehicle_params_header",
)

# Use in your code
cc_library(
    name = "controller",
    srcs = ["controller.cc"],
    hdrs = ["controller.h"],
    deps = [":vehicle_params"],
)
```

**Option 2: Inline (good for small parameter sets)**

```python
load("@fire//fire/starlark:parameters_inline.bzl", "parameter_library", "cc_parameter_library")

parameter_library(
    name = "vehicle_params_header",
    namespace = "vehicle.dynamics",
    parameters = [
        {"name": "max_velocity", "type": "float", "value": 55.0, ...},
        {"name": "wheel_count", "type": "integer", "value": 4, ...},
    ],
)
```

### Use in C++ Code

```cpp
#include "vehicle_params_header.h"

namespace my_controller {

void Controller::Initialize() {
    using namespace vehicle::dynamics;

    // Access parameters as constexpr values
    double max_vel = max_velocity;  // 55.0 m/s
    int wheels = wheel_count;       // 4

    // Compile-time constants - fully optimized
    static_assert(wheel_count == 4, "Expected 4 wheels");
}

} // namespace my_controller
```

## Complete Example

Here's a complete example for an autonomous vehicle project:

### Project Structure

```
my_vehicle_project/
├── MODULE.bazel
├── vehicle/
│   ├── BUILD.bazel
│   ├── parameters/
│   │   └── BUILD.bazel          # Parameter definitions
│   └── control/
│       ├── BUILD.bazel
│       ├── controller.h
│       ├── controller.cc
│       └── controller_test.cc
```

### vehicle/parameters/BUILD.bazel

```python
load("@fire//fire/starlark:parameters_inline.bzl", "parameter_library", "cc_parameter_library")

# Dynamics parameters
parameter_library(
    name = "dynamics_header",
    namespace = "vehicle.parameters.dynamics",
    parameters = [
        {
            "name": "max_velocity",
            "type": "float",
            "unit": "m/s",
            "value": 55.0,
            "description": "Maximum vehicle velocity",
        },
        {
            "name": "max_acceleration",
            "type": "float",
            "unit": "m/s^2",
            "value": 3.5,
            "description": "Maximum acceleration",
        },
        {
            "name": "wheel_base",
            "type": "float",
            "unit": "m",
            "value": 2.7,
            "description": "Distance between front and rear axles",
        },
    ],
)

cc_parameter_library(
    name = "dynamics",
    parameter_library = ":dynamics_header",
    visibility = ["//visibility:public"],
)

# Safety parameters
parameter_library(
    name = "safety_header",
    namespace = "vehicle.parameters.safety",
    parameters = [
        {
            "name": "min_safe_distance",
            "type": "float",
            "unit": "m",
            "value": 10.0,
            "description": "Minimum safe following distance",
        },
        {
            "name": "emergency_brake_threshold",
            "type": "float",
            "unit": "m",
            "value": 5.0,
            "description": "Distance threshold for emergency braking",
        },
        {
            "name": "safety_margins_by_speed",
            "type": "table",
            "description": "Required safety margins at different speeds",
            "columns": [
                {"name": "speed", "type": "float", "unit": "m/s"},
                {"name": "lateral_margin", "type": "float", "unit": "m"},
                {"name": "longitudinal_margin", "type": "float", "unit": "m"},
            ],
            "rows": [
                [10.0, 0.5, 10.0],
                [20.0, 0.75, 20.0],
                [30.0, 1.0, 40.0],
            ],
        },
    ],
)

cc_parameter_library(
    name = "safety",
    parameter_library = ":safety_header",
    visibility = ["//visibility:public"],
)
```

### vehicle/control/controller.h

```cpp
#pragma once

namespace vehicle::control {

class VelocityController {
public:
    VelocityController() = default;

    double CalculateSafeVelocity(double desired_velocity,
                                  double distance_to_obstacle) const;

    bool RequiresEmergencyBrake(double distance_to_obstacle) const;
};

} // namespace vehicle::control
```

### vehicle/control/controller.cc

```cpp
#include "vehicle/control/controller.h"
#include "vehicle/parameters/dynamics_header.h"
#include "vehicle/parameters/safety_header.h"

#include <algorithm>
#include <cmath>

namespace vehicle::control {

double VelocityController::CalculateSafeVelocity(
    double desired_velocity,
    double distance_to_obstacle) const {

    using namespace vehicle::parameters;

    // Clamp to maximum velocity (compile-time constant)
    double safe_velocity = std::min(desired_velocity,
                                    dynamics::max_velocity);

    // Reduce velocity if obstacle is close
    if (distance_to_obstacle < safety::min_safe_distance) {
        double max_safe_vel = std::sqrt(
            2.0 * dynamics::max_acceleration * distance_to_obstacle
        );
        safe_velocity = std::min(safe_velocity, max_safe_vel);
    }

    return safe_velocity;
}

bool VelocityController::RequiresEmergencyBrake(
    double distance_to_obstacle) const {

    return distance_to_obstacle <
           vehicle::parameters::safety::emergency_brake_threshold;
}

} // namespace vehicle::control
```

### vehicle/control/BUILD.bazel

```python
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")

cc_library(
    name = "controller",
    srcs = ["controller.cc"],
    hdrs = ["controller.h"],
    deps = [
        "//vehicle/parameters:dynamics",
        "//vehicle/parameters:safety",
    ],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "controller_test",
    srcs = ["controller_test.cc"],
    deps = [":controller"],
)
```

## Parameter Types

Fire supports the following parameter types:

| Type | C++ Type | Starlark Example | C++ Usage |
|------|----------|------------------|-----------|
| `float` | `double` | `"value": 55.0` | `constexpr double max_vel = 55.0;` |
| `integer` | `int` | `"value": 4` | `constexpr int count = 4;` |
| `string` | `const char*` | `"value": "test"` | `constexpr const char* name = "test";` |
| `boolean` | `bool` | `"value": True` | `constexpr bool flag = true;` |
| `table` | `struct + array` | See below | Array of structs with size constant |

### Table Parameters

Tables generate a struct type and a constexpr array:

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
    ],
}
```

Generated C++ code:

```cpp
struct GearRatiosRow {
    int gear;
    double ratio;
    /// Unit: km/h
    double max_speed;
};

/// Gear ratios by gear number
constexpr GearRatiosRow gear_ratios[] = {
    {1, 3.5, 40.0},
    {2, 2.1, 70.0},
    {3, 1.4, 110.0},
};

/// Number of rows in gear_ratios
constexpr size_t gear_ratios_size = 3;
```

Usage in C++:

```cpp
for (size_t i = 0; i < gear_ratios_size; ++i) {
    int gear = gear_ratios[i].gear;
    double ratio = gear_ratios[i].ratio;
    double max_speed = gear_ratios[i].max_speed;
    // ...
}
```

## Key Features

### 1. Load-Time Validation

Parameters are validated when the BUILD file is loaded:

```python
parameter_library(
    name = "bad_params",
    namespace = "invalid namespace!",  # ERROR: Invalid namespace format!
    parameters = [],
)
```

Error appears immediately - no need to build to find errors.

### 2. Compile-Time Constants

All parameters are generated as `constexpr`, enabling:

```cpp
// Compiler can optimize these away
constexpr double max_vel = vehicle::dynamics::max_velocity;

// Can use in constant expressions
constexpr double safety_factor = max_vel * 0.8;

// Static assertions
static_assert(max_vel > 0, "Max velocity must be positive");

// Array sizes
double speeds[static_cast<int>(max_vel) + 1];
```

### 3. Type Safety

The C++ type system ensures correct usage:

```cpp
int wheels = vehicle::dynamics::wheel_count;  // OK: int
double wheels = vehicle::dynamics::wheel_count;  // OK: implicit conversion
std::string wheels = vehicle::dynamics::wheel_count;  // ERROR: No conversion
```

### 4. Documentation in Code

Parameters include documentation from the BUILD file:

```cpp
/// Maximum vehicle velocity - Unit: m/s
constexpr double max_velocity = 55.0;
```

IDEs show this documentation on hover!

## Best Practices

### 1. Organize Parameters by Domain

```
parameters/
├── BUILD.bazel
    ├── dynamics (velocity, acceleration, etc.)
    ├── safety (thresholds, margins, etc.)
    ├── hardware (sensor specs, etc.)
    └── environment (assumptions, limits, etc.)
```

### 2. Use Meaningful Namespaces

```python
namespace = "company.product.subsystem"
# Generates: company::product::subsystem
```

### 3. Always Specify Units

```python
{
    "name": "max_velocity",
    "type": "float",
    "unit": "m/s",  # Always include!
    "value": 55.0,
}
```

### 4. Provide Clear Descriptions

```python
"description": "Maximum velocity per ISO 26262 safety analysis"
```

Explain **why** a parameter has its value, not just what it is.

### 5. Use Tables for Related Data

```python
# Good: Related data in a table
{
    "name": "speed_limits",
    "type": "table",
    "columns": [
        {"name": "zone", "type": "string"},
        {"name": "limit", "type": "float", "unit": "km/h"},
    ],
    "rows": [
        ["residential", 30.0],
        ["urban", 50.0],
        ["highway", 130.0],
    ],
}

# Less good: Separate parameters
{"name": "residential_limit", "value": 30.0},
{"name": "urban_limit", "value": 50.0},
{"name": "highway_limit", "value": 130.0},
```

## Advantages Over External Configuration Files

### Immediate Feedback
Errors are caught when loading BUILD files, not during builds or at runtime.

### No File Parsing
Parameters are Starlark data - no YAML/JSON parsing, no file I/O.

### IDE Support
Starlark is understood by Bazel IDEs - syntax highlighting, validation, refactoring.

### Version Control Friendly
Parameters are in BUILD files alongside the code that uses them.

### Bazel-Native
Everything is pure Starlark - no external tools or dependencies.

## Building and Testing

```bash
# Build parameter libraries
bazel build //vehicle/parameters:all

# View generated headers
cat bazel-bin/vehicle/parameters/dynamics_header.h

# Build code that uses parameters
bazel build //vehicle/control:controller

# Run tests
bazel test //vehicle/control:controller_test
```

## Troubleshooting

### "Parameter validation failed"

Check the error message - it tells you exactly what's wrong:
- Missing required fields
- Invalid type
- Table column mismatch
- Duplicate names
- Invalid namespace format

### "file not found" when including header

The generated header name is `<target_name>.h`:

```python
parameter_library(
    name = "my_params_header",  # Generates my_params_header.h
    ...
)
```

Include it as:
```cpp
#include "my_params_header.h"
```

### Parameters not updating

Bazel caches aggressively. After changing parameters:

```bash
bazel clean
bazel build //your:target
```

Or use:
```bash
bazel build //your:target --expunge
```

## Next Steps

- See [README.md](../README.md) for project overview
- Check [examples/BUILD.bazel](../examples/BUILD.bazel) for a complete working example
- Read [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines

## Example Repository

See the `examples/` directory for a complete working example with:
- Multiple parameter types (float, integer, string, boolean, table)
- Nested namespaces
- C++ test demonstrating usage
- All features in action
