"""SDV Obstacle Warning Evaluator — public interface: evaluate_obstacle."""

import math as _math


def _validate_numeric(value, name: str) -> None:
    """Validate that *value* is a finite, non-negative int or float (not bool).

    Raises ValueError with a descriptive message if any rule is violated.
    Validation steps applied in order:
      1. Reject bool (bool is a subclass of int; must be caught first).
      2. Reject non-numeric types.
      3. If float, reject NaN.
      4. If float, reject infinite values.
      5. Reject negative values.
    Python int is arbitrary-precision and always finite, so steps 3-4 are
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
    if isinstance(value, float):
        if _math.isnan(value):
            raise ValueError(f"{name} must not be NaN")
        if _math.isinf(value):
            raise ValueError(f"{name} must not be infinite; got {value!r}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative; got {value!r}")


def _validate_sensor(value) -> None:
    """Validate that *value* is exactly a bool (True or False).

    Raises ValueError for any other type, including int 1/0, None, and str.
    Because bool is a subclass of int, isinstance(value, bool) correctly
    accepts only True and False while rejecting plain integers.
    """
    if not isinstance(value, bool):
        raise ValueError(
            f"sensor_healthy must be a bool (True or False); "
            f"got {type(value).__name__!r} {value!r}"
        )


def evaluate_obstacle(speed_kmh, distance_m, sensor_healthy) -> str:
    """Evaluate vehicle speed, obstacle distance, and sensor health.

    Returns one of five uppercase status strings:
      "SENSOR_FAULT" — sensor is unhealthy
      "IDLE"         — vehicle is stationary and sensor is healthy
      "BRAKE"        — vehicle moving; obstacle at or within 5 m
      "WARNING"      — vehicle moving; obstacle between 5 m (exclusive)
                       and 10 m (inclusive)
      "CLEAR"        — vehicle moving; obstacle beyond 10 m

    Raises ValueError for any invalid input (see _validate_numeric and
    _validate_sensor for full rules).
    """
    # --- Input validation (all three params before any business logic) ---
    _validate_numeric(speed_kmh, "speed_kmh")
    _validate_numeric(distance_m, "distance_m")
    _validate_sensor(sensor_healthy)

    # --- Business rules applied in strict priority order ---
    if not sensor_healthy:
        return "SENSOR_FAULT"
    if speed_kmh == 0:
        return "IDLE"
    if distance_m <= 5:
        return "BRAKE"
    if distance_m <= 10:
        return "WARNING"
    return "CLEAR"
