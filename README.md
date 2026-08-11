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
bazel_dep(name = "fire", version = "0.6.1")

# Add language rules for the languages you intend to use
bazel_dep(name = "rules_cc", version = "0.2.17")
bazel_dep(name = "rules_python", version = "1.8.5")
```

## System Requirements

System requirements are stored in `.sysreq.md` files. Each requirement is a
heading followed by a metadata line and free-form Markdown text. Entries are
recognized at any heading level (`#` .. `######`), so ID-bearing entries may be
nested under informal section headers.

**Metadata fields:**

- `SIL`: Safety Integrity Level — `ASIL-A/B/C/D` (ISO 26262), `SIL-1/2/3/4`
  (IEC 61508), `DAL-A/B/C/D/E` (DO-178C/DO-254), `PL-a/b/c/d/e` (ISO 13849),
  `QM`, or `TODO(KEY-1234)`
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

## Regulatory Requirements

Regulatory requirements are stored in `.regreq.md` files. They capture
regulatory obligations where safety integrity and security relevance may not
apply, so only `Version` is required — `SIL`, `Sec`, and `Parent` are all
optional:

```markdown
## REQ-GDPR-DATA-RETENTION

Version: 1

The system SHALL delete personal data after the retention period defined by the
applicable data protection regulation has expired.
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

FIRE generates one source file per parameter version. Wrap the generated output
in a language library target to use it in your code — FIRE never depends on the
language rules itself, so you control which ones you use.

**Output shape** differs by language: C++, Python, and Go produce a directory
artifact of per-version files; Java produces a `.srcjar`; Rust produces a single
`lib.rs`.

**Unit suffixes** are embedded in generated names — `m/s` → `_MPS` in
C++/Python/Rust, `Mps` in Go/Java. Dimensionless units (`1` or `dimensionless`)
add no suffix at all, so `wheel_count_v1` with `unit: "1"` becomes
`WHEEL_COUNT`.

**Version suffixes** depend on the output shape. C++ and Python put each version
in its own file, so the version appears in the file name only and the constant
is unversioned (`max_speed_v1.h` → `MAX_SPEED_MPS`). Go, Rust, and Java put all
versions in one package or file, so the version is part of the identifier
(`MaxSpeedMpsV1`, `MAX_SPEED_MPS_V1`).

**`base_name`** sets the name of the generated directory (defaulting to the
target name), and that name — not the C++ namespace or Java package — is what
appears in include and import paths.

The examples below assume a BUILD file in `//vehicle/dynamics`.

### C++

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_cc_parameters")
load("@rules_cc//cc:defs.bzl", "cc_library")

generate_cc_parameters(
    name = "vehicle_params_h",
    base_name = "vehicle_params_cc",  # output directory name
    parameter_library = ":vehicle_params",
    namespace = "vehicle::dynamics",  # optional
)

cc_library(
    name = "vehicle_params_cc",
    hdrs = [":vehicle_params_h"],
)
```

Headers are included as `<bazel-package>/<base_name>/<param>_v<N>.h`. The
`namespace` attribute only wraps the declarations; it does not affect the path:

```cpp
#include "vehicle/dynamics/vehicle_params_cc/max_speed_v1.h"

double limit = vehicle::dynamics::MAX_SPEED_MPS;
```

### Python

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_python_parameters")
load("@rules_python//python:defs.bzl", "py_library")

generate_python_parameters(
    name = "vehicle_params_py_src",
    base_name = "vehicle_params_py",
    parameter_library = ":vehicle_params",
)

py_library(
    name = "vehicle_params_py",
    data = [":vehicle_params_py_src"],
)
```

```python
from vehicle.dynamics.vehicle_params_py.max_speed_v1 import MAX_SPEED_MPS
```

### Go

All parameter versions land in a single Go package named after `base_name`:

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_go_parameters")
load("@rules_go//go:def.bzl", "go_library")

generate_go_parameters(
    name = "vehicle_params_go_src",
    base_name = "vehicle_params_go",
    parameter_library = ":vehicle_params",
)

go_library(
    name = "vehicle_params_go",
    srcs = [":vehicle_params_go_src"],
)
```

```go
import params "vehicle/dynamics/vehicle_params_go"

limit := params.MaxSpeedMpsV1
```

### Rust

Rust generates one `lib.rs` holding every parameter version. Wrap it in a
`rust_library` to depend on it:

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_rust_parameters")
load("@rules_rust//rust:defs.bzl", "rust_library")

generate_rust_parameters(
    name = "vehicle_params_rs_src",
    parameter_library = ":vehicle_params",
)

rust_library(
    name = "vehicle_params_rs",
    srcs = [":vehicle_params_rs_src"],
)
```

```rust
use vehicle_params_rs::MAX_SPEED_MPS_V1;
```

### Java

All parameters become static members of a single class. The class name defaults
to the PascalCase of the target name — pass `class_name` to override it, since
the target name usually carries a `_src` suffix you do not want in the class:

```starlark
load("@fire//fire/starlark:codegen.bzl", "generate_java_parameters")
load("@rules_java//java:defs.bzl", "java_library")

generate_java_parameters(
    name = "vehicle_params_java_src",
    class_name = "VehicleParams",  # else: VehicleParamsJavaSrc
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

## Source Traceability

`source_traceability` records which source files implement a requirement and
which test files verify it, pinned to a specific requirement version. It
validates that every referenced requirement ID exists in `deps` and emits a
`<name>.trace.json` that the release readiness report consumes as its coverage
input.

```starlark
load("@fire//fire/starlark:traceability.bzl", "source_traceability")

