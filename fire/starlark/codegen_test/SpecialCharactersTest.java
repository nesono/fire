package com.example.special;

import static com.example.special.SpecialParams.*;
import static org.junit.Assert.assertEquals;

import org.junit.Test;

/** Compiles and checks generated Java for special characters in values and units. */
public class SpecialCharactersTest {

    // A literal backslash followed by "u000a" is written as \\u000a; Java would
    // translate an odd number of backslashes before "u" into a unicode escape.
    private static final String EXPECTED =
        "say \"hi\" \\ back\\\\slash\ttab\nline2 é {x} %s $y 'q' /* c */ "
            + "// not a comment \\u000a \\n ??/ \001\177end\\";

    private static final double DELTA = 0.0;

    @Test
    public void testStringValue() {
        assertEquals(EXPECTED, SpecialStringV1);
    }

    @Test
    public void testTableCellsAndColumns() {
        assertEquals(2, SpecialTableV1.TABLE.size());
        assertEquals(EXPECTED, SpecialTableV1.TABLE.get(0).label());
        assertEquals("plain", SpecialTableV1.TABLE.get(1).label());
        assertEquals(-40.5, SpecialTableV1.TABLE.get(0).tempDegc(), DELTA);
        assertEquals(12.5, SpecialTableV1.TABLE.get(0).ratioPercent(), DELTA);
        assertEquals(9.81, SpecialTableV1.TABLE.get(0).accelMps2(), DELTA);
        assertEquals(85.0, SpecialTableV1.TABLE.get(0).levelDba(), DELTA);
    }

    @Test
    public void testUnitsInIdentifiers() {
        assertEquals(21.5, TemperatureDegcV1, DELTA);
        assertEquals(12.5, RatioPercentV1, DELTA);
        assertEquals(9.81, AccelerationMps2V1, DELTA);
        assertEquals(85.0, NoiseLevelDbaV1, DELTA);
        assertEquals(3.0, ThicknessUmV1, DELTA);
        assertEquals(4.7, ResistanceOhmV1, DELTA);
        assertEquals(1.5, VolumeM3V1, DELTA);
        assertEquals(2.5, ErrorRatePermilleV1, DELTA);
        assertEquals(90.0, TurnRateDegpsV1, DELTA);
    }
}
