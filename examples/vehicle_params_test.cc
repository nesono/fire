// Integration test for parameter code generation

#include "examples/vehicle_params.h"
#include <cassert>
#include <cstring>
#include <iostream>

int main() {
    using namespace examples;

    // Test simple float parameter with version check
    auto max_velocity = maximum_vehicle_velocity<1>();
    assert(max_velocity == 55.0);
    std::cout << "✓ maximum_vehicle_velocity<1>() = " << max_velocity << " m/s" << std::endl;

    // Test integer parameter
    auto wheels = wheel_count<1>();
    assert(wheels == 4);
    std::cout << "✓ wheel_count<1>() = " << wheels << std::endl;

    // Test string parameter
    auto name = vehicle_name<1>();
    assert(std::strcmp(name, "TestVehicle") == 0);
    std::cout << "✓ vehicle_name<1>() = \"" << name << "\"" << std::endl;

    // Test boolean parameter
    auto debug = debug_mode<1>();
    assert(debug == false);
    std::cout << "✓ debug_mode<1>() = " << (debug ? "true" : "false") << std::endl;

    // Test table parameter
    auto table = braking_distance_table<1>();
    assert(BRAKING_DISTANCE_TABLE_SIZE == 6);
    std::cout << "✓ BRAKING_DISTANCE_TABLE_SIZE = " << BRAKING_DISTANCE_TABLE_SIZE << std::endl;

    // Test first row of table
    assert(table[0].velocity == 10.0);
    assert(table[0].friction_coefficient == 0.7);
    assert(table[0].braking_distance == 7.1);
    std::cout << "✓ braking_distance_table<1>()[0] = {"
              << table[0].velocity << ", "
              << table[0].friction_coefficient << ", "
              << table[0].braking_distance << "}" << std::endl;

    // Test last row of table
    assert(table[5].velocity == 30.0);
    assert(table[5].friction_coefficient == 0.3);
    assert(table[5].braking_distance == 150.0);
    std::cout << "✓ braking_distance_table<1>()[5] = {"
              << table[5].velocity << ", "
              << table[5].friction_coefficient << ", "
              << table[5].braking_distance << "}" << std::endl;

    // Test iteration over table
    double total_distance = 0.0;
    for (size_t i = 0; i < BRAKING_DISTANCE_TABLE_SIZE; ++i) {
        total_distance += table[i].braking_distance;
    }
    std::cout << "✓ Total braking distance across all entries = " << total_distance << " m" << std::endl;

    std::cout << "\nAll tests passed!" << std::endl;
    return 0;
}
