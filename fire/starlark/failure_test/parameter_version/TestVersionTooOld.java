package fire.starlark.failure_test.parameter_version;

import static fire.starlark.failure_test.parameter_version.TestParamsJavaSrc.*;

/**
 * Test that referencing a version that doesn't exist causes build error.
 * TestValueV3 does not exist (max version is v2), so this should fail.
 */
public class TestVersionTooOld {
    public static void main(String[] args) {
        // This constant does not exist - compilation should fail
        double value = TestValueV3;
        System.out.println("Value: " + value);
    }
}
