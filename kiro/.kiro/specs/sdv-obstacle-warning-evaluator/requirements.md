# Requirements Specification — SDV Obstacle Warning Evaluator

## Overview

The SDV Obstacle Warning Evaluator is a single, pure Python function that accepts vehicle speed, front obstacle distance, and sensor health as inputs, then returns a status string. It has no side effects and no external dependencies.

---

## Functional Requirements

### FR-1 — Public Interface

The module `obstacle_evaluator.py` must expose exactly one public function:

```python
def evaluate_obstacle(speed_kmh, distance_m, sensor_healthy) -> str:
```

**Acceptance criteria:**
- AC-1.1: Importing `obstacle_evaluator` must not execute any code, trigger a demonstration, print output, or produce any other side effect. The module-level scope must contain only definitions (imports, the public function, and any private helpers).
- AC-1.2: The function must return one of the five uppercase status strings defined in FR-4.
- AC-1.3: No additional public API (classes, public globals, extra public functions) is permitted. Private helper functions (names prefixed with `_`) are allowed internally to keep the implementation readable, but they must not be part of the public interface and must not introduce behaviour beyond what FR-2 through FR-4 specify.

---

### FR-2 — Input Validation

All three parameters must be validated before any business logic is applied. A `ValueError` must be raised for any invalid input.

#### FR-2.1 — `speed_kmh`

| Rule | Valid | Invalid — raises `ValueError` |
|---|---|---|
| Type | `int` or `float` (but **not** `bool`) | `bool`, `str`, `None`, any other type |
| Value | Finite and ≥ 0 | Negative, `math.inf`, `-math.inf`, `math.nan` |

**Acceptance criteria:**
- AC-2.1.1: `evaluate_obstacle(0, 5, True)` returns a valid status (no error).
- AC-2.1.2: `evaluate_obstacle(0.0, 5, True)` returns a valid status (no error).
- AC-2.1.3: `evaluate_obstacle(True, 5, True)` raises `ValueError` (bool rejected).
- AC-2.1.4: `evaluate_obstacle(False, 5, True)` raises `ValueError` (bool rejected).
- AC-2.1.5: `evaluate_obstacle(-1, 5, True)` raises `ValueError` (negative).
- AC-2.1.6: `evaluate_obstacle(float('inf'), 5, True)` raises `ValueError` (infinity).
- AC-2.1.7: `evaluate_obstacle(float('nan'), 5, True)` raises `ValueError` (NaN).
- AC-2.1.8: `evaluate_obstacle(None, 5, True)` raises `ValueError` (None).
- AC-2.1.9: `evaluate_obstacle("30", 5, True)` raises `ValueError` (string).

#### FR-2.2 — `distance_m`

| Rule | Valid | Invalid — raises `ValueError` |
|---|---|---|
| Type | `int` or `float` (but **not** `bool`) | `bool`, `str`, `None`, any other type |
| Value | Finite and ≥ 0 | Negative, `math.inf`, `-math.inf`, `math.nan` |

**Acceptance criteria:**
- AC-2.2.1: `evaluate_obstacle(30, 0, True)` returns a valid status (no error).
- AC-2.2.2: `evaluate_obstacle(30, 0.0, True)` returns a valid status (no error).
- AC-2.2.3: `evaluate_obstacle(30, True, True)` raises `ValueError` (bool rejected).
- AC-2.2.4: `evaluate_obstacle(30, False, True)` raises `ValueError` (bool rejected).
- AC-2.2.5: `evaluate_obstacle(30, -1, True)` raises `ValueError` (negative).
- AC-2.2.6: `evaluate_obstacle(30, float('inf'), True)` raises `ValueError` (infinity).
- AC-2.2.7: `evaluate_obstacle(30, float('nan'), True)` raises `ValueError` (NaN).
- AC-2.2.8: `evaluate_obstacle(30, None, True)` raises `ValueError` (None).
- AC-2.2.9: `evaluate_obstacle(30, "10", True)` raises `ValueError` (string).

#### FR-2.3 — `sensor_healthy`

| Rule | Valid | Invalid — raises `ValueError` |
|---|---|---|
| Type | `bool` exactly (`True` or `False`) | `int`, `float`, `str`, `None`, any other type |

