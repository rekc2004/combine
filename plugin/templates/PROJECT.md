# PROJECT

Keep this root file short and durable. It prevents repeated discovery; it is not a code dump or a task log.

## Purpose and architecture invariants
- <what the project does>
- <structures, APIs and decisions that must not be changed accidentally>

## Durable map
| Area | Entry point / document | What to read first |
|---|---|---|
| <area> | <relative path> | <reason> |

## Programs, models and external resources
| Type | Purpose | Name | Location or command | Why installed / limits | Last verified |
|---|---|---|---|---|---|
| Program | <need> | <name> | <absolute path or PATH command> | <reason and constraints> | <date/check> |
| Model | <kind of work> | <name> | <local path or configured alias; no key> | <why chosen, known weaknesses> | <date/check> |
| Resource | <need> | <name> | <path or non-secret endpoint> | <reason and limitations> | <date/check> |

## Reusable functions and local lessons
| Need | Existing function/helper | Location or graph lookup | Adaptation limits | Verification |
|---|---|---|---|---|
| <need> | <function name> | <relative path; graph `find` when useful> | <inputs/outputs, constraints, what may differ> | <test/check> |

- Before writing a helper, inspect this table and the project graph; reuse/adapt a verified existing function unless the owner explicitly requires an independent implementation.
- Keep project-specific failure lessons here. Generalize a lesson into shared `LESSONS.md` only after verification and sanitization.

## Global registry note
For tools/models shared across projects, use `~/.combine/TOOLS.json` and the deterministic `registry.py find/upsert` instead of duplicating them here. PROJECT.md is for local facts only.

## Project-specific workflows
- <non-obvious build/test/start command and its working directory>
- <owner preferences that remain true across tasks>

## Safety and maintenance
- Never store API keys, tokens, passwords, secrets, personal data, private prompts or source snippets here.
- Record only confirmed locations; mark an unverified entry `NOT VERIFIED` and verify before relying on it.
- Append newly discovered tools; never replace an existing PROJECT.md with the template or truncate it to save space. Correct only the specific stale entry and preserve unrelated content. Do not duplicate TASK.md or long documentation.
