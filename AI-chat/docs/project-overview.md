# SDV Obstacle Warning Evaluator

## Goal

Build a small Python function that evaluates vehicle speed, front obstacle distance and sensor health, then returns a status. 

## Inputs

| Input | Meaning | Valid values |
|---|---|---|
| `speed_kmh` | Vehicle speed in kilometres per hour | Finite, non-negative `int` or `float`; Boolean values are invalid |
| `distance_m` | Front obstacle distance in metres | Finite, non-negative `int` or `float`; Boolean values are invalid |
| `sensor_healthy` | Whether the distance sensor is healthy | `True` or `False` only |

## Behaviour

Validate all inputs first. Raise `ValueError` for invalid inputs, including missing values passed as `None`, strings, negative numbers, infinity and NaN. Do not silently convert input types.

For valid inputs, apply the following rules in order and return exactly one uppercase status string:

| Priority | Condition | Status |
|---|---|---|
| 1 | Sensor is unhealthy | `SENSOR_FAULT` |
| 2 | Speed equals zero | `IDLE` |
| 3 | Vehicle is moving and distance is at most 5 metres | `BRAKE` |
| 4 | Vehicle is moving and distance is greater than 5 and at most 10 metres | `WARNING` |
| 5 | Vehicle is moving and distance is greater than 10 metres | `CLEAR` |

Sensor failure therefore takes priority over a stopped vehicle. With a healthy sensor, a stopped vehicle returns `IDLE` regardless of valid obstacle distance.

## Scope

- One evaluator function and automated pytest tests.
- No graphical interface, simulator, database, network connection or Eclipse components.
- Speed and distance are supplied as values; no real sensor hardware is required.
- Both implementations must follow this same behaviour, including exact threshold boundaries.