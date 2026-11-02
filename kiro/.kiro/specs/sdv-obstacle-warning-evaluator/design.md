# Design — SDV Obstacle Warning Evaluator

## 1. Overview

`obstacle_evaluator.py` is a single-file Python module that implements the `evaluate_obstacle` function. It has no runtime dependencies outside the Python standard library, no I/O, no state, and no public surface beyond the one required function.

---

## 2. File Layout

Matches the structure mandated by `docs/architecture.md`:

```
obstacle_evaluator.py          # application module (public function + private helpers)
tests/
    test_obstacle_evaluator.py # pytest test suite
docs/
    project-overview.md
    architecture.md
```

The `.kiro/specs/` directory holds development artefacts (requirements, design, tasks) and is not a runtime dependency.

---

## 3. Module Structure

### 3.1 Imports

Only the Python standard library is used. The `math` module is needed to detect `inf` and `NaN` in float values. It is imported under a private alias so it does not become an additional public name on the module:

```python
import math as _math
```

No other import is required.

### 3.2 Private helpers

Two private helpers keep validation logic readable and avoid repeating the same checks. Neither is part of the public interface.

#### `_validate_numeric(value, name: str) -> None`

Checks that a single numeric argument (`speed_kmh` or `distance_m`) is valid. Raises `ValueError` with a descriptive message if any rule is violated.

Validation steps (applied in order):
1. Reject `bool` — `isinstance(value, bool)` must be `False`.
2. Reject non-numeric — `isinstance(value, (int, float))` must be `True`.
3. If the value is a `float`, reject `NaN` — `_math.isnan(value)` must be `False`.
4. If the value is a `float`, reject infinite — `_math.isinf(value)` must be `False`.
5. Reject negative — `value < 0` must be `False`.

Python `int` values are always mathematically finite (arbitrary precision), so steps 3 and 4 are skipped for integers. This means values such as `10**400` are accepted without triggering an `OverflowError` that would occur if `math.isfinite` were called on a very large integer cast to float.

#### `_validate_sensor(value) -> None`

Checks that `sensor_healthy` is exactly a `bool`. Raises `ValueError` if not.

Validation steps:
1. `isinstance(value, bool)` must be `True`. This simultaneously rejects `int`, `float`, `str`, `None`, and every other type (because in Python `bool` is a subclass of `int`, the check must be `isinstance(value, bool)`, not `isinstance(value, int)`).

### 3.3 Public function

```python
def evaluate_obstacle(speed_kmh, distance_m, sensor_healthy) -> str:
```

**Execution order (no step may be skipped or reordered):**

1. **Validate all inputs** — call `_validate_numeric(speed_kmh, "speed_kmh")`, then `_validate_numeric(distance_m, "distance_m")`, then `_validate_sensor(sensor_healthy)`. If any raises `ValueError`, it propagates immediately; the remaining validations and all business logic are skipped.
2. **Apply rules in priority order:**
   1. `if not sensor_healthy` → return `"SENSOR_FAULT"`
   2. `if speed_kmh == 0` → return `"IDLE"`
   3. `if distance_m <= 5` → return `"BRAKE"`
   4. `if distance_m <= 10` → return `"WARNING"`
   5. return `"CLEAR"`

   (Steps 3–5 are only reached when `speed_kmh > 0`, which is guaranteed by step 2 having not matched.)

---

## 4. Decision Rationale

### 4.1 Why apply `_math.isnan` / `_math.isinf` only to `float` values?

Python `int` is arbitrary-precision and always finite, so calling `math.isnan` or `math.isinf` on a very large integer (e.g. `10**400`) would require converting it to `float` first, which raises `OverflowError`. Guarding with `isinstance(value, float)` before those checks avoids the error and correctly accepts arbitrarily large integers. `float` values still go through both checks as before.

### 4.2 Why check `isinstance(value, bool)` before `isinstance(value, (int, float))`?

In Python, `bool` is a subclass of `int`, so `isinstance(True, int)` is `True`. Without the leading bool guard, `True` and `False` would silently pass the numeric type check and evaluate as `1` and `0` respectively, violating FR-2.1 and FR-2.2.

### 4.3 Why import `math` as `_math`?

A bare `import math` would expose `math` as a public attribute of the module. Using `import math as _math` follows the convention that `_`-prefixed names are private, keeping the public surface limited to `evaluate_obstacle` only (AC-1.3).

### 4.4 Why two private helpers instead of inline validation?

The same five-step numeric check applies to both `speed_kmh` and `distance_m`. Extracting it to `_validate_numeric` avoids duplication and makes it straightforward to verify that both parameters are validated identically. The sensor check is separate because the rules for `sensor_healthy` are fundamentally different (must be `bool`, not numeric).

### 4.5 Why no `elif` chain for rules 3–5?

After rules 1 and 2, `speed_kmh > 0` is guaranteed. Rules 3–5 then partition `distance_m` into three non-overlapping ranges: `[0, 5]`, `(5, 10]`, `> 10`. A simple chain of `if / if / return` is sufficient and mirrors the table in the spec directly.

### 4.6 Why no `if __name__ == "__main__"` block?

The architecture document explicitly states: "Importing the module must not execute a demonstration." No demonstration code exists, so no guard is needed. The absence of such a block is intentional.

