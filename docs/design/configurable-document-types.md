# Design: Configurable Document Types for FIRE (Issue #224)

## Context

FIRE currently hardcodes three document types (`.sysreq.md`, `.swreq.md`, `.regreq.md`)
with validation rules embedded in Python Pydantic models. Systems engineering teams need
many more document types (`.handbook.md`, `.ipsra.md`, `.opman.md`, etc.) each with
different mandatory/optional fields. The issue asks for a consumer-configurable system
where document formats are defined in YAML, validated by FIRE tooling via Bazel, and
auto-generated into a FORMAT_SPECIFICATION.md usable as LLM context.

## Design: YAML Config Schema

A `fire_config.yaml` in the consumer's repo defines field types and document types:

```yaml
fire_config_version: 1

field_definitions:
  sil:
    display_name: "SIL"
    type: enum
    values:
      [
        "ASIL-A",
        "ASIL-B",
        "ASIL-C",
        "ASIL-D",
        "SIL-1",
        "SIL-2",
        "SIL-3",
        "SIL-4",
        "DAL-A",
        "DAL-B",
        "DAL-C",
        "DAL-D",
        "DAL-E",
        "QM",
      ]
    allow_todo: true
    description: "Safety Integrity Level (ISO 26262, IEC 61508, DO-178C/DO-254, QM)"

  sec:
    display_name: "Sec"
    type: bool
    allow_todo: true
    description: "Security relevance flag"

  version:
    display_name: "Version"
    type: int
    min_value: 1
    allow_todo: false
    description: "Requirement version, positive integer >= 1"

  parent:
    display_name: "Parent"
    type: parent_link
    allow_todo: true
    allow_multiple: true
    description: "Markdown link(s) to parent requirement(s)"

document_types:
  sysreq:
    suffix: ".sysreq.md"
    display_name: "System Requirement"
    description: "High-level system requirements"
    required_fields: [sil, sec, version]
    optional_fields: [parent]

  swreq:
    suffix: ".swreq.md"
    display_name: "Software Requirement"
    description: "Implementation-level software requirements"
    required_fields: [sil, sec, version]
    optional_fields: [parent]

  regreq:
    suffix: ".regreq.md"
    display_name: "Regulatory Requirement"
    description: "Regulatory obligations (SIL/Sec optional)"
    required_fields: [version]
    optional_fields: [sil, sec, parent]
```

Consumers extend this by adding their own types:

```yaml
handbook:
  suffix: ".handbook.md"
  display_name: "Handbook Entry"
  description: "Operational handbook entries"
  required_fields: [version]
  optional_fields: []
```

## Key Architectural Decisions

- **`field_definitions`** are reusable across document types (sil is identical for sysreq and swreq)
- **Field types**: `enum`, `bool`, `int`, `parent_link` — matching existing Pydantic validators. Extensible later with `string`, `float`, `regex`
- **Default config** ships with FIRE and matches current hardcoded behavior — backwards compatible with no consumer config
- **Dynamic Pydantic models** built at runtime from config, preserving error reporting quality and `extra: "forbid"` behavior

## Files to Create

| File                                              | Purpose                                                                                                                  |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `fire/starlark/config_models.py`                  | Pydantic models for config schema (`FireConfig`, `FieldDefinition`, `DocumentType`) + `load_config()` + embedded default |
| `fire/starlark/config_models_test.py`             | Tests for config parsing and validation                                                                                  |
| `fire/starlark/dynamic_requirement_model.py`      | Factory: config -> Pydantic BaseModel subclass at runtime                                                                |
| `fire/starlark/dynamic_requirement_model_test.py` | Tests proving dynamic models match static ones                                                                           |
| `fire/starlark/default_fire_config.yaml`          | Default config file shipped with FIRE                                                                                    |
| `fire/starlark/generate_format_spec.py`           | Reads config, produces FORMAT_SPECIFICATION.md                                                                           |
| `fire/starlark/generate_format_spec_test.py`      | Tests for spec generation                                                                                                |
| `fire/starlark/format_spec.bzl`                   | Bazel rule `generate_format_specification()`                                                                             |

## Files to Modify

| File                                         | Change                                                                                   |
| -------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `fire/starlark/validate_cross_references.py` | `_metadata_model_for_file()` -> config-driven suffix lookup; `main()` accepts `--config` |
| `fire/starlark/requirements.bzl`             | `requirement_library()` gains optional `config` attr, passed to Python script            |
| `fire/starlark/release_report.py`            | `main()` accepts `--config`; passes to metadata parsing                                  |
| `fire/starlark/reports.bzl`                  | `release_report` rule gains optional `config` attr                                       |
| `fire/starlark/BUILD.bazel`                  | New build targets for new files                                                          |
| `FORMAT_SPECIFICATION.md`                    | Replaced by auto-generated output                                                        |

## Bazel Integration

```text
fire_config.yaml ─┬──> requirement_library(config=":fire_config")
                   │        └─> validate_cross_references.py --config fire_config.yaml
                   │
                   ├──> release_report(config=":fire_config")
                   │        └─> release_report.py --config fire_config.yaml
                   │
                   └──> generate_format_specification(config=":fire_config", out="FORMAT_SPEC.md")
                            └─> generate_format_spec.py --config fire_config.yaml
```

Config is `attr.label(allow_single_file=[".yaml",".yml"], default=None)`. When None, Python scripts use the embedded default.

## Implementation Phases

### Phase 1: Config Models (no behavior change)

1. Create `config_models.py` with Pydantic models for config schema
2. Create `default_fire_config.yaml` matching current behavior
3. Add `load_config()` that loads YAML or returns default
4. Tests: config parses correctly, invalid configs rejected

### Phase 2: Dynamic Model Factory (no behavior change)

1. Create `dynamic_requirement_model.py` — builds Pydantic model from config
2. Tests: dynamic models produce identical validation to static `RequirementMetadata` and `RegulatoryRequirementMetadata` for all existing test cases

### Phase 3: Wire Config into Validation

1. Modify `validate_cross_references.py`: config-driven `_metadata_model_for_file()` and `--config` arg
2. Modify `requirements.bzl`: optional `config` attr
3. Modify `release_report.py` and `reports.bzl`: optional `config` attr
4. Tests: existing tests still pass, new test with custom document type

### Phase 4: Format Specification Generator

1. Create `generate_format_spec.py` and `format_spec.bzl`
2. Replace hand-written `FORMAT_SPECIFICATION.md` with auto-generated output
3. Tests: generated output covers all document types and fields

### Phase 5: Documentation and Examples

1. Update README.md with config section
2. Add example with custom document type

## Verification

- All existing tests pass unchanged (backwards compatibility)
- New unit tests for config parsing, dynamic model generation, format spec generation
- Integration test: add custom document type to `integration_test/`, validate it works end-to-end
- Verify generated FORMAT_SPECIFICATION.md is equivalent to current hand-written one
