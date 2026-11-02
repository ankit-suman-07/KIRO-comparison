"""SDV Obstacle Warning Evaluator — public interface: evaluate_obstacle.

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

    Validation steps applied in order:
      1. Reject bool (bool is a subclass of int; must be caught first).
      2. Reject non-numeric types.
      3. Reject negative values.
      4. If float, reject NaN or infinite values.
    Python int is arbitrary-precision and always finite, so step 4 is
    skipped for int values — e.g. 10**400 is accepted without OverflowError.
    """
    if isinstance(value, bool):
        raise ValueError(
            f"{name} must be an int or float, not bool; got {value!r}"
        )
    if not isinstance(value, (int, float)):
        raise ValueError(
            f"{name} must be an int or float; got {type(value).__name__!r}"
        )
    if value < 0:
        raise ValueError(f"{name} must be non-negative; got {value!r}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} must be finite; got {value!r}")


def evaluate_obstacle(speed_kmh, distance_m, sensor_healthy) -> str:
    """Validate readings and return the highest-priority obstacle status.

    All inputs are validated before any rule runs, so an invalid value raises
    ``ValueError`` even when the sensor is faulty or the vehicle is stopped.
    No inputs are silently converted.

    Rule priority for valid inputs:
      1. Unhealthy sensor  -> ``SENSOR_FAULT``
      2. Speed equals zero -> ``IDLE``
      3. Moving and distance <= 5 m -> ``BRAKE``
      4. Moving and 5 m < distance <= warning distance -> ``WARNING``
      5. Moving and distance > warning distance -> ``CLEAR``

    The warning distance is 10 m normally, but rises to 15 m when speed
    exceeds 50 km/h. The braking threshold (5 m) is unaffected by speed.
    Speed exactly 50 does NOT exceed 50, so it keeps the 10 m threshold.

    Raises ValueError for any invalid input (see _validate_reading for
    full rules).
    """
    # --- Input validation (all three params before any business logic) ---
    _validate_reading(speed_kmh, "speed_kmh")
    _validate_reading(distance_m, "distance_m")
    if not isinstance(sensor_healthy, bool):
        raise ValueError(
            f"sensor_healthy must be a bool (True or False); "
            f"got {type(sensor_healthy).__name__!r} {sensor_healthy!r}"
        )

    # --- Business rules applied in strict priority order ---
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
