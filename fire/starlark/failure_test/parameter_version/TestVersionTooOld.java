package fire.starlark.failure_test.parameter_version;

/**
 * Test that requesting a version newer than available causes runtime error.
 */
public class TestVersionTooOld {
    public static void main(String[] args) {
        // Parameter is at version 2, but we request version 3
        // This should throw IllegalArgumentException
        double value = TestParams.testValue(3);
        System.out.println("Value: " + value);
    }
}
