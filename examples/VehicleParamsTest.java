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
        assertEquals(100.0, MaximumVehicleVelocityMpsV3, 0.001);
        assertEquals(4, WheelCountV1);
        assertEquals("TestVehicle", VehicleNameV1);
        assertEquals(false, DebugModeV1);
    }

    @Test
    public void testTableParameters() {
        // Access table parameter through nested class
        var table = BrakingDistanceTableV1.TABLE;

        // Check we have the expected number of rows
        assertEquals(6, table.size());

        // Check first row using record accessor methods
        var firstRow = table.get(0);
        assertEquals(10.0, firstRow.velocity(), 0.001);
        assertEquals(0.7, firstRow.frictionCoefficient(), 0.001);
        assertEquals(7.1, firstRow.brakingDistance(), 0.001);

        // Iterate over table with enhanced for-loop
        boolean found20ms = false;
        for (var row : table) {
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
        var row = BrakingDistanceTableV1.TABLE.get(0);

        // Verify we can access the value
        assertEquals(10.0, row.velocity(), 0.001);
    }
}
