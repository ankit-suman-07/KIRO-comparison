"""Tests for obstacle_evaluator.evaluate_obstacle.

Groups mirror design.md §6:
  - Input validation: speed_kmh  (AC-2.1.x)
  - Input validation: distance_m (AC-2.2.x)
  - Input validation: sensor_healthy (AC-2.3.x)
  - Rule priority (AC-3.x)
  - Boundary values (AC-4.x)
  - Large integer inputs
  - Purity (AC-5.1)
  - Module import side-effects (AC-1.1)
"""

import importlib
import math
import sys
from decimal import Decimal

import pytest

from obstacle_evaluator import evaluate_obstacle


# ---------------------------------------------------------------------------
# Rule priority (AC-3.x)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("speed", [0, 0.0])
@pytest.mark.parametrize("distance", [0, 5, 10, 100])
def test_sensor_fault_has_highest_priority(speed, distance):
    # A faulty sensor wins over a stopped vehicle and any distance.
    assert evaluate_obstacle(speed, distance, False) == "SENSOR_FAULT"


def test_sensor_fault_overrides_brake_distance():
    # AC-3.2: distance within brake range, sensor=False → SENSOR_FAULT
    assert evaluate_obstacle(100, 2, False) == "SENSOR_FAULT"


@pytest.mark.parametrize("speed", [0, 0.0])
@pytest.mark.parametrize("distance", [0, 5, 10, 100])
def test_stopped_vehicle_is_idle(speed, distance):
    # With a healthy sensor, zero speed is IDLE regardless of distance.
    assert evaluate_obstacle(speed, distance, True) == "IDLE"


def test_idle_overrides_close_distance():
    # AC-3.3: speed=0, distance=3 → IDLE (not BRAKE)
    assert evaluate_obstacle(0, 3, True) == "IDLE"


def test_idle_overrides_large_distance():
    # AC-3.4: speed=0, distance=100 → IDLE (not CLEAR)
    assert evaluate_obstacle(0, 100, True) == "IDLE"


@pytest.mark.parametrize("speed", [1, 0.001, 30.5, 10 ** 1000])
def test_any_positive_speed_counts_as_moving(speed):
    assert evaluate_obstacle(speed, 5, True) == "BRAKE"


# ---------------------------------------------------------------------------
# Boundary values (AC-4.x)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("distance, expected", [
    (0,                            "BRAKE"),
    (4.999,                        "BRAKE"),
    (5,                            "BRAKE"),    # AC-4.1 / AC-4.2: inclusive
    (math.nextafter(5, math.inf),  "WARNING"),  # AC-4.3: just above 5 m
    (7.5,                          "WARNING"),
    (10,                           "WARNING"),  # AC-4.4 / AC-4.5: inclusive
    (math.nextafter(10, math.inf), "CLEAR"),    # AC-4.6: just above 10 m
    (100,                          "CLEAR"),    # AC-4.8
])
def test_moving_thresholds(distance, expected):
    # speed=30, fixed 10 m warning threshold
    assert evaluate_obstacle(30, distance, True) == expected


def test_distance_5_int_returns_brake():
    # AC-4.1
    assert evaluate_obstacle(30, 5, True) == "BRAKE"


def test_distance_5_float_returns_brake():
    # AC-4.2
    assert evaluate_obstacle(30, 5.0, True) == "BRAKE"


def test_distance_5_1_returns_warning():
    # AC-4.3
    assert evaluate_obstacle(30, 5.1, True) == "WARNING"


def test_distance_10_int_returns_warning():
    # AC-4.4
    assert evaluate_obstacle(30, 10, True) == "WARNING"


def test_distance_10_float_returns_warning():
    # AC-4.5
    assert evaluate_obstacle(30, 10.0, True) == "WARNING"


def test_distance_10_1_returns_clear():
    # AC-4.6
    assert evaluate_obstacle(30, 10.1, True) == "CLEAR"


def test_zero_distance_moving_vehicle_returns_brake():
    # AC-4.7
    assert evaluate_obstacle(30, 0, True) == "BRAKE"


def test_large_distance_moving_vehicle_returns_clear():
    # AC-4.8
    assert evaluate_obstacle(30, 100, True) == "CLEAR"


def test_minimum_nonzero_float_speed_returns_brake():
    # AC-4.9
    assert evaluate_obstacle(0.1, 5, True) == "BRAKE"


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
    # High speed: threshold is still 10 m (no speed-dependent extension)
    (60,  10,    True,  "WARNING"),
    (60,  10.01, True,  "CLEAR"),
    (60,  15,    True,  "CLEAR"),
    (100, 10,    True,  "WARNING"),
    (100, 10.01, True,  "CLEAR"),
]


@pytest.mark.parametrize("speed, distance, healthy, expected", ACCEPTANCE_CASES)
def test_acceptance_cases(speed, distance, healthy, expected):
    assert evaluate_obstacle(speed, distance, healthy) == expected


# ---------------------------------------------------------------------------
# Large integer inputs
# ---------------------------------------------------------------------------

def test_large_integer_speed_accepted():
    # 10**400 is a valid non-negative int; obstacle at 5 m → BRAKE
    assert evaluate_obstacle(10 ** 400, 5, True) == "BRAKE"


