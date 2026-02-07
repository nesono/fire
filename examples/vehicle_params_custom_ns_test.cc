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
  assert(MAXIMUM_VEHICLE_VELOCITY == 100.0);
  std::cout << "✓ MAXIMUM_VEHICLE_VELOCITY = " << MAXIMUM_VEHICLE_VELOCITY
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
  const auto& table = braking_distance_table();
  assert(table.size() == 6);
  std::cout << "✓ braking_distance_table().size() = " << table.size()
            << std::endl;

  // Test first row of table
  assert(table[0].velocity == 10.0);
  assert(table[0].friction_coefficient == 0.7);
  assert(table[0].braking_distance == 7.1);
  std::cout << "✓ braking_distance_table()[0] = {" << table[0].velocity << ", "
            << table[0].friction_coefficient << ", "
            << table[0].braking_distance << "}" << std::endl;

  std::cout << "\nAll custom namespace tests passed!" << std::endl;
  return 0;
}
