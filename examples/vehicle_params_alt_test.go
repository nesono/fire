package examples_test

import (
	"testing"

	// Import from the alternate library
	vp "examples/vehicle_params_go_alt"
)

func TestAltSimpleParameters(t *testing.T) {
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

func TestAltTableParameters(t *testing.T) {
	table := vp.BrakingDistanceTableV1

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
