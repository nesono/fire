package com.example;

import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Test for vehicle parameters in Java.
 *
 * This demonstrates how to use the generated per-parameter-version classes.
 */
public class VehicleParamsTest {

    @Test
    public void testSimpleParameters() {
        // Access simple parameters as constants from per-version classes
        assertEquals(55.0, MaximumVehicleVelocityV1.VALUE, 0.001);
        assertEquals(4, WheelCountV1.VALUE);
        assertEquals("TestVehicle", VehicleNameV1.VALUE);
        assertEquals(false, DebugModeV1.VALUE);
    }

    @Test
    public void testTableParameters() {
        // Access table parameter
        BrakingDistanceTableV1.BrakingDistanceTableRow[] table = BrakingDistanceTableV1.VALUE;

        // Check we have the expected number of rows
        assertEquals(6, table.length);
        assertEquals(6, BrakingDistanceTableV1.SIZE);

        // Check first row using record accessor methods
        BrakingDistanceTableV1.BrakingDistanceTableRow firstRow = table[0];
        assertEquals(10.0, firstRow.velocity(), 0.001);
        assertEquals(0.7, firstRow.frictionCoefficient(), 0.001);
        assertEquals(7.1, firstRow.brakingDistance(), 0.001);

        // Iterate over table
        boolean found20ms = false;
        for (BrakingDistanceTableV1.BrakingDistanceTableRow row : table) {
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
        BrakingDistanceTableV1.BrakingDistanceTableRow row = BrakingDistanceTableV1.VALUE[0];

        // Verify we can access the value
        assertEquals(10.0, row.velocity(), 0.001);
    }
}
