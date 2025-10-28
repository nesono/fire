package com.example.vehicle.dynamics;

/**
 * Test for vehicle parameters in Java.
 *
 * This demonstrates how to use the generated parameter code in Java tests.
 * In a real project, you would use JUnit or TestNG.
 */
public class VehicleParamsTest {

    public static void testSimpleParameters() {
        // Access simple parameters
        assert VehicleParams.MAXIMUM_VEHICLE_VELOCITY == 55.0;
        assert VehicleParams.WHEEL_COUNT == 4;
        assert VehicleParams.VEHICLE_NAME.equals("TestVehicle");
        assert VehicleParams.DEBUG_MODE == false;

        System.out.println("Simple parameters test passed");
    }

    public static void testTableParameters() {
        // Access table parameter
        VehicleParams.BrakingDistanceTableRow[] table = VehicleParams.BRAKING_DISTANCE_TABLE;

        // Check we have the expected number of rows
        assert table.length == 6;

        // Check first row using record accessor methods
        VehicleParams.BrakingDistanceTableRow firstRow = table[0];
        assert firstRow.velocity() == 10.0;
        assert firstRow.frictionCoefficient() == 0.7;
        assert firstRow.brakingDistance() == 7.1;

        // Iterate over table
        boolean found20ms = false;
        for (VehicleParams.BrakingDistanceTableRow row : table) {
            if (row.velocity() == 20.0 && row.frictionCoefficient() == 0.7) {
                assert row.brakingDistance() == 28.6;
                found20ms = true;
            }
        }
        assert found20ms;

        System.out.println("Table parameters test passed");
    }

    public static void testRecordImmutability() {
        // Records are immutable by design in Java
        // This is enforced at compile time
        VehicleParams.BrakingDistanceTableRow row = VehicleParams.BRAKING_DISTANCE_TABLE[0];

        // row.velocity = 999.0;  // Would not compile - records are immutable

        System.out.println("Record immutability verified (compile-time)");
    }

    public static void main(String[] args) {
        testSimpleParameters();
        testTableParameters();
        testRecordImmutability();
        System.out.println("All Java parameter tests passed!");
    }
}
