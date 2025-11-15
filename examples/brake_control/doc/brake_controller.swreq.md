---
system_function: /examples/system_functions/braking_control.sysarch.md
---

# Software Requirements: Brake Controller Component

This document contains the software requirements for the Brake Controller component. These requirements are derived from the system-level braking requirements and define the specific behavior that must be implemented in the brake controller software.

## REQ_BC_CALCULATE_FORCE

```yaml
parent: /examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
parent_version: 1
sil: ASIL-D
sec: false
```

Derived from [REQ-BRK-001](/examples/requirements/REQ-BRK-001.sysreq.md?version=1#REQ-BRK-001).
The brake controller component shall calculate the required brake force based on current vehicle speed, target deceleration, and estimated friction coefficient. The calculation shall use a PID controller with feed-forward compensation derived from the braking distance table REQ_BC_USE_BRAKING_TABLE. The brake force shall be expressed as a percentage value in the range [0, 100].

---

## REQ_BC_MONITOR_DECELERATION

```yaml
parent: /examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
parent_version: 1
sil: ASIL-D
sec: false
```

Derived from [REQ-BRK-001](/examples/requirements/REQ-BRK-001.sysreq.md?version=1#REQ-BRK-001).
The brake controller component shall continuously monitor the actual vehicle deceleration by reading the vehicle status at a minimum rate of 50 Hz. The monitored deceleration shall be compared against the target deceleration, and the error shall be used as input to the brake force calculation algorithm REQ_BC_CALCULATE_FORCE.

---

## REQ_BC_USE_BRAKING_TABLE

```yaml
parent: /examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
parent_version: 1
sil: ASIL-D
sec: false
```

Derived from [REQ-BRK-001](/examples/requirements/REQ-BRK-001.sysreq.md?version=1#REQ-BRK-001).
The brake controller component shall use the braking distance table parameter to determine the relationship between vehicle speed, friction coefficient, and required braking distance. The table shall be loaded from vehicle parameters at initialization and validated to contain at least 6 data points. For intermediate values not present in the table, the component shall perform linear interpolation.

---

## REQ_BC_EMERGENCY_BRAKE

```yaml
parent: /examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
parent_version: 1
sil: ASIL-D
sec: false
```

Derived from [REQ-BRK-001](/examples/requirements/REQ-BRK-001.sysreq.md?version=1#REQ-BRK-001).
The brake controller component shall enter emergency braking mode and command maximum brake force (100 percent) if any of the following error conditions are detected: vehicle status input timeout (age greater than 40 milliseconds), vehicle speed exceeds maximum safe speed (30 meters per second), or friction estimate is invalid or out of range [0.3, 0.9]. The component shall continue in emergency braking mode until all error conditions are cleared for at least 500 milliseconds.

---

## REQ_BC_OUTPUT_RATE

```yaml
parent: /examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
parent_version: 1
sil: ASIL-D
sec: false
```

Derived from [REQ-BRK-001](/examples/requirements/REQ-BRK-001.sysreq.md?version=1#REQ-BRK-001).
The brake controller component shall publish brake force commands at a rate of 50 Hz (20 millisecond period) with a maximum jitter of 2 milliseconds. Each command shall include a timestamp, the commanded brake force percentage, and a status field indicating whether the component is operating in nominal mode or emergency mode as defined in REQ_BC_EMERGENCY_BRAKE.

---

## REQ_BC_INPUT_VALIDATION

```yaml
parent: /examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
parent_version: 1
sil: ASIL-D
sec: false
```

Derived from [REQ-BRK-001](/examples/requirements/REQ-BRK-001.sysreq.md?version=1#REQ-BRK-001).
The brake controller component shall validate all input values at each processing cycle. Vehicle speed shall be validated to be in range [0, 30] meters per second. Vehicle acceleration shall be validated to be in range [-15, 5] meters per second squared. Friction coefficient shall be validated to be in range [0.3, 0.9]. If any input value is out of range or stale (exceeds maximum age), the component shall trigger the emergency braking mode per REQ_BC_EMERGENCY_BRAKE.

---

## REQ_BC_FORCE_LIMITS

```yaml
parent: /examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
parent_version: 1
sil: ASIL-D
sec: false
```

Derived from [REQ-BRK-001](/examples/requirements/REQ-BRK-001.sysreq.md?version=1#REQ-BRK-001).
The brake controller component shall limit all calculated brake force values to the range [0, 100] percent before publishing brake commands. Values below 0 shall be clamped to 0, and values above 100 shall be clamped to 100. The component shall ensure that brake force can never be commanded outside this safe range under any circumstances, including during transient conditions or error recovery.

---

## REQ_BC_INITIALIZATION

```yaml
parent: /examples/requirements/REQ-BRK-001.sysreq.md#REQ-BRK-001
parent_version: 1
sil: ASIL-D
sec: false
```

Derived from [REQ-BRK-001](/examples/requirements/REQ-BRK-001.sysreq.md?version=1#REQ-BRK-001).
The brake controller component shall perform initialization at startup including: loading and validating the braking distance table from vehicle parameters, verifying table structure and data ranges, initializing all controller state variables to zero, establishing subscriptions to required input topics, and beginning to publish brake commands. If initialization fails due to invalid parameters or inability to establish communication, the component shall report an error and not enter operational mode.

---
