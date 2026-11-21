# FIRE Safety Manual

This manual describes how FIRE may be used in the development of safety-related systems, which assumptions the user has to fulfil, and which limitations are known.
It applies to FIRE 0.6.1.

**FIRE is not a qualified tool.**
No tool confidence level has been assigned, no qualification has been performed, and no certificate exists.
This document gives you the information needed to perform the classification and qualification for your own project and safety standard.
Classification is a project-specific decision and stays with the user.

## Scope and Intended Use

FIRE is a Bazel module that:

1. Validates requirement documents (Markdown) and parameter files (YAML) at build time.
2. Checks cross-references between requirements, parameters, and source files, including their pinned versions.
3. Generates source code constants (C++, Python, Go, Rust, Java) from parameter files.
4. Produces a release readiness report and a pass/fail gate from the above.
5. Renders requirement documents as PDF and generates a format specification.

FIRE is intended to support review and release decisions by detecting inconsistencies automatically.
It is **not** intended to replace human review of requirements, review of generated code, or verification of the product.
Items 1-4 can influence safety-related artifacts (use cases UC-1 to UC-6 below).
Item 5 (PDF, format specification) only affects presentation.

## Tool Architecture

FIRE consists of Starlark rules and Python scripts that run as Bazel actions.
The Python scripts are located in `fire/starlark/`.

| Component                                       | Role                                                                |
| ----------------------------------------------- | ------------------------------------------------------------------- |
| `requirement_library`                           | Validates requirement files and their cross-references              |
| `parameter_library`                             | Validates parameter files and injects inferred types                |
| `generate_*_parameters`                         | Generates source code from validated parameters                     |
| `source_traceability`                           | Validates declared source-to-requirement links, emits `.trace.json` |
| `release_report`, `release_readiness_test`      | Aggregates all checks into a Markdown report and a pass/fail gate   |
| `document_pdf`, `generate_format_specification` | Presentation only                                                   |

Input files are trusted repository content.
FIRE does not defend against malicious input and does not sandbox the scripts that read the source tree (`source_traceability` runs without a sandbox).

## Use Cases and Failure Modes

The table lists malfunctions that could lead to an undetected defect in a safety-related work product.
It is the starting point for a tool impact analysis.

| ID   | Use case                          | Malfunction                                                        | Effect                                                       | Detected by FIRE itself?                                    | Limitation         |
| ---- | --------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------ | ----------------------------------------------------------- | ------------------ |
| UC-1 | Requirement metadata validation   | Invalid or missing metadata is accepted                            | Requirement with wrong SIL or version enters the baseline    | No, when the heading is not conformant                      | L-1                |
| UC-2 | Cross-reference validation        | Reference to a non-existent parameter or stale version is accepted | Requirement is linked to the wrong or an outdated item       | Partly; stale versions are only warnings at validation time | L-2, L-3           |
| UC-3 | Parameter validation              | Malformed table is accepted                                        | Generated code contains missing or surplus values            | Partly                                                      | L-8                |
| UC-4 | Code generation                   | Generated value or declaration deviates from the parameter file    | Product code uses a wrong constant                           | No; there is no check of the generated output               | L-9, L-10          |
| UC-5 | Source traceability               | A declared link is wrong, or does not reflect the code             | Requirement appears implemented or verified without being so | No                                                          | L-6, L-7           |
| UC-6 | Release readiness report and gate | The report omits a requirement, or reports a duplicate ID as one   | "READY FOR RELEASE" although evidence is missing             | No                                                          | L-1, L-4, L-5, L-7 |

## Checks Performed

| Check                                                                                           | Where                            | Result on violation                                           |
| ----------------------------------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------- |
| Required metadata fields and value ranges per document type (`SIL`, `Sec`, `Version`, `Parent`) | `validate_cross_references.py`   | Build fails                                                   |
| Every `TODO` uses the form `TODO(KEY-1234)`                                                     | `validate_cross_references.py`   | Build fails                                                   |
| References use repository-relative paths and a `?version=N` query                               | `validate_cross_references.py`   | Build fails                                                   |
| Referenced requirement file exists and contains the referenced ID                               | `validate_cross_references.py`   | Build fails                                                   |
| Referenced requirement is in the declared `deps`                                                | `validate_cross_references.py`   | Build fails                                                   |
| Referenced version is older than the current requirement or parameter version                   | `validate_cross_references.py`   | Warning only                                                  |
| Parameter keys follow `<name>_v<N>`, versions are consecutive, at most two versions coexist     | `parameter_models.py`            | Build fails                                                   |
| Scalar types are inferred from the value; table column types are consistent across rows         | `parameter_models.py`            | Build fails                                                   |
| `implements` and `verifies` reference existing requirement IDs and carry `?version=`            | `extract_source_traceability.py` | Build fails                                                   |
| Trace version is ahead of the requirement version                                               | `extract_source_traceability.py` | Build fails                                                   |
| Trace version is behind the requirement version                                                 | `extract_source_traceability.py` | Warning (`OUTDATED`), reported as stale in the release report |
| Stale requirement, parameter, and trace versions                                                | `release_report.py`              | `NOT READY FOR RELEASE`                                       |
| Open `TODO(KEY-1234)` items                                                                     | `release_report.py`              | `NOT READY FOR RELEASE`                                       |
| Each requirement has at least one implementing and one verifying trace                          | `release_report.py`              | `NOT READY FOR RELEASE`                                       |

