# Combine pipeline
Task state lives in `docs/TASK.md`, not in chat context. New session/compaction loads it automatically (hook `hook-state`).

## Stages
1. **Dialogue.** Clarify task (CORE rule 1). Result: goal and hard constraints in TASK.md. No code.
2. **Plan.** `combine-architect` (or main session if small) splits work into stages. Per stage: goal, done-criterion, model and effort with justification from `core/models.json`. Strike unnecessary, mark done.
3. **Skeleton.** `combine-skeleton`: structure, stubs, configs, build. **Acceptance:** builds, basic tests pass, structure matches plan. Cheap models may report unchecked, so main session accepts: runs build and tests itself. No further until accepted.
4. **Build-up.** `combine-builder` implements on the skeleton by stage. Critical parts (network, crypto, untrusted input parsing): `combine-architect` leads the stage, not builder.
5. **Verification.** Tests, build. `combine-security` for anything security-related. Result: report of what was checked and what was NOT.
6. **Closing.** Update TASK.md: done, remaining, known limits.

## Choosing a model
Orchestrator decides by class of work, not a stage->model table:
- Search, reading, running commands, formatting: `scout` (cheap, low effort), always.
- New logic with clear spec: `builder`.
- Uncertainty, protocol design, threat model, contested trade-offs: `architect`.
- Security: `security`, plus recheck of critical parts by the strongest model.
- Raise effort first, then model (Anthropic: often the best lever). Cheap model failed a stage twice: raise effort or model, no third retry.
- Strong model doing routine work: stop, hand to `scout`/`builder`.
- A chain of dependent steps: one model, cheaper and more reliable. Split between agents only independent parts.
- Tell cheap agents explicitly what to check and how to report: they do not ask for help or verification.
- Expensive skills (`[expensive]` in description) only on user request.

## docs/TASK.md format
See `core/templates/TASK.md`. One line per stage: checkbox, model/effort, short result. No elaboration: details go to commits and project docs.
