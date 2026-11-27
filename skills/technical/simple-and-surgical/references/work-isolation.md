# Compare and Isolate Work

Load this reference only for competing variants, temporary file copies, parallel writers, or a stage whose raw work would flood the main context.

## Temporary copies for comparison
1. Create a local temporary directory and copy only the files needed for the variants. Record each source path and original hash. Do not copy credentials, unrelated directories, or the whole repository.
2. Apply variants to separate copies and compare them under the same inputs and acceptance checks.
3. Inspect the diff and measurements against the original. A temporary copy is not a security sandbox and does not make an unsafe command safe.
4. After the main session/owner selects a result, apply the minimal intended patch to the real file. Never overwrite the real tree by copying an entire temporary directory back.
5. Run verification on the real deliverable and delete the temporary copies. Preserve a temporary artifact in the project only by explicit decision.

## Separate stage contexts with compact collapse
- Main context owns the goal, hard constraints, architecture decisions, current stage and final acceptance.
- Give each isolated worker a self-contained packet: goal, relevant constraints, exact input paths, allowed scope, relevant PROJECT entries, done-criterion and required checks. Do not pass the whole conversation.
- Dependent stages stay sequential. Isolate independent exploration/review/implementation only when this saves context or enables useful parallelism.
- Worker returns one compact handoff: result, changed files, commands/checks actually run, decisions, and not verified. A verified reusable failure adds a lesson candidate: environment/version, symptom, cause, safe abstract rule, verification and scope. Main session verifies/sanitizes it before writing PROJECT.md or shared LESSONS.md. Raw searches, logs and intermediate reasoning remain in the worker context.
- Main session verifies the claimed result as required, records only the decision/outcome in TASK.md, then closes the stage. Do not paste the raw worker transcript back into the main context.

## Full-tree alternatives
For parallel writers or independently merged implementations, use separate Git worktrees (or Kimi Tower when explicitly enabled), not temporary file copies. A session fork isolates conversation only. Worktrees and copies isolate content, not permissions or security.
