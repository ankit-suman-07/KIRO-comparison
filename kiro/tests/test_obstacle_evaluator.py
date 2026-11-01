"""Acceptance and edge-case tests for the obstacle-warning evaluator.

These tests encode the behaviour defined in ``docs/project-overview.md`` and
the acceptance cases from the root ``evaluation.md``: input validation, rule
priority, exact threshold boundaries and determinism.
"""

import math
from decimal import Decimal

import pytest

from obstacle_evaluator import evaluate_obstacle, STATUSES


# ---------------------------------------------------------------------------
# Rule priority
# ---------------------------------------------------------------------------

def test_statuses_are_exact_uppercase_strings():
    assert STATUSES == ("SENSOR_FAULT", "IDLE", "BRAKE", "WARNING", "CLEAR")
    assert all(isinstance(s, str) and s == s.upper() for s in STATUSES)


@pytest.mark.parametrize("speed", [0, 0.0, -0.0])
@pytest.mark.parametrize("distance", [0, 5, 10, 100])
def test_sensor_fault_has_highest_priority(speed, distance):
    # A faulty sensor wins over a stopped vehicle and any distance.
    assert evaluate_obstacle(speed, distance, False) == "SENSOR_FAULT"


@pytest.mark.parametrize("speed", [0, 0.0, -0.0])
@pytest.mark.parametrize("distance", [0, 5, 10, 100])
def test_stopped_vehicle_is_idle(speed, distance):
    # With a healthy sensor, zero speed is IDLE regardless of distance.
    assert evaluate_obstacle(speed, distance, True) == "IDLE"


@pytest.mark.parametrize("speed", [1, 0.001, 30.5, 10 ** 1000])
def test_any_positive_speed_counts_as_moving(speed):
    assert evaluate_obstacle(speed, 5, True) == "BRAKE"


# ---------------------------------------------------------------------------
# Threshold boundaries (moving vehicle, healthy sensor)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("distance, expected", [
    (0, "BRAKE"), (4.999, "BRAKE"), (5, "BRAKE"),
    (math.nextafter(5, math.inf), "WARNING"), (7.5, "WARNING"),
    (10, "WARNING"), (math.nextafter(10, math.inf), "CLEAR"),
    (100, "CLEAR"),
])
def test_moving_thresholds(distance, expected):
    assert evaluate_obstacle(30, distance, True) == expected


def test_large_finite_integer_distance():
    assert evaluate_obstacle(1, 10 ** 1000, True) == "CLEAR"


# ---------------------------------------------------------------------------
# Follow-up change: extended warning distance above 50 km/h
#
# When speed exceeds 50 km/h the warning distance rises from 10 m to 15 m.
# The braking threshold (5 m) and all other rules are unchanged. Speed
# exactly 50 keeps the 10 m threshold (it does not exceed 50).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("distance, expected", [
    (0, "BRAKE"), (4.999, "BRAKE"), (5, "BRAKE"),
    (math.nextafter(5, math.inf), "WARNING"), (10, "WARNING"),
    (15, "WARNING"), (math.nextafter(15, math.inf), "CLEAR"),
    (100, "CLEAR"),
])
def test_high_speed_extended_warning_threshold(distance, expected):
    # At 60 km/h (exceeds 50) the warning band stretches to 15 m.
    assert evaluate_obstacle(60, distance, True) == expected


def test_speed_exactly_50_keeps_10m_threshold():
    # 50 does not exceed 50, so the 15 m boundary does not apply yet.
    assert evaluate_obstacle(50, 15, True) == "CLEAR"
    assert evaluate_obstacle(50, 10, True) == "WARNING"
    assert evaluate_obstacle(50, math.nextafter(10, math.inf), True) == "CLEAR"


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


# ---------------------------------------------------------------------------
# Acceptance cases from evaluation.md
# ---------------------------------------------------------------------------

ACCEPTANCE_CASES = [
    (30, 20, True, "CLEAR"),
    (30, 10, True, "WARNING"),
    (30, 10.01, True, "CLEAR"),
    (30, 5.01, True, "WARNING"),
    (30, 5, True, "BRAKE"),
    (30, 0, True, "BRAKE"),
    (0, 2, True, "IDLE"),
    (0, 20, True, "IDLE"),
    (30, 20, False, "SENSOR_FAULT"),
    (0, 0, False, "SENSOR_FAULT"),
    (0.1, 4.9, True, "BRAKE"),
]


@pytest.mark.parametrize("speed, distance, healthy, expected", ACCEPTANCE_CASES)
def test_acceptance_cases(speed, distance, healthy, expected):
    assert evaluate_obstacle(speed, distance, healthy) == expected


# ---------------------------------------------------------------------------
# Input validation
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


@pytest.mark.parametrize("speed, distance, invalid", [
    (-1, 20, True),    # negative speed
    (30, -1, True),    # negative distance
])
def test_negative_readings_raise(speed, distance, invalid):
    with pytest.raises(ValueError):
        evaluate_obstacle(speed, distance, invalid)


def test_validation_priority_over_sensor_fault():
    # -1 speed with a faulty sensor: validation must win.
    with pytest.raises(ValueError):
        evaluate_obstacle(-1, 20, False)


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
    import importlib
    import obstacle_evaluator
    importlib.reload(obstacle_evaluator)
    assert capsys.readouterr() == ("", "")