## Checks Not Performed

FIRE does **not** check that:

- A requirement is correct, complete, unambiguous, or testable.
- The text of a requirement is unchanged since its version was last incremented.
  Whether a change is semantic and requires a version increment is a manual decision.
- A source or test file listed in `implements` or `verifies` exists, contains the claimed implementation, or passes.
- The set of requirement files passed to `release_report` is the complete set of requirements of the product.
- Requirement IDs are unique across files.
- Generated code compiles, is correct for the target language, or matches the parameter file.
- The `SIL` of a child requirement is consistent with its parent.
- The parameter `unit` is physically meaningful or consistent between a requirement text and the parameter.

## Known Limitations

Each limitation was either reproduced with the FIRE scripts at the time of writing or derived from reading the code.
The Evidence column states which.
All Python scripts were run with Python 3.14.

| ID   | Limitation                                                                                                                                                                                                                                                                                                                                     | Evidence                                                       | Direction                                            |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------- |
| L-1  | **Non-conformant requirement headings are silently skipped.** Only headings that match `## [A-Z][A-Z0-9_-]+` exactly are treated as requirements. A heading such as `## req-lower-002` or `## REQ-TITLE-003 Braking distance` is neither validated nor listed in the release report, even with invalid or missing metadata.                    | Reproduced                                                     | Unsafe (false pass)                                  |
| L-2  | **Parameter reference existence is checked by text search.** The check looks for the string `<name>_v<N>:` anywhere in the file. A reference `[@speed](…#speed)` passes if the file defines `max_speed_v1`, and so does a key that is commented out. A reference to a version older than the oldest version in the file passes with a warning. | Reproduced (suffix match), code review (comments, old version) | Unsafe (false pass)                                  |
| L-3  | **Stale references are warnings during validation.** The `requirement_library` build prints `WARNING: REQUIREMENT VERSION MISMATCH` and succeeds. The stale reference only fails the build through the release readiness test.                                                                                                                 | Reproduced                                                     | Depends on gate being used                           |
| L-4  | **Duplicate requirement IDs are not detected.** Two files with the same ID are both validated. The report lists both and keeps one version (the last one read) for staleness checks. Coverage is evaluated per ID, so a trace for one counts for both.                                                                                         | Reproduced (not detected), code review (version, coverage)     | Unsafe (false pass)                                  |
| L-5  | **The release gate matches report text.** `release_readiness_test` fails if the report contains `NOT READY FOR RELEASE` anywhere, including in the product name. A report without any status line also fails.                                                                                                                                  | Reproduced                                                     | Safe (false fail)                                    |
| L-6  | **Traces are declarations.** The files named in `implements` and `verifies` are plain strings, not Bazel labels. Their existence, content, and test results are not checked, and changing them does not invalidate the trace.                                                                                                                  | Code review                                                    | Unsafe (false pass)                                  |
| L-7  | **Coverage is existence, not adequacy.** One implementing and one verifying trace per requirement ID is sufficient. Only the requirement files passed to `release_report` are assessed; a requirement file left out is absent from the report without a finding.                                                                               | Code review                                                    | Unsafe (false pass)                                  |
| L-8  | **Table shape is only partly validated.** A row with fewer values than the first row, and rows with more values than there are columns, are accepted. A row longer than the first row aborts validation with an `IndexError` traceback.                                                                                                        | Reproduced                                                     | Unsafe (false pass) / safe (abort)                   |
| L-9  | **Generated string literals and comments are not escaped.** A string value containing `"` or `\` produces invalid C++ and Rust. A description containing a line break ends the comment, and the remainder is emitted as code. Not tested for Python, Go, and Java, which use the same template approach.                                       | Reproduced (C++, Rust)                                         | Mostly safe (compile error), code injection possible |
| L-10 | **Non-finite floats are accepted.** `.inf` and `.nan` pass parameter validation and are emitted as the identifier `inf` or `nan`, which is not a valid literal in C++ or Rust.                                                                                                                                                                 | Reproduced                                                     | Safe (compile error)                                 |
| L-11 | **No tool requirements specification and no coverage metric.** Behavior is defined by README, source code, and tests. CI does not measure code coverage.                                                                                                                                                                                       | Code review                                                    | Qualification effort                                 |
| L-12 | **PDF rendering depends on the host.** WeasyPrint uses native libraries and fonts of the host. Building PDFs via Bazel is not supported on macOS (see README).                                                                                                                                                                                 | README                                                         | Presentation only                                    |

"Unsafe" means that a defect can pass undetected, "safe" means that FIRE fails or the product does not compile.

## Assumptions of Use

The user is responsible for the following.
A violated assumption can invalidate the confidence argument for FIRE.

| ID     | Assumption                                                                                                                                                                                  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AoU-1  | Requirement headings are reviewed or checked to match `## [A-Z][A-Z0-9_-]+` (L-1). Consider a project-side check that every `##` heading in a requirement file is a conformant ID.          |
| AoU-2  | A `Version` increment is part of the review checklist for every semantic change to a requirement or parameter.                                                                              |
| AoU-3  | Requirement IDs are unique across the baseline (L-4), for example by an independent check.                                                                                                  |
| AoU-4  | `release_readiness_test` is part of the release pipeline. Validation warnings are not the only gate (L-3).                                                                                  |
| AoU-5  | The `requirements`, `params`, and `source_traces` of `release_report` are checked against the complete baseline, for example by comparing against the requirements management source (L-7). |
| AoU-6  | Trace links are reviewed against the code, and the verifying tests are executed and their results evaluated independently of FIRE (L-6, L-7).                                               |
| AoU-7  | Generated code is verified: the generated constants are covered by tests or reviewed, and the generated files are compiled in the project's toolchain (UC-4).                               |
| AoU-8  | Parameter strings and descriptions contain only characters that are valid in all target languages, and no line breaks (L-9). Parameter tables are reviewed for shape (L-8).                 |
| AoU-9  | The FIRE version, the Bazel version, the Python version, and the pinned Python dependencies (`requirements.txt`) are fixed for a baseline and recorded.                                     |
| AoU-10 | PDFs and the format specification are not used as the only record of a requirement. The Markdown source is authoritative.                                                                   |

