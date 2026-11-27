---
name: combine-triz-navigator
description: "[cheap] Conditional TRIZ entry across Combine stages: map the active symptom or pipeline stage to one small reference."
---

# TRIZ Navigator

Use **after Dialogue has recorded the goal and hard constraints**. Do not use for a clear routine task. If the task itself is unclear, return to Combine Dialogue rather than forcing a contradiction.

Codes: **A** = `combine-triz-ariz`, **M** = `combine-triz-modeling`, **P** = `combine-triz-principles`. Invoke the named skill, then read only the reference for that code.

| Symptom after task clarification | Route | Required output |
|---|---|---|
| Deadlock; every option violates a constraint | A1 | Mini-task and conflict model |
| Improving X worsens Y | M2 | Named X/Y pair |
| Direction unclear although the goal is clear | A3 | IFR before solutions |
| Solution is cumbersome or expensive | M7 | Functions to trim; then P only with a selection criterion |
| Tool/architecture trade-off | M3 | One goal↔cost cell |
| System stopped evolving | M4 | One development-law question |
| Interaction between parts is unclear | M5 | One su-field model |
| Defect or recurring failure | M6 | Evidence-backed causal chain |
| Redundant or missing function | M7 | Trim/strengthen list |
| Need the general mini-task template | M1 | One-line task and X/Y pair |

No obvious route: start at **A1** and follow its gate. Do not preload the default ARIZ chain.

## Combine stage entry points
TRIZ is available across the pipeline, not only in Task analysis. Use the active stage's code; do not run these routes as a mandatory checklist.

| Combine stage | Route |
|---|---|
| Dialogue: confirmed goal, conflicting constraints | M1/A1 |
| Task analysis | M2/M4/M5/M6 or A1/A2/A4/A7 |
| Plan | M7/A8; P1/P5/P27 |
| Skeleton | P9/P10/P16/P26 |
| Build-up | M6/A7 and selected P operators |
| Verification | A9/P13/P22/M7 |
| Closing | A10/A11/P23; optional M6 |

## Gate after every step
1. Record the step output in `docs/TASK.md` under Decisions; keep reasoning elsewhere.
2. Close the current reference. Read another only when the previous gate requests it.
3. Return to Combine Plan as soon as a testable direction exists. Two blocked attempts: change route or replan; do not scan the whole pack.
