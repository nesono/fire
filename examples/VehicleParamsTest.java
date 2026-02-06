package com.example;

import org.junit.Test;
import static org.junit.Assert.*;
import static com.example.VehicleParamsJavaSrc.*;

/**
 * Test for vehicle parameters in Java.
 *
 * This demonstrates how to use the consolidated parameter class.
 */
public class VehicleParamsTest {

    @Test
    public void testSimpleParameters() {
        // Access simple parameters directly from the consolidated class
        assertEquals(55.0, MaximumVehicleVelocityV1, 0.001);
        assertEquals(4, WheelCountV1);
        assertEquals("TestVehicle", VehicleNameV1);
        assertEquals(false, DebugModeV1);
    }

    @Test
    public void testTableParameters() {
        // Access table parameter through nested class
        BrakingDistanceTableV1.BrakingDistanceTableRow[] table = BrakingDistanceTableV1.TABLE;

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
        BrakingDistanceTableV1.BrakingDistanceTableRow row = BrakingDistanceTableV1.TABLE[0];

        // Verify we can access the value
        assertEquals(10.0, row.velocity(), 0.001);
    }
}
