package fire.starlark.failure_test.parameter_version;

/**
 * Test that requesting an older version causes warning.
 */
public class TestVersionUpgraded {
    public static void main(String[] args) {
        // Parameter is at version 2, but we request version 1
        // This should print a warning to stderr
        double value = TestParams.testValue(1);
        System.out.println("Value: " + value);
    }
}