## Guidance for Tool Qualification

This section outlines how the ISO 26262-8 (clause 11, confidence in the use of software tools) argument can be structured.
IEC 61508-3 (tool classes T1-T3) and other standards use similar reasoning.
Check the clause numbers and terms against the edition required in your project.

### Step 1: Tool Impact (TI)

Decide per use case whether a malfunction can introduce or fail to detect an error in a safety-related item or element.

| Use case                            | Suggested TI | Rationale                                                                                          |
| ----------------------------------- | ------------ | -------------------------------------------------------------------------------------------------- |
| UC-4 Code generation                | TI2          | The output is compiled into the product.                                                           |
| UC-1, UC-2, UC-3, UC-5, UC-6 checks | TI2          | A missed finding can let a defect in requirements or traceability pass.                            |
| PDF export, format specification    | TI1          | Presentation only, provided AoU-10 holds. If the PDF is used as the review artifact, treat as TI2. |

### Step 2: Tool Error Detection (TD)

TD is the likelihood that a malfunction is prevented or detected.
FIRE does not give TD for itself.
Higher TD requires measures in the project, which the assumptions of use point to:

- Reviews of requirements, traces, and generated code (AoU-1, AoU-6, AoU-7).
- Independent consistency checks of the baseline (AoU-3, AoU-5).
- Tests of generated constants in the product test suite (AoU-7).

### Step 3: Resulting Tool Confidence Level (TCL)

Combine TI and TD using the table of your standard.
If TI2 uses are only covered by TD3 (low detection confidence), a qualification measure for FIRE is required.
The options are increased confidence from use, evaluation of the development process, validation of the tool, or development in accordance with a safety standard.

### Step 4: Qualification Measures

The following evidence exists today and may be used in a validation-of-the-tool argument.
It has not been assessed against a safety standard.

| Evidence                                                                                  | Location                                              |
| ----------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Unit tests (pytest), colocated with each script as `*_test.py`                            | `fire/starlark/`                                      |
| Failure tests that confirm invalid inputs fail the build or produce warnings              | `fire/starlark/failure_test/`, `run_failure_tests.sh` |
| Integration test as a consumer of the module, with a Python version matrix (3.11 to 3.15) | `integration_test/`                                   |
| Example project with requirements, parameters, and code in five languages                 | `examples/`                                           |
| CI on Linux and macOS with Bazel 7, 8, and 9; type checking with `ty`; pre-commit checks  | `.github/workflows/ci.yaml`                           |
| Pinned Python dependencies                                                                | `requirements.txt`, `MODULE.bazel.lock`               |
| Pull-request based workflow; test-driven development required                             | `AGENT.md`, `CONTRIBUTING.md`                         |

A validation-of-the-tool argument additionally needs:

- A tool requirements specification derived from the use cases and failure modes above (L-11).
- Test cases traced to those requirements, including negative tests for L-1 to L-10.
- A coverage measurement with a justified target.
- A record of the validation results for the exact FIRE, Bazel, and Python versions used.

## Reporting Problems

Report suspected malfunctions that could cause an undetected defect on the [issue tracker](https://github.com/nesono/fire/issues).
Include the FIRE version, the input files that reproduce the problem, and the output of the failing target.
