// Integration test for parameter code generation

#include "examples/vehicle_params_cc/braking_distance_table_v1.h"
#include "examples/vehicle_params_cc/debug_mode_v1.h"
#include "examples/vehicle_params_cc/maximum_vehicle_velocity_v3.h"
#include "examples/vehicle_params_cc/vehicle_name_v1.h"
#include "examples/vehicle_params_cc/wheel_count_v1.h"
#include <cassert>
#include <cstring>
#include <iostream>

int main() {

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

  // Test table parameter
  assert(BRAKING_DISTANCE_TABLE_SIZE == 6);
  std::cout << "✓ BRAKING_DISTANCE_TABLE_SIZE = " << BRAKING_DISTANCE_TABLE_SIZE
            << std::endl;

  // Test first row of table
  auto table = braking_distance_table();
  assert(table[0].velocity == 10.0);
  assert(table[0].friction_coefficient == 0.7);
  assert(table[0].braking_distance == 7.1);
  std::cout << "✓ braking_distance_table()[0] = {" << table[0].velocity << ", "
            << table[0].friction_coefficient << ", "
            << table[0].braking_distance << "}" << std::endl;

  // Test last row of table
  assert(table[5].velocity == 30.0);
  assert(table[5].friction_coefficient == 0.3);
  assert(table[5].braking_distance == 150.0);
  std::cout << "✓ braking_distance_table()[5] = {" << table[5].velocity << ", "
            << table[5].friction_coefficient << ", "
            << table[5].braking_distance << "}" << std::endl;

  // Test iteration over table
  double total_distance = 0.0;
  for (size_t i = 0; i < BRAKING_DISTANCE_TABLE_SIZE; ++i) {
    total_distance += table[i].braking_distance;
  }
  std::cout << "✓ Total braking distance across all entries = "
            << total_distance << " m" << std::endl;

  std::cout << "\nAll tests passed!" << std::endl;
  return 0;
}
