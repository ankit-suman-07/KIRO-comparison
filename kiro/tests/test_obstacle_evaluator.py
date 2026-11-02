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
import sys

import pytest

from obstacle_evaluator import evaluate_obstacle


# ---------------------------------------------------------------------------
# Input validation — speed_kmh (AC-2.1.x)
# ---------------------------------------------------------------------------

class TestSpeedValidation:
    """Valid speed_kmh values are accepted; invalid ones raise ValueError."""

    # Valid inputs (AC-2.1.1, AC-2.1.2)
    def test_speed_zero_int_is_valid(self):
        assert evaluate_obstacle(0, 5, True) == "IDLE"

    def test_speed_zero_float_is_valid(self):
        assert evaluate_obstacle(0.0, 5, True) == "IDLE"

    def test_speed_positive_int_is_valid(self):
        assert evaluate_obstacle(30, 15, True) == "CLEAR"

    def test_speed_positive_float_is_valid(self):
        assert evaluate_obstacle(30.5, 15, True) == "CLEAR"

    # bool rejected (AC-2.1.3, AC-2.1.4)
    def test_speed_true_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(True, 5, True)

    def test_speed_false_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(False, 5, True)

    # Negative (AC-2.1.5)
    def test_speed_negative_int_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(-1, 5, True)

    def test_speed_negative_float_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(-0.1, 5, True)

    # Infinity (AC-2.1.6)
    def test_speed_positive_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(float("inf"), 5, True)

    def test_speed_negative_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(float("-inf"), 5, True)

    # NaN (AC-2.1.7)
    def test_speed_nan_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(float("nan"), 5, True)

    # None (AC-2.1.8)
    def test_speed_none_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(None, 5, True)

    # String (AC-2.1.9)
    def test_speed_string_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle("30", 5, True)

    # Large integer accepted (design.md §6 large integer row)
    def test_speed_large_int_accepted(self):
        # 10**400 is a valid non-negative int; obstacle at 5 m → BRAKE
        assert evaluate_obstacle(10 ** 400, 5, True) == "BRAKE"


# ---------------------------------------------------------------------------
# Input validation — distance_m (AC-2.2.x)
# ---------------------------------------------------------------------------

class TestDistanceValidation:
    """Valid distance_m values are accepted; invalid ones raise ValueError."""

    # Valid inputs (AC-2.2.1, AC-2.2.2)
    def test_distance_zero_int_is_valid(self):
        assert evaluate_obstacle(30, 0, True) == "BRAKE"

    def test_distance_zero_float_is_valid(self):
        assert evaluate_obstacle(30, 0.0, True) == "BRAKE"

    def test_distance_positive_int_is_valid(self):
        assert evaluate_obstacle(30, 10, True) == "WARNING"

    def test_distance_positive_float_is_valid(self):
        assert evaluate_obstacle(30, 10.5, True) == "CLEAR"

    # bool rejected (AC-2.2.3, AC-2.2.4)
    def test_distance_true_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, True, True)

    def test_distance_false_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, False, True)

    # Negative (AC-2.2.5)
    def test_distance_negative_int_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, -1, True)

    def test_distance_negative_float_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, -0.1, True)

    # Infinity (AC-2.2.6)
    def test_distance_positive_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, float("inf"), True)

    def test_distance_negative_inf_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, float("-inf"), True)

    # NaN (AC-2.2.7)
    def test_distance_nan_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, float("nan"), True)

    # None (AC-2.2.8)
    def test_distance_none_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, None, True)

    # String (AC-2.2.9)
    def test_distance_string_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, "10", True)

    # Large integer accepted (design.md §6 large integer row)
    def test_distance_large_int_accepted(self):
        # 10**400 >> 10 m → CLEAR
        assert evaluate_obstacle(30, 10 ** 400, True) == "CLEAR"


# ---------------------------------------------------------------------------
# Input validation — sensor_healthy (AC-2.3.x)
# ---------------------------------------------------------------------------

