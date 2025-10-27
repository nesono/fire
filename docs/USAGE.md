# Using Fire in Your Project

This guide shows how to use Fire as a Bazel module in your own projects.

## Adding Fire as a Dependency

### Step 1: Add to MODULE.bazel

In your project's `MODULE.bazel` file, add Fire as a dependency:

```python
bazel_dep(name = "fire", version = "0.1.0")

# If using a local checkout during development:
local_path_override(
    module_name = "fire",
    path = "../fire.git",  # Adjust path as needed
)
```

For production use with a published module:

```python
bazel_dep(name = "fire", version = "0.1.0")
```

### Step 2: Import Rules in BUILD Files

In your `BUILD.bazel` files where you want to use Fire:

```python
load("@fire//fire/rules:parameters.bzl", "parameter_library", "cc_parameter_library")
```

## Complete Example

Here's a complete example showing how to integrate Fire into an autonomous vehicle project:

### Project Structure

```
my_vehicle_project/
├── MODULE.bazel
├── vehicle/
│   ├── BUILD.bazel
│   ├── parameters/
│   │   ├── BUILD.bazel
│   │   ├── dynamics.yaml
│   │   └── safety.yaml
│   └── control/
│       ├── BUILD.bazel
│       ├── controller.h
│       ├── controller.cc
│       └── controller_test.cc
```

### MODULE.bazel

```python
module(
    name = "my_vehicle_project",
    version = "1.0.0",
)

bazel_dep(name = "fire", version = "0.1.0")
bazel_dep(name = "rules_cc", version = "0.0.9")
```

### vehicle/parameters/dynamics.yaml

```yaml
schema_version: "1.0"
namespace: "vehicle.parameters.dynamics"

parameters:
  - name: max_velocity
    type: float
    unit: m/s
    value: 55.0
    description: "Maximum vehicle velocity"

  - name: max_acceleration
    type: float
    unit: m/s^2
    value: 3.5
    description: "Maximum acceleration"

  - name: max_deceleration
    type: float
    unit: m/s^2
    value: 8.0
    description: "Maximum deceleration (braking)"

  - name: wheel_base
    type: float
    unit: m
    value: 2.7
    description: "Distance between front and rear axles"
```

### vehicle/parameters/safety.yaml

```yaml
schema_version: "1.0"
namespace: "vehicle.parameters.safety"

parameters:
  - name: min_safe_distance
    type: float
    unit: m
    value: 10.0
    description: "Minimum safe following distance"

  - name: emergency_brake_threshold
    type: float
    unit: m
    value: 5.0
    description: "Distance threshold for emergency braking"

  - name: collision_warning_time
    type: float
    unit: s
    value: 2.5
    description: "Time to collision for warning activation"

  - name: safety_margins_by_speed
    type: table
    description: "Required safety margins at different speeds"
    columns:
      - name: speed
        type: float
        unit: m/s
      - name: lateral_margin
        type: float
        unit: m
      - name: longitudinal_margin
        type: float
        unit: m
    rows:
      - [10.0, 0.5, 10.0]
      - [20.0, 0.75, 20.0]
      - [30.0, 1.0, 40.0]
```

### vehicle/parameters/BUILD.bazel

```python
load("@fire//fire/rules:parameters.bzl", "parameter_library", "cc_parameter_library")

# Dynamics parameters
parameter_library(
    name = "dynamics",
    src = "dynamics.yaml",
)

cc_parameter_library(
    name = "dynamics_cc",
    parameter_library = ":dynamics",
)

# Safety parameters
parameter_library(
    name = "safety",
    src = "safety.yaml",
)

cc_parameter_library(
    name = "safety_cc",
    parameter_library = ":safety",
)

# Make parameters visible to other packages
exports_files([
    "dynamics.yaml",
    "safety.yaml",
])
```

### vehicle/control/controller.h

```cpp
#pragma once

#include "vehicle/parameters/dynamics_cc.h"
#include "vehicle/parameters/safety_cc.h"

namespace vehicle::control {

class VelocityController {
public:
    VelocityController() = default;

    // Calculate safe target velocity based on current conditions
    double CalculateSafeVelocity(double desired_velocity,
                                  double distance_to_obstacle) const;

    // Check if emergency braking is required
    bool RequiresEmergencyBrake(double distance_to_obstacle) const;

private:
    // Parameters are accessible as compile-time constants
    static constexpr double max_velocity_ =
        vehicle::parameters::dynamics::max_velocity;

    static constexpr double emergency_threshold_ =
        vehicle::parameters::safety::emergency_brake_threshold;
};

} // namespace vehicle::control
```

### vehicle/control/controller.cc

```cpp
#include "vehicle/control/controller.h"
#include <algorithm>
#include <cmath>

namespace vehicle::control {

double VelocityController::CalculateSafeVelocity(
    double desired_velocity,
    double distance_to_obstacle) const {

    using namespace vehicle::parameters;

    // Clamp to maximum velocity
    double safe_velocity = std::min(desired_velocity,
                                    dynamics::max_velocity);

    // Reduce velocity if obstacle is close
    if (distance_to_obstacle < safety::min_safe_distance) {
        // Calculate velocity based on braking distance
        double max_safe_vel = std::sqrt(
            2.0 * dynamics::max_deceleration * distance_to_obstacle
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

### vehicle/control/controller_test.cc

```cpp
#include "vehicle/control/controller.h"
#include <cassert>
#include <iostream>

