// Test for parameter code generation with custom namespace

#include "examples/vehicle_params_custom_ns/braking_distance_table_v1.h"
#include "examples/vehicle_params_custom_ns/debug_mode_v1.h"
#include "examples/vehicle_params_custom_ns/maximum_vehicle_velocity_v3.h"
#include "examples/vehicle_params_custom_ns/vehicle_name_v1.h"
#include "examples/vehicle_params_custom_ns/wheel_count_v1.h"
#include <cassert>
#include <cstring>
#include <iostream>

int main() {
  using namespace my_project::vehicle::params;

  // Test simple float parameter
  assert(MAXIMUM_VEHICLE_VELOCITY_MPS == 100.0);
  std::cout << "✓ MAXIMUM_VEHICLE_VELOCITY_MPS = " << MAXIMUM_VEHICLE_VELOCITY_MPS
            << " m/s" << std::endl;

  // Test integer parameter
  assert(WHEEL_COUNT == 4);
  std::cout << "✓ WHEEL_COUNT = " << WHEEL_COUNT << std::endl;

  // Test string parameter
  assert(std::strcmp(VEHICLE_NAME, "TestVehicle") == 0);
  std::cout << "✓ VEHICLE_NAME = \"" << VEHICLE_NAME << "\"" << std::endl;

  // Test boolean parameter
  assert(DEBUG_MODE == false);
  std::cout << "✓ DEBUG_MODE = " << (DEBUG_MODE ? "true" : "false")
            << std::endl;

  // Test table parameter with std::array
  assert(BRAKING_DISTANCE_TABLE.size() == 6);
  std::cout << "✓ BRAKING_DISTANCE_TABLE.size() = " << BRAKING_DISTANCE_TABLE.size()
            << std::endl;

  // Test first row of table
  assert(BRAKING_DISTANCE_TABLE[0].velocity_mps == 10.0);
  assert(BRAKING_DISTANCE_TABLE[0].friction_coefficient == 0.7);
  assert(BRAKING_DISTANCE_TABLE[0].braking_distance_m == 7.1);
  std::cout << "✓ BRAKING_DISTANCE_TABLE[0] = {" << BRAKING_DISTANCE_TABLE[0].velocity_mps << ", "
            << BRAKING_DISTANCE_TABLE[0].friction_coefficient << ", "
            << BRAKING_DISTANCE_TABLE[0].braking_distance_m << "}" << std::endl;

  std::cout << "\nAll custom namespace tests passed!" << std::endl;
  return 0;
}
