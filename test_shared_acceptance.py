"""Shared acceptance tests derived from evaluation.md — baseline only.
These cases must pass for both implementations before and after any change.
"""
import math
import pytest
from obstacle_evaluator import evaluate_obstacle

# --- Table 1: baseline acceptance cases (evaluation.md) ---
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
]

@pytest.mark.parametrize("s,d,h,exp", ACCEPTANCE_CASES)
def test_acceptance_baseline(s, d, h, exp):
    assert evaluate_obstacle(s, d, h) == exp

# --- ValueError cases ---
@pytest.mark.parametrize("s,d,h", [(-1, 20, True), (30, -1, True), (-1, 20, False)])
def test_acceptance_value_error(s, d, h):
    with pytest.raises(ValueError):
        evaluate_obstacle(s, d, h)

# --- Type validation ---
TYPE_INVALID = [None, "5", True, False, math.nan, math.inf, -math.inf]

@pytest.mark.parametrize("invalid", TYPE_INVALID)
@pytest.mark.parametrize("field", ["speed_kmh", "distance_m"])
def test_numeric_type_invalid(invalid, field):
    kwargs = dict(speed_kmh=0, distance_m=0, sensor_healthy=True)
    kwargs[field] = invalid
    with pytest.raises(ValueError):
        evaluate_obstacle(**kwargs)

@pytest.mark.parametrize("invalid", [None, "True", 0, 1])
def test_sensor_type_invalid(invalid):
    with pytest.raises(ValueError):
        evaluate_obstacle(0, 0, invalid)

# --- Output format and purity ---
def test_repeated_calls_consistent():
    assert evaluate_obstacle(30, 7, True) == evaluate_obstacle(30, 7, True)

def test_no_side_effects(capsys):
    evaluate_obstacle(30, 20, True)
    assert capsys.readouterr() == ("", "")
