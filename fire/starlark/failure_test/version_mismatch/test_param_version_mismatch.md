# Test Parameter Version Mismatch

## REQ-PARAM-VERSION-TEST

SIL: ASIL-A | Sec: False | Version: 1

This requirement references [@test_param](/fire/starlark/failure_test/version_mismatch/test_params_v2.yaml?version=1#test_param) with version=1, but test_params_v2.yaml is at version=2.

This should generate a PARAMETER VERSION MISMATCH warning.
