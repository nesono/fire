// Test that outdated version emits warning but still builds.
// implements: REQ_TEST_FEATURE?version=1

#include <iostream>

int main() {
    std::cout << "Using old version 1, but requirement is at version 2" << std::endl;
    return 0;
}
