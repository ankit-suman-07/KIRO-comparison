# Evaluation Criteria

## Fair Comparison

- Give both approaches identical `project-overview.md` and `architecture.md` files.
- Start each implementation in a separate clean folder. Do not reuse the other implementation's code.
- Prepare and freeze a shared acceptance-test suite before evaluating either result. Run the same suite against both; their generated tests are additional evidence.
- Record AI model/version where available, tool versions and environment differences. Different tools or models can influence the result.
- Compare observed results; do not assume either approach will perform better.

## Acceptance Cases

Call `evaluate_obstacle(speed_kmh, distance_m, sensor_healthy)`.

| Speed km/h | Distance m | Sensor healthy | Expected result |
|---|---|---|---|
| 30 | 20 | `True` | `CLEAR` |
| 30 | 10 | `True` | `WARNING` |
| 30 | 10.01 | `True` | `CLEAR` |
| 30 | 5.01 | `True` | `WARNING` |
| 30 | 5 | `True` | `BRAKE` |
| 30 | 0 | `True` | `BRAKE` |
| 0 | 2 | `True` | `IDLE` |
| 0 | 20 | `True` | `IDLE` |
| 30 | 20 | `False` | `SENSOR_FAULT` |
| 0 | 0 | `False` | `SENSOR_FAULT` |
| 0.1 | 4.9 | `True` | `BRAKE` |
| -1 | 20 | `True` | `ValueError` |
| 30 | -1 | `True` | `ValueError` |
| -1 | 20 | `False` | `ValueError` — validation takes priority |

Also test each numeric input independently with `None`, a string, a Boolean, NaN, positive infinity and negative infinity; expect `ValueError`. Test `sensor_healthy` with `None`, a string and numeric values such as `0` and `1`; expect `ValueError`.

Check that results are exact uppercase strings, repeated calls are consistent, and imports/calls produce no printing or other prohibited side effects.

## Comparison Measures

Record these in the root `comparison-notes.md`:

| Measure | Record for each approach |
|---|---|
| Correctness | Shared tests passed/total on first evaluation and after corrections |
| Effort | Setup time separately; total task time including spec review, coding and corrections |
| Human involvement | Clarifications, review decisions and corrective requests |
| Traceability | How a rule connects to code and tests; one concrete example |
| Change handling | Whether code, tests and relevant documents stay consistent after the same change |

## Follow-up Change

After recording baseline results for both, give both this same change:

> When speed exceeds 50 km/h, increase the warning distance to 15 metres. Keep the braking threshold and all other rules unchanged.

Test speeds exactly `50` and just above `50`, distances exactly `15` and just above `15`, and the unchanged 5-metre braking boundary. Repeat baseline tests with expectations updated only where the change requires it.

Keep baseline and changed-version results separate. A single toy task demonstrates workflow differences; it does not establish general superiority.
