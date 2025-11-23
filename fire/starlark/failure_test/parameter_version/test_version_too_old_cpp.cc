// Test that requesting a version newer than available causes compile error
#include "test_params.h"

int main() {
    // Parameter is at version 2, but we request version 3
    // This should cause a static_assert failure
    auto value = test_value<3>();
    return 0;
}
