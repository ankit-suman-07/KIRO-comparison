"""Pure obstacle-warning evaluation for simulated vehicle readings."""

import math


def _validate_reading(value, name: str) -> None:
    # Integers are always finite; avoid converting arbitrarily large ints to float.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite, non-negative int or float")
    if value < 0 or (isinstance(value, float) and not math.isfinite(value)):
        raise ValueError(f"{name} must be a finite, non-negative int or float")


def evaluate_obstacle(speed_kmh, distance_m, sensor_healthy) -> str:
    """Validate readings and return the highest-priority obstacle status.

    Raises ValueError for invalid supplied values, even if the sensor is faulty
    or the vehicle is stopped. No inputs are silently converted.
    """
    _validate_reading(speed_kmh, "speed_kmh")
    _validate_reading(distance_m, "distance_m")
    if not isinstance(sensor_healthy, bool):
        raise ValueError("sensor_healthy must be True or False")

    if not sensor_healthy:
        return "SENSOR_FAULT"
    if speed_kmh == 0:
        return "IDLE"
    if distance_m <= 5:
        return "BRAKE"
    if distance_m <= 10:
        return "WARNING"
    return "CLEAR"
