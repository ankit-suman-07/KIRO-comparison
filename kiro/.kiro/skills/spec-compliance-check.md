# Skill: Spec Compliance Check

## Purpose

Before changing any implementation file or test, verify that the proposed change
is consistent with every authoritative spec document. Never update a spec document
to match an implementation; always go the other direction.

---

## Step 1 — Read the authoritative sources first

Read **all** of the following before touching any code or test:

1. `docs/project-overview.md` — behaviour, rules, thresholds, and scope
2. `docs/architecture.md` — technology constraints, public interface, file layout
3. `.kiro/specs/{feature}/requirements.md` — functional requirements and acceptance criteria
4. `.kiro/specs/{feature}/design.md` — implementation design and rationale
5. `.kiro/specs/{feature}/tasks.md` — task definitions and definitions of done

If any file is missing, note it and continue with what exists.

---

## Step 2 — Identify the authoritative rule for every disputed behaviour

For each behaviour in question (threshold values, rule priority, validation logic,
public interface, etc.), record:

- What **every** spec document says about it
- Whether the documents agree with each other
- Whether the current implementation matches the documents

If documents disagree with each other, report the contradiction to the user
**before making any edits**.

---

## Step 3 — Check the implementation against the spec

Compare `obstacle_evaluator.py` (or the relevant module) against the spec:

| Item | Spec says | Implementation has | Match? |
|---|---|---|---|
| Public names | `evaluate_obstacle` only (AC-1.3) | … | … |
| Warning threshold | fixed 10 m (FR-3/FR-4) | … | … |
| Private helpers | `_validate_numeric`, `_validate_sensor` (design §3.2) | … | … |
| Validation order | speed → distance → sensor (design §3.3) | … | … |
| Rule priority order | SENSOR_FAULT → IDLE → BRAKE → WARNING → CLEAR | … | … |

Fill in the table from what you actually read; do not guess.

---

## Step 4 — Check the tests against the spec

For each test or test group, verify:

- Every AC listed in requirements.md has at least one corresponding test.
- No test asserts behaviour that contradicts the spec (e.g. wrong threshold,
  extra public API, wrong return value at a boundary).
- Tests that reference constants, helpers, or behaviours not in the spec are flagged
  for removal or correction.

Key ACs to cross-check explicitly:

- AC-4.1 – AC-4.6: exact 5 m and 10 m boundary values
- AC-3.1 – AC-3.4: rule priority (sensor fault, idle)
- AC-2.1.x – AC-2.3.x: input validation
- AC-1.1: no side effects on import
- AC-5.1: determinism

---

## Step 5 — Report before editing

Before making any change, write a short report:

```
## Compliance report

### Spec says
<one line per relevant rule, cited to the document>

### Implementation currently does
<one line per discrepancy>

### Tests currently assert
<one line per test that is wrong or missing>

### Proposed changes
<list only the minimum edits needed to bring code and tests into line with the spec>

### Ambiguities
<anything that is unclear across documents — ask the user to resolve before proceeding>
```

Do **not** start editing until the user has reviewed the report and confirmed
there are no ambiguities, or the ambiguities are trivially unambiguous.

---

## Step 6 — Apply only the minimum necessary changes

- Fix the implementation to match the spec. Do not refactor unrelated code.
- Fix or remove tests that contradict the spec.
- Add tests only for ACs that have no coverage.
- Never update a spec document (requirements.md, design.md, tasks.md,
  project-overview.md, architecture.md) to match the implementation.
  If the spec needs updating, that is a separate decision requiring explicit
  user approval.

---

## Step 7 — Verify

Run the test suite and confirm all tests pass:

```bash
python -m pytest -v
```

Report the final pass count and list every file that was changed with a one-line
summary of what changed and why.

---

## Key rules (never break these)

- Read docs **before** forming any opinion about what the code should do.
- Spec documents are the source of truth; implementations and tests are derived artifacts.
- If a branch or merge introduces behaviour not present in any spec document,
  that behaviour is unapproved until the user explicitly says otherwise.
- Bracketed alternatives or unresolved options in a prompt are **not** approval.
- If in doubt, report the ambiguity and wait for the user's decision.
