package com.example;

import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Test for vehicle parameters in Java.
 *
 * This demonstrates how to use the generated parameter code in Java tests.
 */
public class VehicleParamsTest {

    @Test
    public void testSimpleParameters() {
        // Access simple parameters with version check
        assertEquals(55.0, VehicleParams.maximumVehicleVelocity(1), 0.001);
        assertEquals(4, VehicleParams.wheelCount(1));
        assertEquals("TestVehicle", VehicleParams.vehicleName(1));
        assertEquals(false, VehicleParams.debugMode(1));
    }

    @Test
    public void testTableParameters() {
        // Access table parameter with version check
        VehicleParams.BrakingDistanceTableRow[] table = VehicleParams.brakingDistanceTable(1);

        // Check we have the expected number of rows
        assertEquals(6, table.length);

        // Check first row using record accessor methods
        VehicleParams.BrakingDistanceTableRow firstRow = table[0];
        assertEquals(10.0, firstRow.velocity(), 0.001);
        assertEquals(0.7, firstRow.frictionCoefficient(), 0.001);
        assertEquals(7.1, firstRow.brakingDistance(), 0.001);

        // Iterate over table
        boolean found20ms = false;
        for (VehicleParams.BrakingDistanceTableRow row : table) {
            if (row.velocity() == 20.0 && row.frictionCoefficient() == 0.7) {
                assertEquals(28.6, row.brakingDistance(), 0.001);
                found20ms = true;
            }
        }
        assertTrue(found20ms);
    }

    @Test
    public void testRecordImmutability() {
        // Records are immutable by design in Java
        // This is enforced at compile time
        VehicleParams.BrakingDistanceTableRow row = VehicleParams.brakingDistanceTable(1)[0];

        // row.velocity = 999.0;  // Would not compile - records are immutable

        // Verify we can access the value
        assertEquals(10.0, row.velocity(), 0.001);
    }
}
