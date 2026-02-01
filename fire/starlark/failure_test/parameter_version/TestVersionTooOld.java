package fire.starlark.failure_test.parameter_version;

/**
 * Test that referencing a version class that doesn't exist causes build error.
 * TestValueV3 does not exist (max version is v2), so this should fail.
 */
public class TestVersionTooOld {
    public static void main(String[] args) {
        // This class does not exist - compilation should fail
        double value = TestValueV3.VALUE;
        System.out.println("Value: " + value);
    }
}
