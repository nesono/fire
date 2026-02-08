package examples_test

import (
	"testing"

	// Import the single generated Go package
	vp "examples/vehicle_params_go"
)

func TestSimpleParameters(t *testing.T) {
	if vp.MaximumVehicleVelocityMpsV3 != 100.0 {
		t.Errorf("Expected MaximumVehicleVelocityMpsV3 = 100.0, got %f", vp.MaximumVehicleVelocityMpsV3)
	}

	if vp.WheelCountV1 != 4 {
		t.Errorf("Expected WheelCountV1 = 4, got %d", vp.WheelCountV1)
	}

	if vp.VehicleNameV1 != "TestVehicle" {
		t.Errorf("Expected VehicleNameV1 = TestVehicle, got %s", vp.VehicleNameV1)
	}

	if vp.DebugModeV1 != false {
		t.Errorf("Expected DebugModeV1 = false, got %v", vp.DebugModeV1)
	}
}

func TestTableParameters(t *testing.T) {
	table := vp.BrakingDistanceTableV1

	// Check we have the expected number of rows
	if len(table) != 6 {
		t.Errorf("Expected 6 rows, got %d", len(table))
	}

	// Check first row
	firstRow := table[0]
	if firstRow.Velocity != 10.0 {
		t.Errorf("Expected first row velocity = 10.0, got %f", firstRow.Velocity)
	}
	if firstRow.FrictionCoefficient != 0.7 {
		t.Errorf("Expected first row friction = 0.7, got %f", firstRow.FrictionCoefficient)
	}
	if firstRow.BrakingDistance != 7.1 {
		t.Errorf("Expected first row braking distance = 7.1, got %f", firstRow.BrakingDistance)
	}

	// Iterate over table
	found20ms := false
	for _, row := range table {
		if row.Velocity == 20.0 && row.FrictionCoefficient == 0.7 {
			if row.BrakingDistance != 28.6 {
				t.Errorf("Expected braking distance = 28.6 for 20 m/s, got %f", row.BrakingDistance)
			}
			found20ms = true
		}
	}

	if !found20ms {
		t.Error("Did not find expected row with velocity=20.0 and friction=0.7")
	}
}

func TestTableLookup(t *testing.T) {
	velocity := 10.0
	friction := 0.3

	var brakingDist float64
	found := false

	for _, row := range vp.BrakingDistanceTableV1 {
		if row.Velocity == velocity && row.FrictionCoefficient == friction {
			brakingDist = row.BrakingDistance
			found = true
			break
		}
	}

	if !found {
		t.Errorf("Could not find entry for velocity=%f, friction=%f", velocity, friction)
	}

	if brakingDist != 16.7 {
		t.Errorf("Expected braking distance = 16.7, got %f", brakingDist)
	}
}

// Example of a benchmark using the generated parameters
func BenchmarkTableLookup(b *testing.B) {
	for i := 0; i < b.N; i++ {
		for _, row := range vp.BrakingDistanceTableV1 {
			_ = row.BrakingDistance
		}
	}
}
