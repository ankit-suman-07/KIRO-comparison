# Architecture Constraints

## Technology

- Python 3.12 or later; standard library only for application code.
- pytest for automated tests.
- No UI, server, database, network services or Eclipse dependencies.

## Structure

Each implementation directory contains:

```text
obstacle_evaluator.py
tests/
    test_obstacle_evaluator.py
docs/
    project-overview.md
    architecture.md
```

Kiro may additionally generate its specification files. They are development artifacts, not runtime dependencies.

## Public Interface

Expose this function from `obstacle_evaluator.py`:

```python
def evaluate_obstacle(speed_kmh, distance_m, sensor_healthy) -> str:
    ...
```

Use the input validation, rule priority and output statuses defined in `project-overview.md`. Invalid supplied values raise `ValueError`.

## Execution

The evaluator is a pure, deterministic function: identical inputs produce the same result. It must not read user input, print, access files, use randomness or retain state between calls. Importing the module must not execute a demonstration.

Run tests from the implementation directory:

```bash
python -m pytest -q
```

Use the same public interface and constraints for both approaches so the shared acceptance tests can assess them consistently. Internal implementation choices remain open.
