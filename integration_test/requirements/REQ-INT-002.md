# Braking Distance Requirement

## REQ-INT-002

SIL: ASIL-C | Version: 1

**Minimum Braking Distance**

The system SHALL maintain a minimum braking distance of [@min_braking_distance](test_params.bzl#min_braking_distance) when operating at maximum speed [REQ-INT-001](requirements/REQ-INT-001.md?version=1#REQ-INT-001).

### Rationale

This requirement is derived from [REQ-INT-001](requirements/REQ-INT-001.md?version=1#REQ-INT-001) to ensure safe stopping distance.

### Verification

Tested by [test_braking](//:test_braking).