def test_large_integer_distance_accepted():
    # 10**400 >> 10 m → CLEAR
    assert evaluate_obstacle(30, 10 ** 400, True) == "CLEAR"


# ---------------------------------------------------------------------------
# Input validation — speed_kmh (AC-2.1.x)
# ---------------------------------------------------------------------------

INVALID_READINGS = [
    None, True, False, "5", "", -1, -0.1,
    math.inf, -math.inf, math.nan, [], {}, 1j, Decimal("5"),
]


@pytest.mark.parametrize("invalid", INVALID_READINGS)
@pytest.mark.parametrize("field", ["speed_kmh", "distance_m"])
@pytest.mark.parametrize("healthy", [True, False])
def test_invalid_readings_are_rejected_before_rules(invalid, field, healthy):
    # Validation takes priority even over sensor fault.
    readings = dict(speed_kmh=0, distance_m=0, sensor_healthy=healthy)
    readings[field] = invalid
    with pytest.raises(ValueError):
        evaluate_obstacle(**readings)


def test_validation_priority_over_sensor_fault():
    # -1 speed with a faulty sensor: validation must still win.
    with pytest.raises(ValueError):
        evaluate_obstacle(-1, 20, False)


class TestSpeedValidation:
    """Per-field spot-checks for speed_kmh (AC-2.1.x)."""

    def test_speed_zero_int_is_valid(self):
        assert evaluate_obstacle(0, 5, True) == "IDLE"

    def test_speed_zero_float_is_valid(self):
        assert evaluate_obstacle(0.0, 5, True) == "IDLE"

    def test_speed_positive_int_is_valid(self):
        assert evaluate_obstacle(30, 15, True) == "CLEAR"

    def test_speed_positive_float_is_valid(self):
        assert evaluate_obstacle(30.5, 15, True) == "CLEAR"

    def test_speed_large_int_accepted(self):
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

    def test_speed_negative_float_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(-0.1, 5, True)

    def test_speed_positive_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(float("inf"), 5, True)

    def test_speed_negative_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(float("-inf"), 5, True)

    def test_speed_nan_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(float("nan"), 5, True)

    def test_speed_none_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(None, 5, True)

    def test_speed_string_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle("30", 5, True)


# ---------------------------------------------------------------------------
# Input validation — distance_m (AC-2.2.x)
# ---------------------------------------------------------------------------

class TestDistanceValidation:
    """Per-field spot-checks for distance_m (AC-2.2.x)."""

    def test_distance_zero_int_is_valid(self):
        assert evaluate_obstacle(30, 0, True) == "BRAKE"

    def test_distance_zero_float_is_valid(self):
        assert evaluate_obstacle(30, 0.0, True) == "BRAKE"

    def test_distance_positive_int_is_valid(self):
        assert evaluate_obstacle(30, 10, True) == "WARNING"

    def test_distance_positive_float_is_valid(self):
        assert evaluate_obstacle(30, 10.5, True) == "CLEAR"

    def test_distance_large_int_accepted(self):
        assert evaluate_obstacle(30, 10 ** 400, True) == "CLEAR"

    def test_distance_true_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, True, True)

    def test_distance_false_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, False, True)

    def test_distance_negative_int_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, -1, True)

    def test_distance_negative_float_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, -0.1, True)

    def test_distance_positive_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, float("inf"), True)

    def test_distance_negative_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, float("-inf"), True)

    def test_distance_nan_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, float("nan"), True)

    def test_distance_none_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, None, True)

    def test_distance_string_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, "10", True)


# ---------------------------------------------------------------------------
# Input validation — sensor_healthy (AC-2.3.x)
# ---------------------------------------------------------------------------

class TestSensorValidation:
    """sensor_healthy must be exactly bool (AC-2.3.x)."""

    def test_sensor_true_is_valid(self):
        assert evaluate_obstacle(30, 10, True) == "WARNING"

    def test_sensor_false_is_valid(self):
        assert evaluate_obstacle(30, 10, False) == "SENSOR_FAULT"

    def test_sensor_int_one_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, 10, 1)

    def test_sensor_int_zero_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, 10, 0)

    def test_sensor_none_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, 10, None)

    def test_sensor_string_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, 10, "True")


@pytest.mark.parametrize("invalid", [None, 0, 1, 0.0, 1.0, "True", "False", [], {}])
def test_sensor_health_requires_boolean(invalid):
    with pytest.raises(ValueError):
        evaluate_obstacle(0, 0, invalid)


# ---------------------------------------------------------------------------
# Purity (AC-5.1)
# ---------------------------------------------------------------------------

def test_repeated_calls_are_independent_and_silent(capsys):
    assert evaluate_obstacle(30, 20, True) == "CLEAR"
    assert evaluate_obstacle(30, 2, True) == "BRAKE"
    assert evaluate_obstacle(30, 20, True) == "CLEAR"
    assert capsys.readouterr() == ("", "")


def test_identical_calls_return_same_result():
    first = evaluate_obstacle(30, 7, True)
    second = evaluate_obstacle(30, 7, True)
    assert first == second


# ---------------------------------------------------------------------------
# Module import side-effects (AC-1.1)
# ---------------------------------------------------------------------------

def test_import_has_no_side_effects(capsys):
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
