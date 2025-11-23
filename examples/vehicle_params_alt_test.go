package examples_test

import (
	"testing"

	// Import from the alternate library
	vehicle_params_go_alt "examples/vehicle_params_go_alt"
)

func TestAltSimpleParameters(t *testing.T) {
	if vehicle_params_go_alt.MaximumVehicleVelocity(1) != 55.0 {
		t.Errorf("Expected MaximumVehicleVelocity = 55.0, got %f", vehicle_params_go_alt.MaximumVehicleVelocity(1))
	}

	if vehicle_params_go_alt.WheelCount(1) != 4 {
		t.Errorf("Expected WheelCount = 4, got %d", vehicle_params_go_alt.WheelCount(1))
	}

	if vehicle_params_go_alt.VehicleName(1) != "TestVehicle" {
		t.Errorf("Expected VehicleName = TestVehicle, got %s", vehicle_params_go_alt.VehicleName(1))
	}

	if vehicle_params_go_alt.DebugMode(1) != false {
		t.Errorf("Expected DebugMode = false, got %v", vehicle_params_go_alt.DebugMode(1))
	}
}

func TestAltTableParameters(t *testing.T) {
	table := vehicle_params_go_alt.BrakingDistanceTable(1)

	if len(table) != 6 {
		t.Errorf("Expected 6 rows, got %d", len(table))
	}

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
}
