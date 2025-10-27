// Integration test for parameter code generation

#include "vehicle_params_header.h"
#include <cassert>
#include <cstring>
#include <iostream>

int main() {
    using namespace vehicle::dynamics;

    // Test simple float parameter
    assert(maximum_vehicle_velocity == 55.0);
    std::cout << "✓ maximum_vehicle_velocity = " << maximum_vehicle_velocity << " m/s" << std::endl;

    // Test integer parameter
    assert(wheel_count == 4);
    std::cout << "✓ wheel_count = " << wheel_count << std::endl;

    // Test string parameter
    assert(std::strcmp(vehicle_name, "TestVehicle") == 0);
    std::cout << "✓ vehicle_name = \"" << vehicle_name << "\"" << std::endl;

    // Test boolean parameter
    assert(debug_mode == false);
    std::cout << "✓ debug_mode = " << (debug_mode ? "true" : "false") << std::endl;

    // Test table parameter
    assert(braking_distance_table_size == 6);
    std::cout << "✓ braking_distance_table_size = " << braking_distance_table_size << std::endl;

    // Test first row of table
    assert(braking_distance_table[0].velocity == 10.0);
    assert(braking_distance_table[0].friction_coefficient == 0.7);
    assert(braking_distance_table[0].braking_distance == 7.1);
    std::cout << "✓ braking_distance_table[0] = {"
              << braking_distance_table[0].velocity << ", "
              << braking_distance_table[0].friction_coefficient << ", "
              << braking_distance_table[0].braking_distance << "}" << std::endl;

    // Test last row of table
    assert(braking_distance_table[5].velocity == 30.0);
    assert(braking_distance_table[5].friction_coefficient == 0.3);
    assert(braking_distance_table[5].braking_distance == 150.0);
    std::cout << "✓ braking_distance_table[5] = {"
              << braking_distance_table[5].velocity << ", "
              << braking_distance_table[5].friction_coefficient << ", "
              << braking_distance_table[5].braking_distance << "}" << std::endl;

    // Test iteration over table
    double total_distance = 0.0;
    for (size_t i = 0; i < braking_distance_table_size; ++i) {
        total_distance += braking_distance_table[i].braking_distance;
    }
    std::cout << "✓ Total braking distance across all entries = " << total_distance << " m" << std::endl;

    std::cout << "\nAll tests passed!" << std::endl;
    return 0;
}