int main() {
    using namespace vehicle::control;
    using namespace vehicle::parameters;

    VelocityController controller;

    // Test 1: Normal operation
    double safe_vel = controller.CalculateSafeVelocity(50.0, 100.0);
    assert(safe_vel == 50.0);
    std::cout << "✓ Normal velocity: " << safe_vel << " m/s\n";

    // Test 2: Maximum velocity limit
    safe_vel = controller.CalculateSafeVelocity(100.0, 100.0);
    assert(safe_vel == dynamics::max_velocity);
    std::cout << "✓ Clamped to max: " << safe_vel << " m/s\n";

    // Test 3: Emergency braking
    bool emergency = controller.RequiresEmergencyBrake(3.0);
    assert(emergency == true);
    std::cout << "✓ Emergency brake activated\n";

    // Test 4: Using table parameters
    std::cout << "\nSafety margins by speed:\n";
    for (size_t i = 0; i < safety::safety_margins_by_speed_size; ++i) {
        const auto& entry = safety::safety_margins_by_speed[i];
        std::cout << "  Speed: " << entry.speed << " m/s"
                  << ", Lateral: " << entry.lateral_margin << " m"
                  << ", Longitudinal: " << entry.longitudinal_margin << " m\n";
    }

    std::cout << "\nAll tests passed!\n";
    return 0;
}
```

### vehicle/control/BUILD.bazel

```python
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")

cc_library(
    name = "controller",
    srcs = ["controller.cc"],
    hdrs = ["controller.h"],
    deps = [
        "//vehicle/parameters:dynamics_cc",
        "//vehicle/parameters:safety_cc",
    ],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "controller_test",
    srcs = ["controller_test.cc"],
    deps = [":controller"],
)
```

## Building and Testing

```bash
# Build everything
bazel build //...

# Run tests
bazel test //...

# Run specific test
bazel test //vehicle/control:controller_test

# Build specific target
bazel build //vehicle/parameters:dynamics_cc

# View generated header
cat bazel-bin/vehicle/parameters/dynamics_cc.h
```

## Benefits of Using Fire

### 1. Type Safety

Parameters are validated at build time and generated as `constexpr` constants:

```cpp
// Compile-time constant - optimized away by compiler
constexpr double max_vel = vehicle::parameters::dynamics::max_velocity;

// Compiler error if you try to modify it
// max_vel = 100.0;  // ERROR: cannot assign to const
```

### 2. Dependency Tracking

Bazel tracks parameter dependencies automatically:

```python
cc_library(
    name = "controller",
    deps = [
        "//vehicle/parameters:dynamics_cc",  # Bazel knows about this dependency
    ],
)
```

If `dynamics.yaml` changes, Bazel will rebuild `controller` automatically.

### 3. Documentation in Code

Generated headers include documentation from parameter files:

```cpp
/// Maximum vehicle velocity - Unit: m/s
constexpr double max_velocity = 55.0;
```

### 4. Single Source of Truth

Parameters are defined once in YAML and used everywhere:
- In C++ code (via generated headers)
- In documentation
- In configuration files
- In test cases

### 5. Validation

Invalid parameter files are caught at build time:

```bash
$ bazel build //vehicle/parameters:dynamics_cc
ERROR: Validation failed: Parameter 'max_velocity' must be a number (float)
```

## Best Practices

### 1. Organize Parameters by Domain

Group related parameters into separate files:

```
parameters/
├── dynamics.yaml      # Vehicle dynamics
├── safety.yaml        # Safety thresholds
├── hardware.yaml      # Hardware specifications
└── environment.yaml   # Environment assumptions
```

### 2. Use Meaningful Namespaces

Choose namespaces that reflect your project structure:

```yaml
namespace: "company.product.subsystem"
```

### 3. Always Specify Units

Include units for all physical quantities:

```yaml
- name: max_velocity
  type: float
  unit: m/s
  value: 55.0
```

### 4. Provide Clear Descriptions

Write descriptions that explain **why** a parameter has its value:

```yaml
description: "Maximum velocity per ISO 26262 safety analysis"
```

### 5. Use Tables for Related Data

When parameters are naturally tabular, use table types:

```yaml
- name: gear_ratios
  type: table
  columns:
    - {name: gear, type: integer}
    - {name: ratio, type: float}
  rows:
    - [1, 3.5]
    - [2, 2.1]
```

## Troubleshooting

### Build Fails: "cannot find parameter file"

Make sure the file is listed in the `srcs` of your `parameter_library`:

```python
parameter_library(
    name = "params",
    src = "parameters.yaml",  # Must exist
)
```

### Include Path Not Found

The generated header follows your package structure:

```cpp
// For //vehicle/parameters:dynamics_cc
#include "vehicle/parameters/dynamics_cc.h"
```

### Namespace Mismatch

The namespace comes from the YAML file, not the Bazel package:

```yaml
namespace: "vehicle.parameters.dynamics"  # This determines namespace
```

```cpp
namespace vehicle::parameters::dynamics {
    // Parameters here
}
```

## Next Steps

- See [README.md](../README.md) for full feature documentation
- Check [examples/](../examples/) for more examples
- Read about upcoming features in the Roadmap section
