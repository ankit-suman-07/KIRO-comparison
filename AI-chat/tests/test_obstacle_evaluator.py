"""Acceptance tests for the overview's validation, boundaries and priorities."""

import math
from decimal import Decimal

import pytest

from obstacle_evaluator import evaluate_obstacle


@pytest.mark.parametrize("distance, expected", [
    (0, "BRAKE"), (4.999, "BRAKE"), (5, "BRAKE"),
    (math.nextafter(5, math.inf), "WARNING"), (7.5, "WARNING"),
    (10, "WARNING"), (math.nextafter(10, math.inf), "CLEAR"),
    (100, "CLEAR"),
])
def test_moving_thresholds(distance, expected):
    assert evaluate_obstacle(30, distance, True) == expected


JUST_ABOVE_50 = math.nextafter(50, math.inf)
JUST_ABOVE_15 = math.nextafter(15, math.inf)


@pytest.mark.parametrize("speed, distance, expected", [
    (50, 10, "WARNING"),
    (50, 10.01, "CLEAR"),
    (50, 15, "CLEAR"),
    (JUST_ABOVE_50, 10.01, "WARNING"),
    (JUST_ABOVE_50, 15, "WARNING"),
    (JUST_ABOVE_50, JUST_ABOVE_15, "CLEAR"),
    (60, 15, "WARNING"),
    (60, JUST_ABOVE_15, "CLEAR"),
])
def test_warning_distance_extends_above_50_kmh(speed, distance, expected):
    assert evaluate_obstacle(speed, distance, True) == expected


@pytest.mark.parametrize("speed", [50, JUST_ABOVE_50, 60, 100])
@pytest.mark.parametrize("distance, expected", [
    (5, "BRAKE"),
    (math.nextafter(5, math.inf), "WARNING"),
])
def test_braking_boundary_is_unchanged_at_any_speed(speed, distance, expected):
    assert evaluate_obstacle(speed, distance, True) == expected


def test_high_speed_rule_keeps_fault_priority():
    assert evaluate_obstacle(60, 15, False) == "SENSOR_FAULT"


@pytest.mark.parametrize("speed", [0, 0.0, -0.0, 1, 30.5])
@pytest.mark.parametrize("distance", [0, 5, 10, 100])
def test_sensor_fault_has_highest_priority(speed, distance):
    assert evaluate_obstacle(speed, distance, False) == "SENSOR_FAULT"


@pytest.mark.parametrize("speed", [0, 0.0, -0.0])
@pytest.mark.parametrize("distance", [0, 5, 10, 100])
def test_stopped_vehicle_is_idle(speed, distance):
    assert evaluate_obstacle(speed, distance, True) == "IDLE"


INVALID_READINGS = [None, True, False, "5", "", -1, -0.1,
                    math.inf, -math.inf, math.nan, [], {}, 1j, Decimal("5")]


@pytest.mark.parametrize("invalid", INVALID_READINGS)
@pytest.mark.parametrize("field", ["speed_kmh", "distance_m"])
@pytest.mark.parametrize("healthy", [True, False])
def test_invalid_readings_are_rejected_before_rules(invalid, field, healthy):
    readings = dict(speed_kmh=0, distance_m=0, sensor_healthy=healthy)
    readings[field] = invalid
    with pytest.raises(ValueError):
        evaluate_obstacle(**readings)


@pytest.mark.parametrize("invalid", [None, 0, 1, 0.0, 1.0, "True", "False", [], {}])
def test_sensor_health_requires_boolean(invalid):
    with pytest.raises(ValueError):
        evaluate_obstacle(0, 0, invalid)


@pytest.mark.parametrize("speed", [1, 0.001, 10**1000])
def test_any_positive_speed_counts_as_moving(speed):
    assert evaluate_obstacle(speed, 5, True) == "BRAKE"


def test_large_finite_integer_distance():
    assert evaluate_obstacle(1, 10**1000, True) == "CLEAR"


def test_repeated_calls_are_independent_and_silent(capsys):
    assert evaluate_obstacle(30, 20, True) == "CLEAR"
    assert evaluate_obstacle(30, 2, True) == "BRAKE"
    assert evaluate_obstacle(30, 20, True) == "CLEAR"
    assert capsys.readouterr() == ("", "")
