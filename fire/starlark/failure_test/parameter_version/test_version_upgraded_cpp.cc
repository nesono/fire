// Test that requesting an older version causes compile-time deprecation warning
#include "fire/starlark/failure_test/parameter_version/test_params.h"

int main() {
    // Parameter is at version 2, but we request version 1
    // This should cause a deprecation warning at compile time
    auto value = test::test_value<1>();
    return 0;
}
