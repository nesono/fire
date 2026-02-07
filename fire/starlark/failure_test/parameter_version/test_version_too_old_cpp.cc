// Test that requesting a version that doesn't exist causes build error.
// test_value_v3.h does not exist (max version is v2), so this should fail.
#include "fire/starlark/failure_test/parameter_version/test_params_cc/test_value_v3.h"

int main() {
    return 0;
}