class TestSensorValidation:
    """True/False are accepted; everything else raises ValueError."""

    # Valid (AC-2.3.1, AC-2.3.2)
    def test_sensor_true_is_valid(self):
        assert evaluate_obstacle(30, 10, True) == "WARNING"

    def test_sensor_false_is_valid(self):
        assert evaluate_obstacle(30, 10, False) == "SENSOR_FAULT"

    # int 1 and 0 rejected (AC-2.3.3, AC-2.3.4)
    def test_sensor_int_one_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, 10, 1)

    def test_sensor_int_zero_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, 10, 0)

    # None (AC-2.3.5)
    def test_sensor_none_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, 10, None)

    # String (AC-2.3.6)
    def test_sensor_string_raises(self):
        with pytest.raises(ValueError):
            evaluate_obstacle(30, 10, "True")


# ---------------------------------------------------------------------------
# Rule priority (AC-3.x)
# ---------------------------------------------------------------------------

class TestRulePriority:
    """Sensor fault overrides all; idle overrides distance rules."""

    def test_sensor_fault_overrides_idle_speed(self):
        # AC-3.1: speed=0, sensor=False → SENSOR_FAULT (not IDLE)
        assert evaluate_obstacle(0, 3, False) == "SENSOR_FAULT"

    def test_sensor_fault_overrides_brake_distance(self):
        # AC-3.2: distance within brake range, sensor=False → SENSOR_FAULT
        assert evaluate_obstacle(100, 2, False) == "SENSOR_FAULT"

    def test_idle_overrides_close_distance(self):
        # AC-3.3: speed=0, distance=3 → IDLE (not BRAKE)
        assert evaluate_obstacle(0, 3, True) == "IDLE"

    def test_idle_overrides_large_distance(self):
        # AC-3.4: speed=0, distance=100 → IDLE (not CLEAR)
        assert evaluate_obstacle(0, 100, True) == "IDLE"


# ---------------------------------------------------------------------------
# Boundary values (AC-4.x)
# ---------------------------------------------------------------------------

class TestBoundaryValues:
    """Exact threshold boundaries at 5 m and 10 m."""

    def test_distance_5_int_returns_brake(self):
        # AC-4.1: distance == 5 (int), inclusive → BRAKE
        assert evaluate_obstacle(30, 5, True) == "BRAKE"

    def test_distance_5_float_returns_brake(self):
        # AC-4.2: distance == 5.0 (float), inclusive → BRAKE
        assert evaluate_obstacle(30, 5.0, True) == "BRAKE"

    def test_distance_5_1_returns_warning(self):
        # AC-4.3: distance just above 5 m → WARNING
        assert evaluate_obstacle(30, 5.1, True) == "WARNING"

    def test_distance_10_int_returns_warning(self):
        # AC-4.4: distance == 10 (int), inclusive → WARNING
        assert evaluate_obstacle(30, 10, True) == "WARNING"

    def test_distance_10_float_returns_warning(self):
        # AC-4.5: distance == 10.0 (float), inclusive → WARNING
        assert evaluate_obstacle(30, 10.0, True) == "WARNING"

    def test_distance_10_1_returns_clear(self):
        # AC-4.6: distance just above 10 m → CLEAR
        assert evaluate_obstacle(30, 10.1, True) == "CLEAR"

    def test_zero_distance_moving_vehicle_returns_brake(self):
        # AC-4.7: distance=0, speed>0 → BRAKE
        assert evaluate_obstacle(30, 0, True) == "BRAKE"

    def test_large_distance_moving_vehicle_returns_clear(self):
        # AC-4.8: distance=100 → CLEAR
        assert evaluate_obstacle(30, 100, True) == "CLEAR"

    def test_minimum_nonzero_float_speed_returns_brake(self):
        # AC-4.9: speed=0.1 (non-zero float), distance=5 → BRAKE
        assert evaluate_obstacle(0.1, 5, True) == "BRAKE"


# ---------------------------------------------------------------------------
# Purity (AC-5.1)
# ---------------------------------------------------------------------------

class TestPurity:
    """Identical inputs always produce the same output."""

    def test_identical_calls_return_same_result(self):
        first = evaluate_obstacle(30, 7, True)
        second = evaluate_obstacle(30, 7, True)
        assert first == second


# ---------------------------------------------------------------------------
# Module import side-effects (AC-1.1)
# ---------------------------------------------------------------------------

class TestModuleImport:
    """Importing obstacle_evaluator must not produce stdout or stderr."""

    def test_import_produces_no_output(self, capsys):
        # Remove the cached module so the import actually executes again.
        sys.modules.pop("obstacle_evaluator", None)
        importlib.import_module("obstacle_evaluator")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""
