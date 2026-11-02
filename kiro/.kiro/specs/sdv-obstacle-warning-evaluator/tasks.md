# Implementation Tasks — SDV Obstacle Warning Evaluator

Tasks must be completed in order. Each task is independently verifiable before moving to the next.

---

## Task 1 — Create the project directory structure

**What to do:**
Create the two files that the project requires (initially empty or with a minimal placeholder), matching the layout defined in `design.md` section 2:

```
obstacle_evaluator.py
tests/
    test_obstacle_evaluator.py
```

**Definition of done:**
- Both files exist at the workspace root.
- `obstacle_evaluator.py` contains only a module-level docstring (or is empty).
- `tests/test_obstacle_evaluator.py` contains only a module-level docstring (or is empty).
- Neither file contains any executable statements.

**References:** design.md §2, AC-1.1

---

## Task 2 — Implement `_validate_numeric`

**What to do:**
Add the private helper `_validate_numeric(value, name: str) -> None` to `obstacle_evaluator.py`. This is the only change to the module in this task.

The helper must apply the five validation steps in order (design.md §3.2):
1. Reject `bool` — raise `ValueError` if `isinstance(value, bool)`.
2. Reject non-numeric — raise `ValueError` if not `isinstance(value, (int, float))`.
3. If `value` is a `float`, reject NaN — raise `ValueError` if `_math.isnan(value)`.
4. If `value` is a `float`, reject infinite — raise `ValueError` if `_math.isinf(value)`.
5. Reject negative — raise `ValueError` if `value < 0`.

The `import math as _math` statement must appear at the top of the file.

**Definition of done:**
- `_validate_numeric` is an internal implementation detail. Its underscore prefix signals it is private by convention; it must not be listed or used as part of the public API. (Python does not prevent explicit underscore imports, but no code outside `obstacle_evaluator.py` should reference it.)
- All five steps are applied in the documented order.
- Calling `_validate_numeric(True, "x")` raises `ValueError`.
- Calling `_validate_numeric(-1, "x")` raises `ValueError`.
- Calling `_validate_numeric(float('nan'), "x")` raises `ValueError`.
- Calling `_validate_numeric(float('inf'), "x")` raises `ValueError`.
- Calling `_validate_numeric(10**400, "x")` does **not** raise (large int accepted).
- Calling `_validate_numeric(0, "x")` and `_validate_numeric(0.0, "x")` do not raise.

**References:** FR-2.1, FR-2.2, AC-2.1.1–AC-2.1.9, AC-2.2.1–AC-2.2.9, design.md §3.1, §3.2, §4.1, §4.2

---

## Task 3 — Implement `_validate_sensor`

**What to do:**
Add the private helper `_validate_sensor(value) -> None` to `obstacle_evaluator.py`. This is the only change to the module in this task.

The helper must raise `ValueError` if `not isinstance(value, bool)`.

**Definition of done:**
- `_validate_sensor` is an internal implementation detail. Its underscore prefix signals it is private by convention; it must not be listed or used as part of the public API. (Python does not prevent explicit underscore imports, but no code outside `obstacle_evaluator.py` should reference it.)
- Calling `_validate_sensor(True)` and `_validate_sensor(False)` do not raise.
- Calling `_validate_sensor(1)`, `_validate_sensor(0)`, `_validate_sensor(None)`, and `_validate_sensor("True")` each raise `ValueError`.

**References:** FR-2.3, AC-2.3.1–AC-2.3.6, design.md §3.2

---

## Task 4 — Implement `evaluate_obstacle`

**What to do:**
Add the public function `evaluate_obstacle(speed_kmh, distance_m, sensor_healthy) -> str` to `obstacle_evaluator.py`. This is the only change to the module in this task.

The function must follow the execution order in design.md §3.3 exactly:

1. Call `_validate_numeric(speed_kmh, "speed_kmh")`.
2. Call `_validate_numeric(distance_m, "distance_m")`.
3. Call `_validate_sensor(sensor_healthy)`.
4. Apply the five rules in priority order:
   - `if not sensor_healthy` → return `"SENSOR_FAULT"`
   - `if speed_kmh == 0` → return `"IDLE"`
   - `if distance_m <= 5` → return `"BRAKE"`
   - `if distance_m <= 10` → return `"WARNING"`
   - return `"CLEAR"`

**Definition of done:**
- `evaluate_obstacle` is importable as a public name.
- Importing `obstacle_evaluator` at this point produces no output or side effects.
- The module top-level contains only: `import math as _math`, `_validate_numeric`, `_validate_sensor`, `evaluate_obstacle` — nothing else.
- A quick manual check (or a Python REPL call) confirms:
  - `evaluate_obstacle(0, 5, False)` → `"SENSOR_FAULT"`
  - `evaluate_obstacle(0, 5, True)` → `"IDLE"`
  - `evaluate_obstacle(30, 5, True)` → `"BRAKE"`
  - `evaluate_obstacle(30, 7, True)` → `"WARNING"`
  - `evaluate_obstacle(30, 15, True)` → `"CLEAR"`

**References:** FR-3, FR-4, AC-3.1–AC-3.4, AC-4.1–AC-4.9, design.md §3.3, §4.5

---

## Task 5 — Write tests for input validation

**What to do:**
Implement test cases in `tests/test_obstacle_evaluator.py` covering all input-validation acceptance criteria (FR-2). Group tests clearly by parameter.

