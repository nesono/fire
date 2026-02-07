// Test that including v1 when v2 exists emits deprecation warning.
// test_value_v1.h has a #pragma message deprecation warning.
#include "fire/starlark/failure_test/parameter_version/test_params_cc/test_value_v1.h"

int main() {
    // v1 still works but should emit a compile-time warning
    return 0;
}
