---
name: combine-technical-compaction
description: "[cheap] Conductor watches context fill: saves state to files before compaction and reads the saved summary after."
---

# Context compaction (conductor)

Compaction itself you cannot start (no tool). The owner runs `/compact`, or auto-compact fires. Threshold is a user setting (`/autocompact`), not changed here.

1. At stage boundaries and after big reads check fill: tool `get_usage` (`context.percentUsed`, `autoCompactsAtPercent`) if present, or owner's `/context`. Neither: judge by volume read.
2. Within 5 points of the threshold: reach a safe point, update `docs/TASK.md` (done, remaining, decisions, open questions, changed files, check commands), tell the owner in one line that compaction is near and state is saved. Start no big reads or edits.
3. After compaction: read `docs/TASK.md` and, if `hook-compact` is on, the newest summary in `.claude/combine/compactions/` (on demand, not whole; may be incomplete). Continue from the recorded point.
4. Manual `/compact` text should say what to keep: owner decisions, task state, open questions, changed files, check commands.
5. Skip if the owner said "don't use combine". Off switch: key `technical.compaction`.