source_traceability(
    name = "brake_controller_trace",
    implements = {
        "brake_controller.cc": [
            "REQ_BC_CALCULATE_FORCE?version=1",
            "REQ_BC_EMERGENCY_BRAKE?version=1",
        ],
        "brake_controller.h": ["REQ_BC_CALCULATE_FORCE?version=1"],
    },
    verifies = {
        "brake_controller_test.cc": [
            "REQ_BC_CALCULATE_FORCE?version=1",
            "REQ_BC_EMERGENCY_BRAKE?version=1",
        ],
    },
    deps = [":brake_controller_requirements"],
)
```

Each entry uses `REQ_ID?version=N`; the suffix is mandatory. Unknown requirement
IDs and versions ahead of the requirement fail the build. When a requirement is
incremented past the version a trace declares, the build prints an `OUTDATED`
warning so the source can be reviewed and re-pinned.

The release report itself checks trace coverage — that each requirement has at
least one implementing and one verifying source — and reports the rest as
missing implementation or verification traces.

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

When no config is provided, FIRE uses three built-in document types
(`.sysreq.md`, `.swreq.md`, `.regreq.md`). You can provide a
`fire_config.yaml` to fully define which document types and fields are
available. A custom config replaces the defaults, so include any
built-in types you still need:

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
    # Narrowed to ISO 26262 here; the built-in field also allows the
    # IEC 61508, DO-178C/DO-254, and ISO 13849 values.
    values: ["ASIL-A", "ASIL-B", "ASIL-C", "ASIL-D", "QM"]
    allow_todo: true

document_types:
  # Include built-in types you need
  sysreq:
    suffix: ".sysreq.md"
    display_name: "System Requirement"
    required_fields: [sil, version]
    optional_fields: []

  # Add your own types
  handbook:
    suffix: ".handbook.md"
    display_name: "Handbook Entry"
    description: "Product handbook entries"
    required_fields: [version]
    optional_fields: [sil]

  # Analysis type with entries nested under informal section headers
  # (e.g. `### HARA-H-001` under `## Hazards`). Set id_pattern to make entry
  # recognition explicit.
  hara:
    suffix: ".hara.md"
    display_name: "Hazard Analysis"
    required_fields: [version]
    id_pattern: "HARA-H-\\d+"
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

## PDF Export

Render a FIRE markdown document to a styled PDF with the `document_pdf` rule.
Styling is controlled entirely through CSS: a default `base.css` ships with
FIRE and your stylesheets cascade after it (no Python required).

```starlark
load("@fire//fire/starlark:pdf.bzl", "document_pdf")

document_pdf(
    name = "braking_pdf",
    srcs = ["braking.sysreq.md"],
    stylesheets = ["//branding:corporate.css"],  # optional, cascaded over base.css
    # config = ":fire_config.yaml",               # optional, defaults to built-in
    # template = "//branding:doc.html.j2",         # optional template override
    out = "braking.pdf",
)
```

```bash
bazel build //path/to:braking_pdf
open bazel-bin/path/to/braking.pdf
```

### Customizing the styling

The template emits a stable set of HTML classes and `data-` attributes that your
stylesheets target, so new document types and fields are styled in CSS with no
Python changes:

```html
<section class="fire-entry" data-doc-type="sysreq">
  <h2 class="fire-entry__id">REQ-BRK-001</h2>
  <dl class="fire-fields">
    <div class="fire-field fire-field--sil" data-value="ASIL-D">
      <dt>SIL</dt>
      <dd>ASIL-D</dd>
    </div>
  </dl>
  <div class="fire-entry__body">…</div>
</section>
```

Each stylesheet in `stylesheets` cascades after the built-in `base.css`, so you
override only what you need:

```css
.fire-entry[data-doc-type="sysreq"] .fire-entry__id {
  color: #003366;
}
.fire-field--sil[data-value="ASIL-D"] dd {
  color: #b00020;
  font-weight: 700;
}
```

The default stylesheet and template ship at
`@fire//fire/starlark:render/styles/base.css` and
`@fire//fire/starlark:render/templates/document.html.j2`; copy them as a starting
point and pass your versions via `stylesheets` or `template`.

### Prerequisites

Rendering uses [WeasyPrint](https://weasyprint.org/), which loads native
libraries (pango, cairo, harfbuzz) and fonts from the host. The Python package
is provided by Bazel, but the native libraries and fonts must be installed
separately. On Debian/Ubuntu:

```bash
sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
  libgdk-pixbuf-2.0-0 libharfbuzz0b libffi-dev fonts-dejavu-core
```

On macOS: `brew install pango` (and a font package such as
`font-dejavu`). When the libraries or fonts are missing, the build fails with
an actionable message rather than producing a partial PDF.

### Known limitation: PDF rendering via Bazel on macOS

Building a `document_pdf` target with `bazel` on macOS currently fails to find
the Homebrew native libraries even when they are installed. macOS System
Integrity Protection strips `DYLD_*` variables from the build action's
environment, so the dynamic loader cannot locate `/opt/homebrew/lib`. Render on
Linux (this is what CI uses); macOS rendering through Bazel is not yet
supported.
