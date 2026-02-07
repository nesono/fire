package fire.starlark.failure_test.parameter_version;

import static fire.starlark.failure_test.parameter_version.TestParamsJavaSrc.*;

/**
 * Test that using v1 when v2 exists triggers @Deprecated warning.
 */
public class TestVersionUpgraded {
    public static void main(String[] args) {
        // TestValueV1 has @Deprecated annotation
        double value = TestValueV1;
        System.out.println("Value: " + value);
    }
}
