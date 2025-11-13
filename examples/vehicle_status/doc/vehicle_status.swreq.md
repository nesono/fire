---
system_function: /examples/system_functions/braking_control.sysarch.md
---

# Software Requirements: Vehicle Status Component

This document contains the software requirements for the Vehicle Status component. These requirements define how the component reads sensors, calculates vehicle state, and publishes status information for use by control systems.

## REQ_VS_READ_SENSORS

- **ID**: REQ_VS_READ_SENSORS
- **Parent**: /examples/requirements/REQ-VEL-001.sysreq.md#REQ-VEL-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The vehicle status component shall read wheel speed sensor data from all four wheels via the CAN bus at a rate of 100 Hz. Each wheel speed sensor provides rotational speed in RPM (revolutions per minute) with valid range [0, 2000] RPM. The component shall reject any sensor readings older than 20 milliseconds.

---

## REQ_VS_CALCULATE_SPEED

- **ID**: REQ_VS_CALCULATE_SPEED
- **Parent**: /examples/requirements/REQ-VEL-001.sysreq.md#REQ-VEL-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The vehicle status component shall calculate vehicle linear speed by converting each valid wheel speed from RPM to meters per second using the configured wheel radius parameter, then averaging the converted speeds from all valid wheels. The calculation shall use the formula: linear_velocity = (RPM × 2π × wheel_radius) / 60. The component shall validate sensor readings per REQ_VS_VALIDATE_SENSORS before including them in the average.

---

## REQ_VS_CALCULATE_ACCELERATION

- **ID**: REQ_VS_CALCULATE_ACCELERATION
- **Parent**: /examples/requirements/REQ-VEL-001.sysreq.md#REQ-VEL-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The vehicle status component shall calculate vehicle acceleration by computing the rate of change of vehicle speed over time. The raw acceleration shall be calculated as (current_speed - previous_speed) / time_delta. To reduce measurement noise, the component shall apply a first-order low-pass filter with coefficient alpha = 0.3 according to the formula: filtered_accel = 0.3 × raw_accel + 0.7 × previous_filtered_accel.

---

## REQ_VS_PUBLISH_STATUS

- **ID**: REQ_VS_PUBLISH_STATUS
- **Parent**: /examples/requirements/REQ-VEL-001.sysreq.md#REQ-VEL-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The vehicle status component shall publish vehicle status messages at a rate of 100 Hz (10 millisecond period) with maximum jitter of 1 millisecond. Each status message shall include: vehicle speed in meters per second, vehicle acceleration in meters per second squared, timestamp in nanoseconds, and status field (VALID, DEGRADED, or INVALID) as determined by REQ_VS_VALIDATE_SENSORS. The maximum latency from sensor read to publish shall be 2 milliseconds.

---

## REQ_VS_VALIDATE_SENSORS

- **ID**: REQ_VS_VALIDATE_SENSORS
- **Parent**: /examples/requirements/REQ-VEL-001.sysreq.md#REQ-VEL-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The vehicle status component shall validate wheel speed sensors by performing plausibility checks. For each sensor reading: (1) check that RPM value is within valid range [0, 2000], (2) check that sensor data age is less than 20 milliseconds, (3) calculate the mean of all sensor readings and check that each sensor deviates from the mean by no more than 30 percent. If any sensor fails validation, exclude it from speed calculation. If a sensor deviates by 20-30 percent, mark status as DEGRADED. If fewer than 3 sensors pass validation, mark status as INVALID and publish zero speed and acceleration.

---
