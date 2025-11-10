---
component: brake_actuator
version: 1
sil: ASIL-D
security_related: false
system_function: examples/system_functions/braking_control.sysarch.md
---

# Software Requirements: Brake Actuator Component

This document contains the software requirements for the Brake Actuator component. These requirements define how the component receives brake commands, controls hydraulic pressure, and interfaces with physical brake hardware.

## REQ_BA_RECEIVE_COMMANDS

- **ID**: REQ_BA_RECEIVE_COMMANDS
- **Parent**: examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The brake actuator component shall subscribe to brake force commands at a rate of 50 Hz and process each received command within 2 milliseconds. Each command contains brake force as a percentage [0, 100], a timestamp, and a status field. If no command is received within 30 milliseconds (timeout), the component shall initiate a controlled pressure release by ramping the hydraulic pressure to zero over 100 milliseconds.

---

## REQ_BA_CONVERT_FORCE

- **ID**: REQ_BA_CONVERT_FORCE
- **Parent**: examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The brake actuator component shall convert brake force percentage commands to hydraulic pressure setpoints using the linear relationship: target_pressure = (brake_force_percent × max_pressure) / 100, where max_pressure is calibrated to 120 bar for the vehicle brake system. The conversion shall be performed for each received brake command before updating the pressure controller setpoint. Zero brake force (0 percent) shall result in zero pressure (0 bar), and maximum brake force (100 percent) shall result in 120 bar target pressure.

---

## REQ_BA_CONTROL_HYDRAULICS

- **ID**: REQ_BA_CONTROL_HYDRAULICS
- **Parent**: examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The brake actuator component shall control the electro-hydraulic valve using a PI (Proportional-Integral) controller running at 1000 Hz to maintain actual hydraulic pressure within 1 bar of the target pressure. The controller shall use proportional gain Kp = 5.0 (percent per bar) and integral gain Ki = 2.0 (percent per bar-second). The controller output shall be a PWM duty cycle in range [0, 100] percent commanding the hydraulic valve. The component shall monitor actual pressure per REQ_BA_MONITOR_PRESSURE to calculate pressure error for the controller.

---

## REQ_BA_MONITOR_PRESSURE

- **ID**: REQ_BA_MONITOR_PRESSURE
- **Parent**: examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The brake actuator component shall read the hydraulic pressure sensor at 1000 Hz via an analog-to-digital converter. The sensor provides pressure values in the range [0, 150] bar with 0.1 bar precision. The component shall validate each pressure reading to ensure it is within the valid range. If the pressure sensor reading is out of range or the sensor fails, the component shall enter FAULT state per REQ_BA_SAFETY_LIMITS. The actual pressure shall be used as feedback for the pressure controller REQ_BA_CONTROL_HYDRAULICS and published in the actuator status message at 50 Hz.

---

## REQ_BA_SAFETY_LIMITS

- **ID**: REQ_BA_SAFETY_LIMITS
- **Parent**: examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
- **SIL**: ASIL-D
- **Sec**: false
- **Description**: The brake actuator component shall enforce safety limits on hydraulic pressure to prevent damage and ensure safe operation. The component shall limit target pressure to a maximum of 120 bar under normal conditions and 150 bar absolute maximum (hardware limit). The component shall limit pressure increase rate to 50 bar per second to prevent hydraulic shock. If any safety fault is detected (pressure sensor out of range, valve malfunction, excessive pressure error greater than 10 bar for more than 500 milliseconds), the component shall enter FAULT state, set valve PWM to 0 percent, release hydraulic pressure, and publish FAULT status.

---
