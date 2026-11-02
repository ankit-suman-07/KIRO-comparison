"""Tests for obstacle_evaluator.evaluate_obstacle.

Covers input validation, rule priority, exact threshold boundaries
(including the speed-dependent 10 m / 15 m warning distance), and
determinism. Tests are drawn from both branches of the merge and
unified here; all duplicate coverage has been collapsed.

The intended warning threshold rule:
  - 10 m when speed <= 50 km/h
  - 15 m when speed >  50 km/h
The braking threshold (5 m) is unaffected by speed.
"""

import importlib
import math
import sys
from decimal import Decimal

import pytest

from obstacle_evaluator import evaluate_obstacle, STATUSES


# ---------------------------------------------------------------------------
# STATUSES constant
# ---------------------------------------------------------------------------

def test_statuses_are_exact_uppercase_strings():
    assert STATUSES == ("SENSOR_FAULT", "IDLE", "BRAKE", "WARNING", "CLEAR")
    assert all(isinstance(s, str) and s == s.upper() for s in STATUSES)


# ---------------------------------------------------------------------------
# Rule priority
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("speed", [0, 0.0])
@pytest.mark.parametrize("distance", [0, 5, 10, 100])
def test_sensor_fault_has_highest_priority(speed, distance):
    # A faulty sensor wins over a stopped vehicle and any distance.
    assert evaluate_obstacle(speed, distance, False) == "SENSOR_FAULT"


def test_sensor_fault_overrides_brake_distance():
    # distance within brake range, sensor=False → SENSOR_FAULT (not BRAKE)
    assert evaluate_obstacle(100, 2, False) == "SENSOR_FAULT"


@pytest.mark.parametrize("speed", [0, 0.0])
@pytest.mark.parametrize("distance", [0, 5, 10, 100])
def test_stopped_vehicle_is_idle(speed, distance):
    # With a healthy sensor, zero speed is IDLE regardless of distance.
    assert evaluate_obstacle(speed, distance, True) == "IDLE"


@pytest.mark.parametrize("speed", [1, 0.001, 30.5, 10 ** 1000])
def test_any_positive_speed_counts_as_moving(speed):
    assert evaluate_obstacle(speed, 5, True) == "BRAKE"


# ---------------------------------------------------------------------------
# Threshold boundaries — speed <= 50 km/h (10 m warning distance)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("distance, expected", [
    (0,                              "BRAKE"),
    (4.999,                          "BRAKE"),
    (5,                              "BRAKE"),
    (math.nextafter(5, math.inf),    "WARNING"),
    (7.5,                            "WARNING"),
    (10,                             "WARNING"),
    (math.nextafter(10, math.inf),   "CLEAR"),
    (100,                            "CLEAR"),
])
def test_moving_thresholds_low_speed(distance, expected):
    # speed=30 <= 50, so warning threshold is 10 m
    assert evaluate_obstacle(30, distance, True) == expected


def test_speed_exactly_50_keeps_10m_threshold():
    # 50 does not exceed 50, so the 15 m boundary does not apply yet.
    assert evaluate_obstacle(50, 15, True) == "CLEAR"
    assert evaluate_obstacle(50, 10, True) == "WARNING"
    assert evaluate_obstacle(50, math.nextafter(10, math.inf), True) == "CLEAR"


# ---------------------------------------------------------------------------
# Threshold boundaries — speed > 50 km/h (15 m warning distance)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("distance, expected", [
    (0,                              "BRAKE"),
    (4.999,                          "BRAKE"),
    (5,                              "BRAKE"),
    (math.nextafter(5, math.inf),    "WARNING"),
    (10,                             "WARNING"),
    (15,                             "WARNING"),
    (math.nextafter(15, math.inf),   "CLEAR"),
    (100,                            "CLEAR"),
])
def test_high_speed_extended_warning_threshold(distance, expected):
    # speed=60 > 50, so warning band stretches to 15 m.
    assert evaluate_obstacle(60, distance, True) == expected


def test_just_above_50_uses_15m_threshold():
    just_above_50 = math.nextafter(50, math.inf)
    assert evaluate_obstacle(just_above_50, 15, True) == "WARNING"
    assert evaluate_obstacle(just_above_50, math.nextafter(15, math.inf), True) == "CLEAR"


def test_braking_boundary_unchanged_at_high_speed():
    # The 5 m braking threshold is unaffected by the speed change.
    assert evaluate_obstacle(60, 5, True) == "BRAKE"
    assert evaluate_obstacle(60, math.nextafter(5, math.inf), True) == "WARNING"


@pytest.mark.parametrize("speed", [50.001, 60, 100, 10 ** 1000])
def test_high_speed_warning_at_15m(speed):
    assert evaluate_obstacle(speed, 15, True) == "WARNING"


def test_high_speed_still_respects_sensor_fault_and_idle():
    assert evaluate_obstacle(60, 15, False) == "SENSOR_FAULT"
    assert evaluate_obstacle(0, 15, True) == "IDLE"


def test_large_finite_integer_distance():
    # 10**1000 >> 15 m → CLEAR even at high speed
    assert evaluate_obstacle(1, 10 ** 1000, True) == "CLEAR"