**Acceptance criteria:**
- AC-2.3.1: `evaluate_obstacle(30, 10, True)` returns a valid status (no error).
- AC-2.3.2: `evaluate_obstacle(30, 10, False)` returns a valid status (no error).
- AC-2.3.3: `evaluate_obstacle(30, 10, 1)` raises `ValueError` (int 1 rejected).
- AC-2.3.4: `evaluate_obstacle(30, 10, 0)` raises `ValueError` (int 0 rejected).
- AC-2.3.5: `evaluate_obstacle(30, 10, None)` raises `ValueError` (None).
- AC-2.3.6: `evaluate_obstacle(30, 10, "True")` raises `ValueError` (string).

---

### FR-3 — Rule Priority

Rules are applied in strict priority order. The first matching condition wins; lower-priority rules are not evaluated.

| Priority | Condition | Returned status |
|---|---|---|
| 1 (highest) | `sensor_healthy` is `False` | `"SENSOR_FAULT"` |
| 2 | `speed_kmh == 0` | `"IDLE"` |
| 3 | `speed_kmh > 0` and `distance_m <= 5` | `"BRAKE"` |
| 4 | `speed_kmh > 0` and `5 < distance_m <= 10` | `"WARNING"` |
| 5 | `speed_kmh > 0` and `distance_m > 10` | `"CLEAR"` |

**Acceptance criteria (priority enforcement):**
- AC-3.1: `evaluate_obstacle(0, 3, False)` returns `"SENSOR_FAULT"` — sensor fault overrides idle speed.
- AC-3.2: `evaluate_obstacle(100, 2, False)` returns `"SENSOR_FAULT"` — sensor fault overrides brake distance.
- AC-3.3: `evaluate_obstacle(0, 3, True)` returns `"IDLE"` — stopped vehicle returns IDLE regardless of distance.
- AC-3.4: `evaluate_obstacle(0, 100, True)` returns `"IDLE"` — stopped vehicle returns IDLE regardless of large distance.

---

### FR-4 — Output Statuses

The function must return exactly one of these strings (uppercase, no whitespace variation):

| Status | Meaning |
|---|---|
| `"SENSOR_FAULT"` | Sensor is unhealthy |
| `"IDLE"` | Vehicle is stationary and sensor is healthy |
| `"BRAKE"` | Vehicle moving; obstacle at or closer than 5 m |
| `"WARNING"` | Vehicle moving; obstacle between 5 m (exclusive) and 10 m (inclusive) |
| `"CLEAR"` | Vehicle moving; obstacle beyond 10 m |

**Acceptance criteria (exact boundary values):**
- AC-4.1: `evaluate_obstacle(30, 5, True)` returns `"BRAKE"` (boundary: distance == 5, inclusive).
- AC-4.2: `evaluate_obstacle(30, 5.0, True)` returns `"BRAKE"` (float boundary).
- AC-4.3: `evaluate_obstacle(30, 5.1, True)` returns `"WARNING"` (just above 5 m boundary).
- AC-4.4: `evaluate_obstacle(30, 10, True)` returns `"WARNING"` (boundary: distance == 10, inclusive).
- AC-4.5: `evaluate_obstacle(30, 10.0, True)` returns `"WARNING"` (float boundary).
- AC-4.6: `evaluate_obstacle(30, 10.1, True)` returns `"CLEAR"` (just above 10 m boundary).
- AC-4.7: `evaluate_obstacle(30, 0, True)` returns `"BRAKE"` (zero distance, vehicle moving).
- AC-4.8: `evaluate_obstacle(30, 100, True)` returns `"CLEAR"` (large distance, vehicle moving).
- AC-4.9: `evaluate_obstacle(0.1, 5, True)` returns `"BRAKE"` (minimum non-zero float speed).

---

### FR-5 — Purity and Determinism

**Acceptance criteria:**
- AC-5.1: Calling the function twice with identical arguments must return the same result.
- AC-5.2: The function must not print, write files, read files, access the network, use randomness, or retain state between calls.
- AC-5.3: The module must use the Python standard library only (no third-party packages).

---

### FR-6 — Technology Constraints

- AC-6.1: The implementation must run on Python 3.12 or later.
- AC-6.2: Tests must be written with pytest (no other test framework).
- AC-6.3: No UI, server, database, network service, or Eclipse component is permitted.

---

## Out of Scope

The following are explicitly excluded and must not be implemented:

- Graphical or command-line user interfaces.
- Simulation or hardware sensor integration.
- Persistence (files, databases).
- Network communication.
- Any additional public function, public class, or public logic beyond what is specified above. (Private helpers are permitted; see AC-1.3.)
