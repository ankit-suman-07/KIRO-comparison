# SDV Obstacle Warning Evaluator

A pure Python function that evaluates speed, front obstacle distance and sensor
health. Application code uses only the standard library. Requires Python 3.12+.

## Setup and tests

From this directory:

```bash
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS, or
`.venv\Scripts\Activate.ps1` in Windows PowerShell. Then:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Run an evaluation

```bash
python -c "from obstacle_evaluator import evaluate_obstacle; print(evaluate_obstacle(30, 7, True))"
```

Output: `WARNING`.

All values are validated first; invalid values raise `ValueError`. Speed and
distance must be finite, non-negative integers or floats (excluding booleans).
Sensor health must be a boolean. For valid inputs, rules run in this order:

1. Unhealthy sensor: `SENSOR_FAULT`.
2. Zero speed: `IDLE`.
3. Distance at most 5 m: `BRAKE`.
4. Distance at most 10 m: `WARNING` (extends to 15 m when speed exceeds 50 km/h).
5. Otherwise: `CLEAR`.

The function has no I/O or persistent state. Importing it runs no demonstration.
See `docs/project-overview.md` and `docs/architecture.md` for the supplied spec.