Tests to include (minimum — one test function per AC, or grouped where natural):

**`speed_kmh` validation (AC-2.1.x):**
- Valid: `0` (int), `0.0` (float), `30` (int), `30.5` (float) → no error raised.
- Invalid: `True`, `False` → `ValueError`.
- Invalid: `-1`, `-0.1` → `ValueError`.
- Invalid: `float('inf')`, `float('-inf')`, `float('nan')` → `ValueError`.
- Invalid: `None`, `"30"` → `ValueError`.
- Large int: `10**400` → no error raised.

**`distance_m` validation (AC-2.2.x):**
- Valid: `0` (int), `0.0` (float), `10` (int), `10.5` (float) → no error raised.
- Invalid: `True`, `False` → `ValueError`.
- Invalid: `-1`, `-0.1` → `ValueError`.
- Invalid: `float('inf')`, `float('-inf')`, `float('nan')` → `ValueError`.
- Invalid: `None`, `"10"` → `ValueError`.
- Large int: `10**400` → no error raised (result is `"CLEAR"`).

**`sensor_healthy` validation (AC-2.3.x):**
- Valid: `True`, `False` → no error raised.
- Invalid: `1`, `0` → `ValueError`.
- Invalid: `None`, `"True"` → `ValueError`.

**Definition of done:**
- All listed test cases are present.
- `python -m pytest tests/test_obstacle_evaluator.py -q` passes with no failures.

**References:** FR-2, AC-2.1.1–AC-2.1.9, AC-2.2.1–AC-2.2.9, AC-2.3.1–AC-2.3.6, design.md §6

---

## Task 6 — Write tests for rule priority and boundary values

**What to do:**
Implement test cases in `tests/test_obstacle_evaluator.py` covering rule priority (FR-3) and exact output boundary values (FR-4).

**Rule priority (AC-3.x):**
- `evaluate_obstacle(0, 3, False)` → `"SENSOR_FAULT"` (sensor fault beats idle).
- `evaluate_obstacle(100, 2, False)` → `"SENSOR_FAULT"` (sensor fault beats brake).
- `evaluate_obstacle(0, 3, True)` → `"IDLE"` (idle regardless of close distance).
- `evaluate_obstacle(0, 100, True)` → `"IDLE"` (idle regardless of large distance).

**Boundary values (AC-4.x):**
- `evaluate_obstacle(30, 5, True)` → `"BRAKE"` (distance == 5, int, inclusive).
- `evaluate_obstacle(30, 5.0, True)` → `"BRAKE"` (distance == 5.0, float, inclusive).
- `evaluate_obstacle(30, 5.1, True)` → `"WARNING"` (just above 5 m).
- `evaluate_obstacle(30, 10, True)` → `"WARNING"` (distance == 10, int, inclusive).
- `evaluate_obstacle(30, 10.0, True)` → `"WARNING"` (distance == 10.0, float, inclusive).
- `evaluate_obstacle(30, 10.1, True)` → `"CLEAR"` (just above 10 m).
- `evaluate_obstacle(30, 0, True)` → `"BRAKE"` (zero distance, moving vehicle).
- `evaluate_obstacle(30, 100, True)` → `"CLEAR"` (large distance).
- `evaluate_obstacle(0.1, 5, True)` → `"BRAKE"` (minimum non-zero float speed).

**Definition of done:**
- All listed test cases are present.
- `python -m pytest tests/test_obstacle_evaluator.py -q` passes with no failures.

**References:** FR-3, FR-4, AC-3.1–AC-3.4, AC-4.1–AC-4.9, design.md §6

---

## Task 7 — Write tests for purity and module import

**What to do:**
Implement the remaining test cases in `tests/test_obstacle_evaluator.py`.

**Purity (AC-5.1):**
- Call `evaluate_obstacle(30, 7, True)` twice with identical arguments and assert both return the same value.

**Module import (AC-1.1):**
- Use `pytest`'s `capsys` fixture to capture stdout and stderr, then import (or reload) `obstacle_evaluator` within the test. Capture the result of `capsys.readouterr()` once into a variable and assert that both `.out` and `.err` on that variable are empty strings. Checking `sys.modules` alone is not sufficient because it only confirms the module was loaded, not that loading it was side-effect-free.

**Definition of done:**
- Both test cases are present.
- `python -m pytest -q` (full suite) passes with no failures.

**References:** AC-1.1, AC-5.1, FR-5, design.md §6

---

## Task 8 — Final verification

**What to do:**
Run the complete test suite from the workspace root and confirm all tests pass.

```bash
python -m pytest -q
```

Check that:
1. Every test passes (zero failures, zero errors).
2. No warnings about missing imports or incompatible pytest versions.
3. The module can be imported cleanly in a Python REPL without any output.
4. The project contains all required source, test, and documentation files as specified in design.md §2. Tool-generated directories (`__pycache__`, `.pytest_cache`) and spec artefacts (`.kiro/specs/`) are expected and allowed. No additional application source files, packages, or components beyond those in design.md §2 should be present.

**Definition of done:**
- `python -m pytest -q` exits with code 0.
- The project contains all required source, test, and documentation files. Tool-generated cache directories (`__pycache__`, `.pytest_cache`) are expected and allowed.

**References:** AC-6.1, AC-6.2, architecture.md
