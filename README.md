# FIRE — Fully Integrated Requirements Engineering

[![CI](https://github.com/nesono/fire/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/nesono/fire/actions/workflows/ci.yaml)

FIRE is a Bazel module for managing safety-critical requirements and parameters
with versioned traceability between them. Requirements are written in Markdown
and parameters in YAML, with cross-references validated at build time. Parameters
can be consumed from generated source code libraries in C++, Python, Go, Rust,
and Java.

## Integration

Add to `MODULE.bazel`:

```starlark
bazel_dep(name = "fire", version = "0.4.0")

# Add language rules for the languages you intend to use
bazel_dep(name = "rules_cc", version = "0.2.16")
bazel_dep(name = "rules_python", version = "1.8.3")
```

## System Requirements

System requirements are stored in `.sysreq.md` files. Each requirement is an
H2 heading followed by a metadata line and free-form Markdown text.

**Metadata fields:**

- `SIL`: Safety Integrity Level — `ASIL-A/B/C/D` (ISO 26262), `SIL-1/2/3/4`
  (IEC 61508), `DAL-A/B/C/D/E` (DO-178C), `QM`, or `TODO(KEY-1234)`
- `Sec`: Security flag — `true`, `false`, or `TODO(KEY-1234)`
- `Version`: Positive integer, incremented when the requirement changes
  semantically

```markdown
## REQ-BRK-001

SIL: ASIL-D | Sec: true | Version: 4

**Emergency Braking Distance**

The vehicle SHALL come to a full stop within the distance defined by
[@braking_distance_table](/vehicle/params.yaml?version=1#braking_distance_table).
```

References use standard Markdown links with repository-relative paths and a
mandatory `?version=N` query parameter:

- Parameters: `[@param_name](/path/to/params.yaml?version=N#param_name)`
- Requirements: `[REQ-ID](/path/to/file.sysreq.md?version=N#REQ-ID)`

Register requirements in Bazel:

```starlark
load("@fire//fire/starlark:requirements.bzl", "requirement_library")

requirement_library(
    name = "vehicle_requirements",
    srcs = glob(["requirements/*.sysreq.md"]),
    deps = [":vehicle_params"],
)
```

## Software (Component) Requirements

Software requirements are stored in `.swreq.md` files. They follow the same
format as system requirements with one addition: a `Parent` field that links
back to the parent system requirement and tracks its version.

Single parent on the same line:

```markdown
## REQ_BC_CALCULATE_FORCE

SIL: ASIL-D | Sec: false | Version: 2 | Parent: [REQ-BRK-001](/requirements/braking.sysreq.md?version=4#REQ-BRK-001)
```

Multiple parents use multi-line continuation with a trailing `|`:

```markdown
## REQ_BC_EMERGENCY_FUSION

SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-BRK-001](/requirements/braking.sysreq.md?version=4#REQ-BRK-001) |
Parent: [REQ-SENS-003](/requirements/sensing.sysreq.md?version=2#REQ-SENS-003)
```

## Parameters YAML

Parameter files define typed, versioned constants and lookup tables for use in
requirements and source code.

**Naming:** `<name>_v<N>` — lowercase snake_case with a mandatory version suffix.

**Scalar parameters** infer their type from the YAML value (`f64` from float,
`i64` from integer, `bool` from boolean, `string` from string):

```yaml
max_speed_v1:
  value: 30.0
  unit: m/s
  description: Maximum allowed speed

wheel_count_v1:
  value: 4
  unit: "1"
  description: Number of wheels
```

**Table parameters** require `type: table`. Column types are inferred from the
first row — do not specify them explicitly:

```yaml
braking_distance_table_v1:
  type: table
  description: Braking distances by velocity and friction coefficient
  columns:
    - name: velocity
      unit: m/s
    - name: braking_distance
      unit: m
  rows:
    - [10.0, 7.1]
    - [20.0, 28.6]
```

**Versioning:** Add a `_v<N+1>` key alongside the existing one to update a
parameter. References to the old version are flagged as stale. At most two
consecutive versions may coexist per parameter.

Register in Bazel:

```starlark
load("@fire//fire/starlark:parameters.bzl", "parameter_library")

parameter_library(
    name = "vehicle_params",
    src = "vehicle_params.yaml",
)
```

## Code Generation

FIRE generates one source file per parameter version into a directory artifact.
Wrap this artifact in a language library target to use it in your code. Unit
suffixes are embedded in generated names (e.g., `m/s` → `_MPS` in
C++/Python/Rust, `Mps` in Go/Java).

### C++

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_cc_parameters")
load("@rules_cc//cc:defs.bzl", "cc_library")

generate_cc_parameters(
    name = "vehicle_params_h",
    parameter_library = ":vehicle_params",
    namespace = "vehicle::dynamics",  # optional
)

cc_library(
    name = "vehicle_params_cc",
    hdrs = [":vehicle_params_h"],
)
```

```cpp
#include "vehicle/dynamics/vehicle_params/max_speed_v1.h"

double limit = MAX_SPEED_MPS_V1;
```

### Python

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_python_parameters")
load("@rules_python//python:defs.bzl", "py_library")

generate_python_parameters(
    name = "vehicle_params_py_src",
    parameter_library = ":vehicle_params",
)

py_library(
    name = "vehicle_params_py",
    data = [":vehicle_params_py_src"],
)
```

```python
from vehicle.dynamics.vehicle_params.max_speed_v1 import MAX_SPEED_MPS_V1
```

### Go

Go generates one sub-package per parameter version (Go packages map to
directories):

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_go_parameters")
load("@rules_go//go:def.bzl", "go_library")

generate_go_parameters(
    name = "vehicle_params_go_src",
    parameter_library = ":vehicle_params",
)

go_library(
    name = "max_speed_v1_go",
    srcs = [":vehicle_params_go_src"],
    importpath = "vehicle/dynamics/vehicle_params/max_speed_v1",
)
```

```go
import speed "vehicle/dynamics/vehicle_params/max_speed_v1"

limit := speed.MaxSpeedMpsV1
```

### Rust

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_rust_parameters")

generate_rust_parameters(
    name = "vehicle_params_rs",
    parameter_library = ":vehicle_params",
)
```

```rust
use vehicle_params_rs::MAX_SPEED_MPS_V1;
```

### Java

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_java_parameters")
load("@rules_java//java:defs.bzl", "java_library")

generate_java_parameters(
    name = "vehicle_params_java_src",
    package_prefix = "com.example",
    parameter_library = ":vehicle_params",
)

java_library(
    name = "vehicle_params_java",
    srcs = [":vehicle_params_java_src"],
)
```

```java
import static com.example.VehicleParams.*;

double limit = MaxSpeedMpsV1;
```

## Release Readiness Report

The release readiness report checks version consistency across requirements and
parameters, open TODOs, and implementation/verification trace coverage.

```starlark
load("@fire//fire/starlark:reports.bzl", "release_report", "release_readiness_test")

release_report(
    name = "release_report",
    requirements = [":component_requirements"],
    params = [":vehicle_params"],
    source_traces = [":brake_controller_trace"],
    product = "Brake Controller",
    out = "RELEASE_REPORT.md",
)

release_readiness_test(
    name = "release_readiness",
    report = ":release_report",
)
```

Build and inspect the report during authoring:

```bash
bazel build //path/to:release_report
cat bazel-bin/path/to/RELEASE_REPORT.md
```

Use `release_readiness_test` as a CI gate — it fails the build when the report
status is `NOT READY FOR RELEASE`.

## Custom Document Types

FIRE ships with three built-in document types (`.sysreq.md`, `.swreq.md`,
`.regreq.md`). You can define additional types by providing a
`fire_config.yaml`:

```yaml
fire_config_version: 1

field_definitions:
  version:
    display_name: "Version"
    type: int
    min_value: 1

  sil:
    display_name: "SIL"
    type: enum
    values: ["ASIL-A", "ASIL-B", "ASIL-C", "ASIL-D", "QM"]
    allow_todo: true

document_types:
  handbook:
    suffix: ".handbook.md"
    display_name: "Handbook Entry"
    description: "Product handbook entries"
    required_fields: [version]
    optional_fields: [sil]
```

Pass the config to FIRE rules:

```starlark
load("@fire//fire/starlark:requirements.bzl", "requirement_library")

requirement_library(
    name = "handbook_entries",
    srcs = glob(["docs/*.handbook.md"]),
    config = ":fire_config.yaml",
)
```

The default configuration (matching the built-in types) is at
`@fire//fire/starlark:default_fire_config.yaml`.

### Format Specification

Generate a `FORMAT_SPECIFICATION.md` from your config for use as
documentation or LLM context:

```starlark
load("@fire//fire/starlark:format_spec.bzl", "generate_format_specification")

generate_format_specification(
    name = "format_spec",
    config = ":fire_config.yaml",
    out = "FORMAT_SPECIFICATION.md",
)
```

## Windows Support

FIRE supports Windows with the following limitations:

### Rust code generation

The `rules_rust` toolchain cannot build on Windows due to an upstream linker
issue with the process_wrapper. All Rust targets must be tagged with
`requires-rust` so they are automatically excluded on Windows via `.bazelrc`:

```starlark
rust_library(
    name = "my_params_rs",
    srcs = [":my_params_rs_src"],
    tags = ["requires-rust"],
)
```

### Shell-based test rules

`release_readiness_test` generates a shell script as its test executable, which
Windows cannot run via `CreateProcessW`. Tag these targets with `requires-shell`
to exclude them on Windows:

```starlark
release_readiness_test(
    name = "release_readiness",
    report = ":release_report",
    tags = ["requires-shell"],
)
```

### Platform configuration

Windows exclusions are handled automatically via `.bazelrc` platform config.
Projects consuming FIRE should include these lines in their `.bazelrc`:

```text
common --enable_platform_specific_config

build:windows --build_tag_filters=-requires-rust,-requires-shell
test:windows --test_tag_filters=-requires-rust,-requires-shell
```

### C++ standard

Windows (MSVC) requires C++20 for designated initializer support. Configure
in `.bazelrc`:

```text
build:windows --cxxopt=/std:c++20
build:windows --host_cxxopt=/std:c++20
```

### File encoding

Python scripts that read or write files containing Unicode characters (e.g.,
`✓`, `⚠️`) must specify `encoding="utf-8"` explicitly, as Windows defaults to
`cp1252`.
