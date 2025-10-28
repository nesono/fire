package dynamics_test

import (
	"testing"

	// Import the generated parameters
	// In actual use: "yourproject/vehicle/dynamics"
	dynamics "vehicle_params_go"
)

func TestSimpleParameters(t *testing.T) {
	// Access simple parameters
	if dynamics.MaximumVehicleVelocity != 55.0 {
		t.Errorf("Expected MaximumVehicleVelocity = 55.0, got %f", dynamics.MaximumVehicleVelocity)
	}

	if dynamics.WheelCount != 4 {
		t.Errorf("Expected WheelCount = 4, got %d", dynamics.WheelCount)
	}

	if dynamics.VehicleName != "TestVehicle" {
		t.Errorf("Expected VehicleName = TestVehicle, got %s", dynamics.VehicleName)
	}

	if dynamics.DebugMode != false {
		t.Errorf("Expected DebugMode = false, got %v", dynamics.DebugMode)
	}
}

func TestTableParameters(t *testing.T) {
	// Access table parameter
	table := dynamics.BrakingDistanceTable

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
	// Example of using the table for lookups
	velocity := 10.0
	friction := 0.3

	var brakingDist float64
	found := false

	for _, row := range dynamics.BrakingDistanceTable {
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
		for _, row := range dynamics.BrakingDistanceTable {
			_ = row.BrakingDistance
		}
	}
}
