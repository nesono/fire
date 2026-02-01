package fire.starlark.failure_test.parameter_version;

/**
 * Test that using v1 when v2 exists triggers @Deprecated warning.
 */
public class TestVersionUpgraded {
    public static void main(String[] args) {
        // TestValueV1 has @Deprecated annotation
        double value = TestValueV1.VALUE;
        System.out.println("Value: " + value);
    }
}
