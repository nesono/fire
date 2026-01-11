# Test Parameter Version Mismatch Error

## REQ-PARAM-VERSION-ERROR

SIL: ASIL-A | Sec: Public | Version: 1

This requirement references
[@test_param](/fire/starlark/failure_test/version_mismatch/test_params_v2.yaml?version=3#test_param)
with version=3, but test_params_v2.yaml is at version=2 - this needs to create
an error.

This should generate a PARAMETER VERSION MISMATCH error.