# ---------------------------------------------------------------------------
# Acceptance cases
# ---------------------------------------------------------------------------

ACCEPTANCE_CASES = [
    (30,  20,    True,  "CLEAR"),
    (30,  10,    True,  "WARNING"),
    (30,  10.01, True,  "CLEAR"),
    (30,  5.01,  True,  "WARNING"),
    (30,  5,     True,  "BRAKE"),
    (30,  0,     True,  "BRAKE"),
    (0,   2,     True,  "IDLE"),
    (0,   20,    True,  "IDLE"),
    (30,  20,    False, "SENSOR_FAULT"),
    (0,   0,     False, "SENSOR_FAULT"),
    (0.1, 4.9,   True,  "BRAKE"),
    # High-speed acceptance cases
    (60,  15,    True,  "WARNING"),
    (60,  15.01, True,  "CLEAR"),
    (60,  10,    True,  "WARNING"),
    (51,  14,    True,  "WARNING"),
    (50,  10,    True,  "WARNING"),
    (50,  10.01, True,  "CLEAR"),
]


@pytest.mark.parametrize("speed, distance, healthy, expected", ACCEPTANCE_CASES)
def test_acceptance_cases(speed, distance, healthy, expected):
    assert evaluate_obstacle(speed, distance, healthy) == expected


# ---------------------------------------------------------------------------
# Input validation — speed_kmh and distance_m
# ---------------------------------------------------------------------------

INVALID_READINGS = [
    None, True, False, "5", "", -1, -0.1,
    math.inf, -math.inf, math.nan, [], {}, 1j, Decimal("5"),
]


@pytest.mark.parametrize("invalid", INVALID_READINGS)
@pytest.mark.parametrize("field", ["speed_kmh", "distance_m"])
@pytest.mark.parametrize("healthy", [True, False])
def test_invalid_readings_are_rejected_before_rules(invalid, field, healthy):
    # Validation takes priority, so even a faulty sensor still raises.
    readings = dict(speed_kmh=0, distance_m=0, sensor_healthy=healthy)
    readings[field] = invalid
    with pytest.raises(ValueError):
        evaluate_obstacle(**readings)


def test_validation_priority_over_sensor_fault():
    # -1 speed with a faulty sensor: validation must win.
    with pytest.raises(ValueError):
        evaluate_obstacle(-1, 20, False)


# Additional per-field validation spot-checks
class TestSpeedValidation:
    """Spot-checks for speed_kmh validation error messages / types."""

    def test_speed_zero_int_is_valid(self):
        assert evaluate_obstacle(0, 5, True) == "IDLE"

    def test_speed_zero_float_is_valid(self):
        assert evaluate_obstacle(0.0, 5, True) == "IDLE"

    def test_speed_positive_int_is_valid(self):
        assert evaluate_obstacle(30, 15, True) == "CLEAR"

    def test_speed_large_int_accepted(self):
        # 10**400 is a valid non-negative int; obstacle at 5 m → BRAKE
        assert evaluate_obstacle(10 ** 400, 5, True) == "BRAKE"

    def test_speed_true_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(True, 5, True)

    def test_speed_false_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(False, 5, True)

    def test_speed_negative_int_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(-1, 5, True)

    def test_speed_nan_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(float("nan"), 5, True)

    def test_speed_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(float("inf"), 5, True)

    def test_speed_none_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(None, 5, True)

    def test_speed_string_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle("30", 5, True)


class TestDistanceValidation:
    """Spot-checks for distance_m validation."""

    def test_distance_zero_int_is_valid(self):
        assert evaluate_obstacle(30, 0, True) == "BRAKE"

    def test_distance_large_int_accepted(self):
        # 10**400 >> 10 m → CLEAR
        assert evaluate_obstacle(30, 10 ** 400, True) == "CLEAR"

    def test_distance_true_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, True, True)

    def test_distance_negative_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, -1, True)

    def test_distance_nan_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, float("nan"), True)

    def test_distance_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, float("inf"), True)

    def test_distance_none_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, None, True)

    def test_distance_string_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, "10", True)


# ---------------------------------------------------------------------------
# Input validation — sensor_healthy
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("invalid", [None, 0, 1, 0.0, 1.0, "True", "False", [], {}])
def test_sensor_health_requires_boolean(invalid):
    with pytest.raises(ValueError):
        evaluate_obstacle(0, 0, invalid)


# ---------------------------------------------------------------------------
# Determinism and side-effect freedom
# ---------------------------------------------------------------------------

def test_repeated_calls_are_independent_and_silent(capsys):
    assert evaluate_obstacle(30, 20, True) == "CLEAR"
    assert evaluate_obstacle(30, 2, True) == "BRAKE"
    assert evaluate_obstacle(30, 20, True) == "CLEAR"
    assert capsys.readouterr() == ("", "")


def test_import_has_no_side_effects(capsys):
    # Re-importing must not print or run anything.
    import obstacle_evaluator
    importlib.reload(obstacle_evaluator)
    assert capsys.readouterr() == ("", "")


def test_module_import_produces_no_output(capsys):
    # Remove the cached module so the import actually executes again.
    sys.modules.pop("obstacle_evaluator", None)
    importlib.import_module("obstacle_evaluator")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
