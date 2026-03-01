# FIRE Format Specification

This document specifies the format for all input files used in the FIRE requirements management system.

**Version:** 0.4.0
**Last Updated:** 2026-03-01

## Table of Contents

1. [System Requirements (`.sysreq.md`)](#system-requirements-sysreqmd)
2. [Software Requirements (`.swreq.md`)](#software-requirements-swreqmd)
3. [Parameter Files (`.yaml`)](#parameter-files-yaml)
4. [Cross-References](#cross-references)
5. [Validation Rules](#validation-rules)

---

## System Requirements (`.sysreq.md`)

System requirements are stored in Markdown files with the `.sysreq.md` extension. These define high-level requirements for the system.

### File Structure

```markdown
# <Document Title>

## <REQ-ID>

<Metadata Line>

<Requirement Description>

### <Optional Subsections>

---
```

### Requirement Format

Each requirement consists of:

1. **Requirement ID** (H2 heading): `## REQ-ID`
2. **Metadata line**: `SIL: <value> | Sec: <value> | Version: <value>`
3. **Requirement text**: One or more paragraphs describing the requirement
4. **Optional subsections**: Rationale, Acceptance Criteria, Verification, etc.
5. **Separator**: `---` (three hyphens)

### Metadata Fields

The metadata line format for system requirements:

```text
SIL: <sil-value> | Sec: <sec-value> | Version: <version>
```

Optional parent field for hierarchical system requirements:

```text
SIL: <sil-value> | Sec: <sec-value> | Version: <version> | Parent: <parent-ref>
```

Fields must be separated by `|` (space-pipe-space).

#### `SIL` Field

**Type:** Safety Integrity Level
**Required:** Yes
**Valid Values:**

- **ISO 26262 (Automotive):** `ASIL-A`, `ASIL-B`, `ASIL-C`, `ASIL-D`
- **IEC 61508 (General):** `SIL-1`, `SIL-2`, `SIL-3`, `SIL-4`
- **DO-178C/DO-254 (Aviation):** `DAL-A`, `DAL-B`, `DAL-C`, `DAL-D`, `DAL-E`
- **Quality Management:** `QM`
- **TODO Placeholder:** `TODO(TICKET-ID)` where TICKET-ID matches `[A-Z]+-[0-9]+`

**Examples:**

```text
SIL: ASIL-D
SIL: SIL-3
SIL: DAL-A
SIL: QM
SIL: TODO(BRK-789)
```

#### `Sec` Field

**Type:** Security-relevant
**Required:** Yes
**Valid Values:** `true`, `false`, or `TODO(TICKET-ID)`

**Examples:**

```text
Sec: true
Sec: false
Sec: TODO(SEC-456)
```

#### `Version` Field

**Type:** Integer
**Required:** Yes
**Valid Values:** Positive integer ≥ 1
**Format:** Plain integer (no quotes, no decimals)

**Examples:**

```text
Version: 1
Version: 42
```

**Invalid:**

```text
Version: "1"    # Quoted
Version: 1.0    # Decimal
Version: 0      # Must be ≥ 1
```

#### `Parent` Field (Optional)

**Type:** Markdown link(s) to parent requirement(s)
**Required:** No (optional for system requirements, commonly used for software requirements)
**Format:**

- Single parent: `Parent: [REQ-ID](/path/to/file.sysreq.md?version=N#REQ-ID)`
- Multiple parents: Multi-line with `|` continuation

The parent field can be used to create hierarchical relationships between requirements. It's optional for system requirements but commonly used in software requirements to trace back to system requirements.

Each parent link must:

- Be a Markdown link: `[text](url)`
- Use a repository-relative path (starting with `/`)
- Include version query parameter: `?version=N`
- Include anchor to requirement ID: `#REQ-ID`

**Single Parent Example:**

```text
SIL: ASIL-D | Sec: false | Version: 1 | Parent: [REQ-SYS-001](/requirements/system.sysreq.md?version=1#REQ-SYS-001)
```

**Multiple Parents Example (Multi-line):**

```text
SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-SYS-001](/requirements/system.sysreq.md?version=1#REQ-SYS-001) |
Parent: [REQ-SYS-002](/requirements/system.sysreq.md?version=2#REQ-SYS-002)
```

**Multi-line Format Rules:**

- Each line must end with `|` to indicate continuation to the next line
- The trailing `|` on the last metadata line is optional but recommended for consistency
- Empty lines between metadata lines will break the continuation
- Each `Parent:` entry must be a valid markdown link or `TODO(KEY-1234)` placeholder

**Use Cases for Multiple Parents:**

Multiple parents are useful when a software requirement implements or derives from multiple system requirements. For example:

```text
## REQ-COLLISION-AVOIDANCE

SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-BRK-001](/requirements/braking.sysreq.md?version=4#REQ-BRK-001) |
Parent: [REQ-SENS-003](/requirements/sensing.sysreq.md?version=2#REQ-SENS-003)

The collision avoidance system shall combine emergency braking capabilities
with sensor fusion to prevent accidents.
```

**TODO Placeholder:**

```text
Parent: TODO(LINK-123)
```

### Requirement ID Format

**Pattern:** `^[A-Z][A-Z0-9_-]+$`

- Must start with an uppercase letter
- May contain uppercase letters, digits, underscores, and hyphens
- No lowercase letters allowed

**Valid Examples:**

```text
REQ-BRK-001
REQ_ALPHA_001
SYS-MAIN-CONFIG
R1
```

**Invalid Examples:**

```text
req-brk-001     # Lowercase
REQ_brk_001     # Mixed case
1REQ-001        # Starts with digit
```

### Optional Subsections

Common subsections (all optional):

- **Rationale**: Why the requirement exists
- **Acceptance Criteria**: How to verify compliance
- **Verification**: Testing approach
- **Dependencies**: Related requirements
- **Test Data**: Expected test inputs/outputs
- **Changelog**: Version history
- **Reference-Style Link Definitions**: Markdown link references

### Complete Example

```markdown
# Braking System Requirements

## REQ-BRK-001

SIL: ASIL-D | Sec: true | Version: 4

**Emergency Braking Distance**

The vehicle SHALL be capable of performing emergency braking from any velocity up to
maximum design velocity (see [REQ-VEL-001][1]),
achieving deceleration according to [@braking_distance_table][2] parameters.

### Rationale

Emergency braking performance is critical for collision avoidance and overall vehicle safety.

### Acceptance Criteria

For each velocity and friction coefficient pair in [@braking_distance_table]:

1. Vehicle SHALL achieve full stop within specified distance ±5%
2. Deceleration SHALL be smooth and controlled (no wheel lock)

### Verification

Testing performed on the following aspects:

- Brake dynamometer testing
- Proving ground testing on various surfaces

TODO(BRK-456) Complete ice surface testing for all velocity ranges

### Reference-Style Link Definitions

[1]: /examples/requirements/velocity_requirements.sysreq.md?version=2#REQ-VEL-001
[2]: /examples/vehicle_params.yaml?version=1#braking_distance_table
[@braking_distance_table]: /examples/vehicle_params.yaml?version=1#braking_distance_table

---
```

---

## Software Requirements (`.swreq.md`)

Software requirements are stored in Markdown files with the `.swreq.md` extension. These define implementation-level requirements for software components.

### File Structure

Software requirement files follow the same structure as system requirements. The `Parent` field is typically included to trace software requirements back to their system requirements.

### Metadata Fields

Software requirements extend the system requirement metadata format:

```text
SIL: <sil-value> | Sec: <sec-value> | Version: <version> | Parent: <parent-ref>
```

#### `Parent` Field

**Type:** Markdown link(s) to parent requirement(s)
**Required:** No (but strongly recommended for traceability to system requirements)
**Format:**

- Single parent: `Parent: [REQ-ID](/path/to/file.sysreq.md?version=N#REQ-ID)`
- Multiple parents: Multi-line with `|` continuation (see System Requirements section)

Software requirements typically include one or more parents to trace back to system requirements. When a software requirement implements or derives
from multiple system requirements, use the multi-line format with multiple Parent entries.

Each parent link must:

- Be a Markdown link: `[text](url)`
- Use a repository-relative path (starting with `/`)
- Include version query parameter: `?version=N`
- Include anchor to requirement ID: `#REQ-ID`

**Valid Examples:**

```text
Parent: [REQ-BRK-001](/examples/requirements/braking_requirements.sysreq.md?version=4#REQ-BRK-001)
Parent: [REQ-VEL-001](/requirements/velocity.sysreq.md?version=1#REQ-VEL-001)
Parent: TODO(LINK-123)
```

**Multiple Parents (Multi-line):**

```text
SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-BRK-001](/requirements/braking_requirements.sysreq.md?version=4#REQ-BRK-001) |
Parent: [REQ-VEL-001](/requirements/velocity.sysreq.md?version=1#REQ-VEL-001)
```

**Invalid Examples:**

```text
Parent: REQ-BRK-001                                    # Not a link
Parent: [REQ-BRK-001](braking_requirements.md)         # Relative path
Parent: [REQ-BRK-001](/requirements/braking.md#REQ-BRK-001)  # Missing version
```

### Complete Example

```markdown
# Software Requirements: Brake Actuator Component

This document contains the software requirements for the Brake Actuator component.

## REQ_BA_RECEIVE_COMMANDS

SIL: ASIL-D | Sec: false | Version: 1 | Parent: [REQ-BRK-001](/examples/requirements/braking_requirements.sysreq.md?version=4#REQ-BRK-001)

The brake actuator component shall subscribe to brake force commands at a rate of 50 Hz
and process each received command within 2 milliseconds. Each command contains brake force
as a percentage [0, 100], a timestamp, and a status field.

---

## REQ_BA_CONTROL_HYDRAULICS

SIL: ASIL-D | Sec: false | Version: 1 | Parent: [REQ-BRK-001](/examples/requirements/braking_requirements.sysreq.md?version=4#REQ-BRK-001)

The brake actuator component shall control the electro-hydraulic valve using a PI
(Proportional-Integral) controller running at 1000 Hz to maintain actual hydraulic
pressure within 1 bar of the target pressure.

---

## REQ_BA_EMERGENCY_BRAKE_FUSION

SIL: ASIL-D | Sec: false | Version: 1 |
Parent: [REQ-BRK-001](/examples/requirements/braking_requirements.sysreq.md?version=4#REQ-BRK-001) |
Parent: [REQ-SENS-003](/examples/requirements/sensing_requirements.sysreq.md?version=2#REQ-SENS-003)

The brake actuator component shall integrate emergency braking commands with sensor
fusion data to optimize braking performance based on detected road conditions and
obstacle proximity. This requirement derives from both the braking system requirement
and the sensing system requirement.

---
```

---

## Parameter Files (`.yaml`)

Parameter files are YAML documents that define typed parameters with units and descriptions. Parameters are versioned and can be referenced from requirements.

### File Structure

```yaml
<param_name>_v<version>:
  value: <value>
  unit: <unit>
  description: <description>

<table_param>_v<version>:
  type: table
  description: <description>
  columns:
    - name: <column_name>
      unit: <unit>
    - name: <column_name>
      unit: <unit>
  rows:
    - [<value>, <value>]
    - [<value>, <value>]
```

### Parameter Naming

**Pattern:** `^[a-z][a-z0-9_]*_v[1-9][0-9]*$`

- Parameter name must be lowercase snake_case
- Must end with version suffix: `_v<N>` where N ≥ 1
- No uppercase letters allowed

**Valid Examples:**

```yaml
max_speed_v1:
wheel_radius_v2:
braking_distance_table_v1:
```

**Invalid Examples:**

```yaml
maxSpeed_v1: # camelCase not allowed
MAX_SPEED_v1: # Uppercase not allowed
max_speed: # Missing version suffix
max_speed_v0: # Version must be ≥ 1
max_speed_version1: # Must use _vN format
```

### Version Constraints

- A parameter can have at most **2 versions** (e.g., `_v1` and `_v2`)
- Versions must be **consecutive** (no gaps)
- If multiple versions exist, they must be `_v1, _v2` or `_v2, _v3`, etc.

**Valid:**

```yaml
max_speed_v1:
  value: 30.0
  unit: m/s
  description: Maximum speed

max_speed_v2:
  value: 35.0
  unit: m/s
  description: Maximum speed (updated)
```

**Invalid:**

```yaml
max_speed_v1:
  value: 30.0
  unit: m/s
  description: Maximum speed

max_speed_v3: # Error: Gap in versions (missing v2)
  value: 35.0
  unit: m/s
  description: Maximum speed
```

```yaml
max_speed_v1:
  value: 30.0
  unit: m/s
  description: Maximum speed

max_speed_v2:
  value: 32.0
  unit: m/s
  description: Maximum speed

max_speed_v3: # Error: More than 2 versions
  value: 35.0
  unit: m/s
  description: Maximum speed
```

### Scalar Parameters

Scalar parameters have a single value with a type, unit, and description.

#### Type Inference

**Types are automatically inferred from values. Do NOT include a `type` field for scalar parameters.**

Type inference rules:

- `bool` values → `bool` type
- `int` values → `i64` type (64-bit signed integer)
- `float` values → `f64` type (64-bit floating point)
- `str` values → `string` type

**Important:** YAML interprets numbers without decimal points as integers. Use `.0` suffix for floats.

#### Required Fields

- `value`: The parameter value (bool, int, float, or string)
- `unit`: Unit of measurement (string, min length 1)
- `description`: Human-readable description (string, min length 1)

#### Examples

```yaml
# Boolean parameter
enable_abs_v1:
  value: true
  unit: bool
  description: Enable anti-lock braking system

# Integer parameter
wheel_count_v1:
  value: 4
  unit: count
  description: Number of wheels

# Float parameter
max_speed_v1:
  value: 30.0
  unit: m/s
  description: Maximum allowed speed in m/s

# String parameter
vehicle_model_v1:
  value: "Sedan-XL"
  unit: model_code
  description: Vehicle model identifier
```

### Table Parameters

Table parameters contain tabular data with typed columns.

#### Required Fields

- `type`: Must be exactly `"table"`
- `description`: Human-readable description (string, min length 1)
- `columns`: List of column definitions (min length 1)
- `rows`: List of data rows (min length 1)

#### Column Definition

Each column must have:

- `name`: Column name (lowercase snake*case matching `^[a-z]a-z0-9*]\*$`)
- `unit`: Unit of measurement (string, min length 1)

**Column types are inferred from the first row. Do NOT include a `type` field in column definitions.**

#### Type Consistency

All values in a column must have the same type:

- The type is inferred from the **first row**
- All subsequent rows must match that type
- Type mismatches will cause validation errors

#### Example

```yaml
braking_distance_table_v1:
  type: table
  description: Required braking distances by velocity and friction coefficient
  columns:
    - name: velocity
      unit: m/s
    - name: friction_coeff
      unit: "1"
    - name: braking_distance
      unit: m
  rows:
    - [10.0, 0.7, 5.2]
    - [20.0, 0.7, 15.8]
    - [30.0, 0.7, 31.4]
    - [10.0, 0.3, 12.1]
    - [20.0, 0.3, 36.7]
```

**Type inference from first row:**

- `velocity`: `10.0` is float → column type is `f64`
- `friction_coeff`: `0.7` is float → column type is `f64`
- `braking_distance`: `5.2` is float → column type is `f64`

**Invalid example (type mismatch):**

```yaml
braking_distance_table_v1:
  type: table
  description: Braking distances
  columns:
    - name: velocity
      unit: m/s
  rows:
    - [10.0] # First row: float type inferred
    - [20] # Error: int doesn't match float type from first row
```

---

## Cross-References

FIRE supports cross-references between requirements and parameters using Markdown link syntax.

### Requirement-to-Requirement References

**Format:** `[REQ-ID](/path/to/file.sysreq.md?version=N#REQ-ID)`

**Components:**

- Link text: Requirement ID
- Path: Repository-relative path (starts with `/`)
- Query parameter: `?version=N` specifying the requirement version
- Anchor: `#REQ-ID` pointing to the requirement heading

**Example:**

```markdown
The braking system (see [REQ-BRK-001](/requirements/braking.sysreq.md?version=4#REQ-BRK-001))
shall activate within 100ms.
```

### Requirement-to-Parameter References

**Format:** `[@param_name](/path/to/params.yaml?version=N#param_name)`

**Components:**

- Link text: `@` prefix + parameter name (without version suffix)
- Path: Repository-relative path to YAML file
- Query parameter: `?version=N` specifying the parameter version
- Anchor: `#param_name` (base name without version suffix)

**Example:**

```markdown
The vehicle shall not exceed the maximum speed defined in
[@max_speed](/examples/params.yaml?version=1#max_speed).
```

### Reference-Style Links

Markdown reference-style links are supported:

```markdown
The vehicle shall brake within [@braking_distance][1] when traveling at [REQ-VEL-001][2].

### Reference-Style Link Definitions

[1]: /examples/params.yaml?version=1#braking_distance
[2]: /requirements/velocity.sysreq.md?version=2#REQ-VEL-001
```

### TODO Placeholders

Incomplete references can use TODO placeholders:

**Pattern:** `TODO(TICKET-ID)` where TICKET-ID matches `[A-Z]+-[0-9]+`

**Example:**

```markdown
SIL: TODO(REQ-123) | Sec: TODO(SEC-456) | Version: 1

SIL: ASIL-D | Sec: true | Version: 1 | Parent: TODO(LINK-456)
```

---

## Validation Rules

### Requirement Files (`.sysreq.md`, `.swreq.md`)

1. **Requirement ID:**
   - Must match pattern `^[A-Z][A-Z0-9_-]+$`
   - Must be unique within the file
   - Used as H2 heading (`## REQ-ID`)

2. **Metadata Line:**
   - Must be the first line(s) after the requirement ID heading
   - Fields separated by `|` (space-pipe-space)
   - Required fields: SIL, Sec, Version
   - Optional field: Parent (recommended for software requirements to trace to system requirements)
   - Supports multi-line format: lines ending with `|` continue to next line
   - Empty lines break multi-line continuation

3. **SIL Values:**
   - Must be one of the predefined values or `TODO(TICKET-ID)`
   - Case-sensitive (e.g., `ASIL-D`, not `asil-d`)

4. **Sec Values:**
   - Must be boolean (`true` or `false`) or `TODO(TICKET-ID)`
   - Case-sensitive

5. **Version:**
   - Must be positive integer ≥ 1
   - Must be unquoted in metadata line

6. **Parent References:**
   - Can specify single or multiple parents
   - Each parent must be Markdown link format
   - Must use repository-relative paths (start with `/`)
   - Must include `?version=N` query parameter
   - Must include `#REQ-ID` anchor
   - Multiple parents use multi-line format with separate `Parent:` entries

### Parameter Files (`.yaml`)

1. **Parameter Names:**
   - Must match pattern `^[a-z][a-z0-9_]*_v[1-9][0-9]*$`
   - Must be lowercase snake_case with version suffix
   - Must be unique within the file

2. **Versioning:**
   - Maximum 2 versions per parameter
   - Versions must be consecutive (no gaps)
   - Version numbers must be ≥ 1

3. **Scalar Parameters:**
   - Must NOT include `type` field (types are inferred)
   - Must include `value`, `unit`, `description`
   - Value type determines parameter type

4. **Table Parameters:**
   - Must include `type: table`
   - Must include `description`, `columns`, `rows`
   - Column names must match `^[a-z][a-z0-9_]*$`
   - Must NOT include `type` field in column definitions
   - All values in a column must have the same type
   - Column types inferred from first row

5. **Type Inference:**
   - `bool` (checked before `int` due to Python inheritance)
   - `int` → `i64`
   - `float` → `f64`
   - `str` → `string`

### Cross-References

1. **Requirement References:**
   - Must use repository-relative paths
   - Must include version query parameter
   - Must include anchor to requirement ID

2. **Parameter References:**
   - Link text must use `@param_name` format
   - Anchor must use base name (no version suffix)
   - Version specified in query parameter

3. **TODO Placeholders:**
   - Must match pattern `TODO([A-Z]+-[0-9]+)`
   - Can be used for SIL, Sec, Parent, or inline references

---

## Common Patterns

### Evolving Requirements

When a requirement changes semantically in a way that requires downstream consumers to review their work, increment the version to signal the change:

**Before:**

```markdown
## REQ-TRAFFIC-001

SIL: ASIL-B | Sec: false | Version: 1

At uncontrolled intersections, the vehicle shall yield according to first-come-first-serve rules.
```

**After:**

```markdown
## REQ-TRAFFIC-001

SIL: ASIL-B | Sec: false | Version: 2

At uncontrolled intersections, the vehicle shall yield to traffic approaching from the right.

### Changelog

- **Version 2**: Changed from first-come-first-serve to right-of-way rule (left yields to right)
- **Version 1**: Initial requirement with first-come-first-serve rule
```

References must update to point to the new version:

```markdown
[REQ-TRAFFIC-001](/requirements/traffic.sysreq.md?version=2#REQ-TRAFFIC-001)
```

### Evolving Parameters

When a parameter changes in a way that requires downstream consumers to review their work, create a new version to signal the change:

```yaml
max_speed_v1:
  value: 30.0
  unit: m/s
  description: Maximum allowed speed

max_speed_v2:
  value: 35.0
  unit: m/s
  description: Maximum allowed speed (increased limit)
```

Requirements should specify which version they reference:

```markdown
[@max_speed](/params.yaml?version=2#max_speed)
```

### Incremental Development with TODOs

Use TODO placeholders during development:

```markdown
## REQ-NEW-001

SIL: TODO(REQ-123) | Sec: TODO(SEC-456) | Version: 1

The system shall implement feature X according to [@config](<TODO(PARAM-789)>).
```

Replace TODOs with actual values as they become available.

---

## Anti-Patterns

### ❌ Incorrect: Uppercase in parameter names

```yaml
MaxSpeed_v1: # Wrong: uppercase not allowed
  value: 30.0
```

### ❌ Incorrect: Explicit type in scalar parameters

```yaml
max_speed_v1:
  type: f64 # Wrong: type is inferred from value
  value: 30.0
  unit: m/s
```

### ❌ Incorrect: Explicit type in table columns

```yaml
braking_table_v1:
  type: table
  columns:
    - name: velocity
      type: f64 # Wrong: type is inferred from first row
      unit: m/s
```

### ❌ Incorrect: Missing version in cross-reference

```markdown
See [REQ-VEL-001](/requirements/velocity.sysreq.md#REQ-VEL-001)
```

Should include `?version=N`:

```markdown
See [REQ-VEL-001](/requirements/velocity.sysreq.md?version=2#REQ-VEL-001)
```

### ❌ Incorrect: Relative path in cross-reference

```markdown
Parent: [REQ-BRK-001](../requirements/braking.sysreq.md?version=1#REQ-BRK-001)
```

Must use repository-relative path (starts with `/`):

```markdown
Parent: [REQ-BRK-001](/requirements/braking.sysreq.md?version=1#REQ-BRK-001)
```

### ❌ Incorrect: Gap in parameter versions

```yaml
max_speed_v1:
  value: 30.0
  unit: m/s
  description: Speed

max_speed_v3: # Wrong: missing v2
  value: 35.0
  unit: m/s
  description: Speed
```

### ❌ Incorrect: More than 2 parameter versions

```yaml
max_speed_v1:
  value: 30.0
max_speed_v2:
  value: 32.0
max_speed_v3: # Wrong: more than 2 versions
  value: 35.0
```

---

## Implementation References

This specification is enforced by the FIRE validation tools:

- **Requirement validation:** `fire/starlark/requirement_models.py`
- **Parameter validation:** `fire/starlark/parameter_models.py`
- **Pattern definitions:** `fire/starlark/patterns.py`
- **Cross-reference validation:** `fire/starlark/validate_cross_references.py`

For questions or clarifications, please refer to the source code or open an issue.