---

## 5. Data Flow Diagram

```
evaluate_obstacle(speed_kmh, distance_m, sensor_healthy)
        │
        ▼
┌───────────────────────────────┐
│ _validate_numeric(speed_kmh)  │──► ValueError (if invalid)
└───────────────────────────────┘
        │ (valid)
        ▼
┌────────────────────────────────┐
│ _validate_numeric(distance_m)  │──► ValueError (if invalid)
└────────────────────────────────┘
        │ (valid)
        ▼
┌───────────────────────────────┐
│ _validate_sensor(sensor_healthy)│──► ValueError (if invalid)
└───────────────────────────────┘
        │ (valid)
        ▼
┌─────────────────────────────────────┐
│ not sensor_healthy?                 │──► "SENSOR_FAULT"
│   no → speed_kmh == 0?             │──► "IDLE"
│     no → distance_m <= 5?          │──► "BRAKE"
│       no → distance_m <= 10?       │──► "WARNING"
│         no                         │──► "CLEAR"
└─────────────────────────────────────┘
```

---

## 6. Test Strategy

All tests live in `tests/test_obstacle_evaluator.py` and are run with:

```bash
python -m pytest -q
```

Tests are grouped by concern:

| Group | What it covers |
|---|---|
| Input validation — `speed_kmh` | All AC-2.1.x: valid types/values, bool rejection, negative, inf, NaN, None, string; `10**400` accepted |
| Input validation — `distance_m` | All AC-2.2.x: same rules as above; `10**400` accepted |
| Input validation — `sensor_healthy` | All AC-2.3.x: True/False accepted; int, None, string rejected |
| Rule priority | AC-3.1 – AC-3.4: sensor fault beats idle, idle beats distance rules |
| Boundary values | AC-4.1 – AC-4.9: exact thresholds at 5 m and 10 m (int and float) |
| Large integer inputs | `evaluate_obstacle(10**400, 5, True)` returns `"BRAKE"`; `evaluate_obstacle(30, 10**400, True)` returns `"CLEAR"` — no `OverflowError` |
| Purity | AC-5.1: same inputs → same output on repeated calls |
| Module import | AC-1.1: importing the module produces no side effects |

No mocking, patching, or fixtures are needed. Every test is a direct call to `evaluate_obstacle` with literal arguments and an `assert` or `pytest.raises` check.

---

## 7. Constraints Checklist

| Constraint | How it is satisfied |
|---|---|
| Python 3.12+ | Only standard-library features; no walrus-operator pitfalls or version-specific syntax |
| Standard library only | `import math as _math` is the sole import; private alias keeps `math` off the public namespace |
| No side effects on import | Module top-level contains only `import math as _math`, three `def` statements; no executable statements |
| Pure / deterministic | No global mutable state, no I/O, no randomness |
| `ValueError` for invalid inputs | Both helpers raise `ValueError` with a message; nothing is silently coerced |
| Exact status strings | String literals appear once each in the function body; no dynamic construction |
| pytest | Test file uses `pytest.raises` and plain `assert`; no unittest or other framework |

---

## Change Request CR-1 — Speed-Dependent Warning Distance

**Requested change (from CR-1 in requirements.md):** When speed exceeds 50 km/h, increase the warning distance to 15 metres. Keep the braking threshold and all other rules unchanged.

### Updated §3.3 — Rule Application (CR-1)

Rule 4 in the execution order from §3.3 is replaced. All other steps remain identical.

Before CR-1:
```
4. if distance_m <= 10  → return "WARNING"
```

After CR-1:
```
4. warning_distance = 15 if speed_kmh > 50 else 10
   if distance_m <= warning_distance  → return "WARNING"
```

Speed exactly 50 does not exceed 50, so it keeps the 10 m threshold. The braking threshold (5 m) is unaffected by speed.

### New §4.7 — Why compute `warning_distance` inline? (CR-1)

The warning threshold depends on speed: 10 m when `speed_kmh <= 50`, 15 m when `speed_kmh > 50`. A single inline ternary `15 if speed_kmh > 50 else 10` keeps both threshold values in one place and makes the condition explicit. Using `>` (not `>=`) ensures speed exactly 50 keeps the 10 m threshold, since 50 does not exceed 50.

An alternative using a named constant would require either two constants or a function — both add indirection without benefit for a two-value rule. The ternary mirrors the spec table directly.

### Updated §5 — Data Flow Diagram (CR-1)

```
│     no → distance_m <= 5?                  │──► "BRAKE"
│       no → warning = 15 if spd>50 else 10  │
│             distance_m <= warning?          │──► "WARNING"
│               no                           │──► "CLEAR"
```

All other nodes in the diagram from §5 are unchanged.

### Updated §6 — Test Strategy (CR-1)

A new test group is added:

| Group | What it covers |
|---|---|
| Speed-dependent threshold | AC-4.10–AC-4.21: speed exactly 50 (10 m threshold), speed just above 50 (15 m threshold), 15 m boundary inclusive/exclusive, braking threshold unchanged |

All existing test groups from §6 remain. Baseline cases (speed 30, 10 m threshold) are re-run to confirm no regressions.
