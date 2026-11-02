"""Pure obstacle-warning evaluation for simulated vehicle readings.

The evaluator validates its inputs and applies a small ordered rule set to
return exactly one status string. It is a pure, deterministic function: it
performs no I/O, uses no randomness and keeps no state between calls.
"""

import math

# Valid statuses, in the order the rules are applied. Kept as a module-level
# tuple so tests and callers can reference the canonical set of outputs.
STATUSES = ("SENSOR_FAULT", "IDLE", "BRAKE", "WARNING", "CLEAR")


def _validate_reading(value, name: str) -> None:
    """Validate a numeric reading (speed or distance).

    Accepts finite, non-negative ``int`` or ``float`` values. Booleans are
    rejected even though ``bool`` subclasses ``int``. Arbitrarily large
    integers are allowed without converting them to float, so they never
    overflow or lose precision. None, strings, containers, complex numbers,
    negatives, NaN and infinities all raise ``ValueError``.
    """
    # bool is a subclass of int, so check it first and reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite, non-negative int or float")
    # Integers are always finite; only floats can be NaN/inf. Avoid converting
    # arbitrarily large ints to float, which would overflow for huge values.
    if value < 0:
        raise ValueError(f"{name} must be a finite, non-negative int or float")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} must be a finite, non-negative int or float")


def evaluate_obstacle(speed_kmh, distance_m, sensor_healthy) -> str:
    """Validate readings and return the highest-priority obstacle status.

    All inputs are validated before any rule runs, so an invalid value raises
    ``ValueError`` even when the sensor is faulty or the vehicle is stopped.
    No inputs are silently converted.

    Rule priority for valid inputs:
      1. Unhealthy sensor -> ``SENSOR_FAULT``
      2. Speed equals zero -> ``IDLE``
      3. Moving and distance <= 5 m -> ``BRAKE``
      4. Moving and 5 m < distance <= warning distance -> ``WARNING``
      5. Moving and distance > warning distance -> ``CLEAR``

    The warning distance is 10 m normally, but rises to 15 m when speed
    exceeds 50 km/h. The braking threshold (5 m) is unaffected by speed.
    """
    _validate_reading(speed_kmh, "speed_kmh")
    _validate_reading(distance_m, "distance_m")
    if not isinstance(sensor_healthy, bool):
        raise ValueError("sensor_healthy must be True or False")

    # Rules run in declared priority order; the first match returns.
    if not sensor_healthy:
        return "SENSOR_FAULT"
    if speed_kmh == 0:
        return "IDLE"
    if distance_m <= 5:
        return "BRAKE"
    # Above 50 km/h the warning distance extends to 15 m; otherwise 10 m.
    # Speed exactly 50 does NOT exceed 50, so it keeps the 10 m threshold.
    warning_distance = 15 if speed_kmh > 50 else 10
    if distance_m <= warning_distance:
        return "WARNING"
    return "CLEAR"
