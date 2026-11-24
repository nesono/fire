package codegen_test

import (
	"testing"

	sp "fire/starlark/codegen_test/special_params_go"
)

const expected = "say \"hi\" \\ back\\\\slash\ttab\nline2 é {x} %s $y 'q' /* c */ // not a comment \\u000a \\n ??/ \x01\x7fend\\"

func TestStringValue(t *testing.T) {
	if sp.SpecialStringV1 != expected {
		t.Errorf("special string: got %q, want %q", sp.SpecialStringV1, expected)
	}
}

func TestTableCellsAndColumns(t *testing.T) {
	table := sp.SpecialTableV1
	if len(table) != 2 {
		t.Fatalf("table size: got %d, want 2", len(table))
	}
	if table[0].Label != expected {
		t.Errorf("table string cell: got %q, want %q", table[0].Label, expected)
	}
	if table[1].Label != "plain" {
		t.Errorf("table plain cell: got %q", table[1].Label)
	}
	if table[0].TempDegc != -40.5 || table[0].RatioPercent != 12.5 ||
		table[0].AccelMps2 != 9.81 || table[0].LevelDba != 85.0 {
		t.Errorf("table columns: got %+v", table[0])
	}
}

func TestUnitsInIdentifiers(t *testing.T) {
	checks := []struct {
		name string
		got  float64
		want float64
	}{
		{"degrees celsius", sp.TemperatureDegcV1, 21.5},
		{"percent", sp.RatioPercentV1, 12.5},
		{"m/s squared", sp.AccelerationMps2V1, 9.81},
		{"dB(A)", sp.NoiseLevelDbaV1, 85.0},
		{"micro sign", sp.ThicknessUmV1, 3.0},
		{"omega", sp.ResistanceOhmV1, 4.7},
		{"m cubed", sp.VolumeM3V1, 1.5},
		{"per mille", sp.ErrorRatePermilleV1, 2.5},
		{"degrees per second", sp.TurnRateDegpsV1, 90.0},
	}
	for _, c := range checks {
		if c.got != c.want {
			t.Errorf("%s: got %v, want %v", c.name, c.got, c.want)
		}
	}
}
