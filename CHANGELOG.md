# Changelog

All notable changes to FIRE are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Releases up to and including 0.6.1 are described in the
[GitHub releases](https://github.com/nesono/fire/releases).

## [Unreleased]

### Breaking changes

Validation is stricter. Projects that built with 0.6.1 can fail with these
changes; each entry says what to change.

- Every H2 heading in a requirement file must be exactly a requirement ID
  (`[A-Z][A-Z0-9_-]+`). Headings such as `## Overview` or `## REQ-1 Title` fail
  validation, because they used to be skipped silently, together with their
  metadata. Use H3 or deeper for structure, and a bold line after the metadata
  for the title. Headings inside fenced code blocks are ignored. (#309)
- Requirement IDs must be unique: among the files of one `requirement_library`
  (validation fails), and among all requirement files of one `release_report`
  (the report is `NOT READY FOR RELEASE`). (#314)
- A parameter reference must name a parameter and a version that the parameter
  file declares, matched by the exact key `<name>_v<N>`. Before, `@speed`
  matched `max_speed_v1`, commented-out keys counted, and a version that is not
  in the file only produced a warning. A reference to an older version that is
  still declared still only warns. (#311)
- Every row of a table parameter must have exactly one value per column. (#316)
- Floating-point parameter values must be finite; `.inf` and `.nan` are
  rejected for scalars and table cells. (#318)
- Parameter units may only contain letters, digits, `/`, `^`, `*`, `·`, `-`,
  spaces, parentheses, and the symbols `°`, `%`, `‰`, `²`, `³`, `µ`, `Ω`. Other
  characters fail validation. Two different parameters, or two table columns,
  that generate the same identifier also fail, for example `speed` in `m` and
  `speed_m` without a unit. (#326)
- The release report requires the coverage that each document type declares
  instead of an implementing and a verifying trace for every requirement. With
  the built-in types, system requirements now need a child requirement (and no
  traces), and regulatory requirements need only a verifying trace. A custom
  `fire_config.yaml` that does not declare `coverage` for a type keeps the
  previous behavior for that type. The report section
  `Implementation & Verification Coverage` is now `Coverage`, and a new
  finding `Missing child requirements` can make the report
  `NOT READY FOR RELEASE`. (#352, #357)
- Python 3.10 is no longer supported. (#294)

### Added

- `coverage` in `fire_config.yaml` document types: a list of `child`,
  `implementation` and `verification` that the release report requires.
  `coverage: []` requires nothing. The release report lists the required
  coverage per document type, and the generated format specification states it.
  (#352, #357)
- Units are spelled out in generated identifiers: `°C` becomes `degc`, `%`
  becomes `percent`, `m/s²` becomes `mps2`, `µm` becomes `um`, `Ω` becomes
  `ohm`. Before, such units generated invalid code. (#326)
- Python 3.14 and 3.15 are supported. (#294)
- A [safety manual](docs/SAFETY_MANUAL.md) with the intended use, known
  limitations, and assumptions of use. (#308)

### Fixed

- Generated code escapes parameter text. String values and table string cells
  are escaped for each target language, and descriptions and units are
  flattened to one line in generated comments. Before, quotes, backslashes and
  line breaks produced invalid code in all five languages, and a line break in a
  description could inject code. (#320)
- The release workflow opens the Bazel Central Registry pull request against
  the upstream registry. (#291)

[Unreleased]: https://github.com/nesono/fire/compare/0.6.1...main
