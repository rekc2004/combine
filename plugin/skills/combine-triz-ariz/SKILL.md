---
name: combine-triz-ariz
description: "[medium] Staged ARIZ-85V for AI tasks: load one stage, pass its gate, then continue or return to Combine."
---

# Staged ARIZ for AI Tasks

Canonical source: ARIZ-85V, Altshuller, 1985. This is a staged adaptation, not a claim that every physical operation applies to software.

Read only the row requested by the navigator or the previous gate. **Never read all references at once.**

| Codes | Stage | Reference |
|---|---|---|
| A1–A2 | Frame the task, operational zone and time | `references/01-frame.md` |
| A3–A4 | Formulate IFR and physical contradiction | `references/02-ideal.md` |
| A5–A7 | Mobilize resources, knowledge and separations | `references/03-solve.md` |
| A8–A9 | Reframe if blocked; otherwise check the answer | `references/04-reframe-check.md` |
| A10–A11 | Apply and analyze a verified answer | `references/05-apply-learn.md` |

Short route: A1–A2 → A3–A4 → a concrete move → A9. Load A5–A7 only when a move does not emerge. A8 is for a blocked or failed route, not the normal verification step. A10–A11 are optional for a disposable local fix and expected for a reusable project decision.

At every gate, write one compact result to TASK.md and return to the Combine stage that owns the work. Do not turn all ARIZ codes into mandatory project stages.
