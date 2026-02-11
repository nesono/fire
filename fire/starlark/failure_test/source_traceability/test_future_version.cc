// Test that future/non-existent version causes build error.
// implements: REQ_TEST_FEATURE?version=3

#include <iostream>

int main() {
    std::cout << "This should fail: version 3 doesn't exist yet" << std::endl;
    return 0;
}
