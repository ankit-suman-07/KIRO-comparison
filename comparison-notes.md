# AI Chat and Kiro Comparison Notes

## Baseline Results

| Item | AI chat | Kiro Spec mode |
|---|---|---|
| Tool and model/version, if available | ChatGPT (GPT-4o) | Kiro (Claude-based) |
| Python and pytest versions | Python 3.9.6 / pytest 8.4.2 | Python 3.9.6 / pytest 8.4.2 |
| Setup time | — | — |
| Total task time, including review and corrections | — | — |
| Shared baseline tests passed / total on first evaluation | 34 / 34 | 34 / 34 |
| Shared baseline tests passed / total after corrections | 34 / 34 (no corrections needed) | 34 / 34 (no corrections needed) |
| Clarification questions | 0 | 0 |
| Human corrective requests | 0 | 1 — merge conflict resolution required manual intervention to reconcile two parallel Kiro implementations; the follow-up change was temporarily reverted to restore spec-defined baseline |
| Human code edits, if any | 0 | 0 (conflict resolved by team member, not manual logic edit) |
| Files/artifacts produced | `obstacle_evaluator.py`, `tests/test_obstacle_evaluator.py`, `README.md`, `requirements-dev.txt` | Same runtime files plus `.kiro/specs/sdv-obstacle-warning-evaluator/requirements.md`, `design.md`, `tasks.md` |
| Example linking one rule to code and a test | Rule: "distance ≤ 5 → BRAKE" → code: `if distance_m <= 5: return "BRAKE"` → test: `test_distance_5_int_returns_brake` | Rule: AC-4.1 in `requirements.md` → `if distance_m <= 5: return "BRAKE"` in `obstacle_evaluator.py` → `test_distance_5_int_returns_brake` in `tests/test_obstacle_evaluator.py` |

Save the baseline result or commit before introducing the follow-up change.

## Follow-up Change Results

Change: increase warning distance to 15 metres when speed exceeds 50 km/h; keep all other rules unchanged.

| Item | AI chat | Kiro Spec mode |
|---|---|---|
| Time to implement and verify the change | Not applied — AI-chat folder left at baseline intentionally | — |
| Shared follow-up tests passed / total on first evaluation | 13 / 15 (fails at speed > 50: returns CLEAR instead of WARNING) | 15 / 15 |
| Shared follow-up tests passed / total after corrections | Not applied | 15 / 15 (no corrections needed) |
| Human corrections or edits needed | N/A | 0 |
| Code, tests and documentation updated consistently? | No — change not applied; code, tests and spec all remain at baseline | Yes — `obstacle_evaluator.py`, `tests/test_obstacle_evaluator.py`, `requirements.md` (CR-1 section), `design.md` (CR-1 section), and `README.md` all updated |
| Any regressions in unchanged behaviour? | N/A | No — all 34 baseline shared cases continue to pass; braking threshold at 5 m unaffected |

### Why 13/15 for AI chat on the follow-up suite?

The AI-chat implementation was not changed. Running the follow-up shared tests against it reveals exactly 2 failures — both in the cases that require the 15 m threshold at speed > 50 km/h:

- `evaluate_obstacle(just_above_50, 15, True)` → returns `CLEAR` (expected `WARNING`)
- `evaluate_obstacle(60, 10.01, True)` → returns `CLEAR` (expected `WARNING`)

This is the expected outcome: the AI-chat code still uses a fixed 10 m threshold. The 13 cases that pass (braking boundary, speed-exactly-50 behaviour, sensor fault, IDLE) are unchanged by the follow-up change and correctly pass on the unmodified code.

## Kiro Follow-up Change Details

The change introduced a speed-dependent warning threshold in `obstacle_evaluator.py`:

```python
warning_distance = 15 if speed_kmh > 50 else 10
if distance_m <= warning_distance:
    return "WARNING"
```

New boundary cases added to tests (AC-4.10–AC-4.21 in CR-1):
- Speed exactly 50: 10 m threshold still applies (`evaluate_obstacle(50, 10, True)` → `WARNING`; `evaluate_obstacle(50, 15, True)` → `CLEAR`)
- Speed just above 50: 15 m threshold applies (`evaluate_obstacle(50+ε, 15, True)` → `WARNING`)
- Speed 60: distance 10.01 m that was `CLEAR` at baseline is now `WARNING`
- Braking threshold unaffected: `evaluate_obstacle(100, 5, True)` still returns `BRAKE`

Spec artifacts updated with a CR-1 section appended (originals preserved):
- `requirements.md`: CR-1 section adds updated FR-3/FR-4 and AC-4.10–AC-4.21; original FRs untouched
- `design.md`: CR-1 section adds updated execution steps, §4.7 rationale, updated diagram; original sections untouched

## Important Observations

- **AI chat:** Produced correct, compact code in one shot with no clarifying questions. The implementation is 33 lines including docstring. The test suite (8 parametrized functions, 110 total cases) covers all baseline acceptance criteria. However, when a change was needed there was no spec artifact to consult — knowing *which* tests to update and *which* behaviour should remain unchanged required re-reading the original brief. Without the change being applied, 2 out of 15 follow-up shared tests fail, exposing exactly the unimplemented behaviour.

- **Kiro:** The spec-first workflow produced a larger artifact set: `requirements.md` (numbered FRs and ACs), `design.md` (decision rationale, data flow diagram, constraint checklist), and `tasks.md` (8 ordered implementation tasks). This created an explicit chain from requirement → design decision → code line → test ID. For the follow-up change, the spec told exactly which rule to amend (FR-3 row 4), which boundary values to test (speed exactly 50, just above 50, 15 m inclusive/exclusive), and which existing ACs to re-run to confirm no regression. The human intervention required was not about logic errors — it was a merge conflict between two parallel implementations.

- **Traceability example (Kiro):** AC-4.1 in `requirements.md` states `evaluate_obstacle(30, 5, True)` must return `"BRAKE"`. Design §3.3 documents this as `if distance_m <= 5: return "BRAKE"`. Test `test_distance_5_int_returns_brake` in `test_obstacle_evaluator.py` asserts exactly this call. The chain is explicit and navigable in both directions.

- **Traceability example (AI chat):** The README lists "Distance at most 5 m: BRAKE" and the code has `if distance_m <= 5: return "BRAKE"`. Test `test_moving_thresholds` covers this boundary via parametrize. The link exists but is informal — no numbered AC ties them together.

- **Conclusion:** Both approaches produced correct baseline implementations. The difference became apparent on the follow-up change: AI-chat had no spec to guide which rules, tests, and documents needed updating, while Kiro's numbered ACs and CR-1 structure made the scope of the change explicit and verifiable. For the larger SDV project — where safety rules must be traceable to requirements, multiple engineers collaborate, and functional changes must be audited — the Kiro SDD workflow provides a traceability scaffold that the prompt-engineering approach lacks.
