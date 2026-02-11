// Test that missing version suffix causes build error.
// implements: REQ_TEST_FEATURE (missing ?version= suffix)

#include <iostream>

int main() {
    std::cout << "This should fail: missing version suffix" << std::endl;
    return 0;
}
