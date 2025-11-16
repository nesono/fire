# Speed Limit Requirement

## REQ-INT-001

```yaml
sil: ASIL-B
version: 1
```

**Maximum Speed Constraint**

The system SHALL NOT exceed the maximum speed defined by [@max_speed](test_params.bzl#max_speed).

This requirement ensures safe operation within design limits.

### Verification

Tested by [test_speed_limit](//:test_speed_limit).
