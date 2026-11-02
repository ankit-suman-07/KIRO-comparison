"""Shared follow-up change tests (evaluation.md CR-1).
Test speeds exactly 50 and just above 50, distances exactly 15 and just above 15,
and the unchanged 5 m braking boundary. Repeat baseline tests with expectations
updated only where the change requires it.
"""
import math
import pytest
from obstacle_evaluator import evaluate_obstacle

just_above_50 = math.nextafter(50, math.inf)

# --- Baseline cases that must be unchanged ---
UNCHANGED_BASELINE = [
    (30,  20,    True,  "CLEAR"),
    (30,  10,    True,  "WARNING"),
    (30,  10.01, True,  "CLEAR"),   # speed 30 < 50, so 10 m still applies
    (30,  5.01,  True,  "WARNING"),
    (30,  5,     True,  "BRAKE"),
    (30,  0,     True,  "BRAKE"),
    (0,   2,     True,  "IDLE"),
    (0,   20,    True,  "IDLE"),
    (30,  20,    False, "SENSOR_FAULT"),
    (0,   0,     False, "SENSOR_FAULT"),
    (0.1, 4.9,   True,  "BRAKE"),
]

@pytest.mark.parametrize("s,d,h,exp", UNCHANGED_BASELINE)
def test_unchanged_baseline(s, d, h, exp):
    assert evaluate_obstacle(s, d, h) == exp

# --- Speed exactly 50: 10 m threshold still applies ---
def test_speed_50_keeps_10m_threshold():
    assert evaluate_obstacle(50, 10,    True) == "WARNING"
    assert evaluate_obstacle(50, 10.01, True) == "CLEAR"
    assert evaluate_obstacle(50, 15,    True) == "CLEAR"

# --- Speed just above 50: 15 m threshold activates ---
def test_speed_just_above_50_uses_15m_threshold():
    assert evaluate_obstacle(just_above_50, 15,                          True) == "WARNING"
    assert evaluate_obstacle(just_above_50, math.nextafter(15, math.inf), True) == "CLEAR"

# --- Speed 60: changed cases ---
def test_speed_60_changed_cases():
    assert evaluate_obstacle(60, 15,    True) == "WARNING"  # was CLEAR at baseline
    assert evaluate_obstacle(60, 15.01, True) == "CLEAR"
    assert evaluate_obstacle(60, 10.01, True) == "WARNING"  # was CLEAR at baseline

# --- Braking threshold unchanged at high speed ---
def test_braking_threshold_unchanged():
    assert evaluate_obstacle(60,  5, True) == "BRAKE"
    assert evaluate_obstacle(100, 5, True) == "BRAKE"
