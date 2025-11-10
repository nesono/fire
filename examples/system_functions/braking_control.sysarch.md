---
implements_requirements:
  - examples/requirements/REQ-BRK-001.sysreq.md
---

# Braking Control System Function

## Description

The Braking Control System Function is responsible for calculating and applying appropriate braking force
to ensure the vehicle can decelerate safely within specified distance constraints. This function implements
the system-level braking requirements and coordinates between multiple software components to achieve safe
vehicle stopping.

## Diagram

```mermaid
flowchart LR
    %%{init: {'theme': 'neutral'}}%%
    classDef Component fill:#aaa,stroke:#222,stroke-width:2;
    classDef SWC fill:#ddd,stroke:#444,stroke-width:1;
    classDef Process fill:#ccc,stroke:#444,stroke-width:1;
    classDef Reference fill:#fff,stroke:#444,stroke-width:1,stroke-dasharray:5;

    subgraph vehicle
        direction LR

        subgraph control_computer
            direction TB

            subgraph brake_controller
                brake_control_swc[brake_controller]:::SWC
            end
            class brake_controller Process

            subgraph vehicle_interface
                vehicle_status[vehicle_status]:::Reference
                brake_actuator[brake_actuator]:::Reference
            end
            class vehicle_interface Process
        end
        class control_computer Component

        subgraph brake_system
            hydraulic_brake[hydraulic_brake]:::Reference
        end
        class brake_system Component
    end

    vehicle_status --> brake_control_swc
    brake_control_swc --> brake_actuator
    brake_actuator --> hydraulic_brake
```

## Behavior

* The brake controller component receives vehicle status information including current speed and desired deceleration
* Based on the braking distance table parameters and current friction conditions, the component calculates required brake force
* The brake force command is sent to the brake actuator interface
* The actuator applies hydraulic pressure to the physical brake system
* The system continuously monitors actual deceleration and adjusts brake force as needed

## References

* [brake_controller](../brake_control/doc/brake_controller.techspec.md) - Software component implementing brake control logic
* [vehicle_status](../vehicle_status/doc/vehicle_status.techspec.md) - Software component providing vehicle state information
* [brake_actuator](../brake_actuator/doc/brake_actuator.techspec.md) - Software component interfacing with brake hardware
* [REQ-BRK-001](../requirements/REQ-BRK-001.sysreq.md) - System requirement for braking distance

## Links

| Link | Transport | Channel | Message |
| :--- | :-------- | :------ | ------: |
| `1`  | `Internal` | `/vehicle/status` | `vehicle_status (speed_mps, acceleration_mps2)` |
| `2`  | `Internal` | `/vehicle/brake/command` | `brake_command (brake_force_percent)` |
| `3`  | `CAN` | can_vehicle | `brake_actuator_cmd (pressure_bar)` |

## Open Topics

* Integration with ABS (Anti-lock Braking System) to be defined in future version
* Coordination with regenerative braking for electric/hybrid vehicles
