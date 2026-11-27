# Combine pipeline
Task state lives in `docs/TASK.md`, not in chat context. New session/compaction loads it automatically (hook `hook-state`). Its purpose is to prevent repeated discovery and re-reading, not to add paperwork.

## Stages
1. **Dialogue.** Clarify task (CORE rule 1). Result: goal and hard constraints in TASK.md. No code and no TRIZ detour while the task itself is unclear.
2. **Task analysis.** Inspect available evidence; record the problem, unknowns, and done-criteria. Clear routine work goes straight to Plan. For a contradiction, deadlock, or contested trade-off, invoke `combine-triz-navigator` once **when installed and not disabled**: follow one route and one gate at a time, then record only the decision in TASK.md. If TRIZ is off or unavailable, main session/architect performs ordinary evidence and trade-off analysis without loading TRIZ. Do not preload TRIZ references or make every task an ARIZ task.
3. **Plan.** `combine-architect` (or main session if small) uses the analysis to split work into stages. Per stage: goal, done-criterion, and owner. Strike unnecessary stages, including empty TRIZ steps; mark done. A correct first architecture and reusable decision records take priority over model tuning.
4. **Skeleton.** `combine-skeleton`: structure, stubs, configs, build. **Acceptance:** builds, basic tests pass, structure matches plan. Main session accepts the skeleton itself by running build and tests. No further until accepted.
5. **Build-up.** `combine-builder` implements on the skeleton by stage. For critical parts, `combine-architect` owns design, threat decisions and acceptance; builder implements the approved design. Load a TRIZ reference only for the active stage's unresolved contradiction. A self-contained stage may run in an isolated subagent context when its searches/logs would flood the main chat; it returns only a compact verified handoff. Dependent stages remain sequential.
6. **Verification.** Tests, build. `combine-security` for anything security-related. If TRIZ was used, apply A9 to the chosen answer without rereading earlier references. Result: report of what was checked and what was NOT.
7. **Closing.** Collapse each isolated stage to its result, changed files, checks and limits; keep raw logs in the worker context. Update TASK.md: done, remaining, known limits. A verified fix may be delivered without causal analysis; for an unclear/recurring root cause, offer M6 as a separate optional stage. For a reusable verified answer, optionally apply A10–A11; do not create a separate TRIZ report by default.

## TRIZ route by Combine stage
TRIZ is not confined to Task analysis. When the module is enabled, use only the active stage's relevant code and one on-demand reference; skip this table for routine work.

| Combine stage | Optional TRIZ entry points |
|---|---|
| Dialogue | M1/A1 for conflicting constraints after the goal is confirmed |
| Task analysis | M2/M4/M5/M6 and A1/A2/A4/A7 by symptom |
| Plan | M7 trimming, A8 reframing, P1/P5 split↔merge, P27 disposable experiment |
| Skeleton | P9/P10 preparation, P16 partial solution, P26 mock/copy |
| Build-up | M6 for evidence-backed causes; A7 separation and selected P operators |
| Verification | A9 plus P13/P22 counter-harm and M7 harm/ideality checks |
| Closing | A10/A11 transfer and learning, P23 feedback; optional M6 for recurring defects |

## Durable project context
`PROJECT.md` in the project root holds only confirmed architecture invariants, durable document map, program/model/resource locations and why they are used. The state hook reads a bounded excerpt. Create it from the supplied template when such facts exist; append new tools and correct only their own stale entries. Never overwrite an existing file with the template, truncate it, invent paths, or store code, secrets, credentials or private prompts. Project contents stay local and never enter releases; only the empty template is distributed. Workers receive only the relevant PROJECT entries in their task packet.

## Global tool registry
`~/.combine/TOOLS.json` is the shared Claude/Kimi index of programs, models and external resources. Before searching projects for a tool, run the installed `tools/registry.py find <name-or-alias>`; add `--project <root>` to search local PROJECT.md in the same call. State loads only a bounded summary. Register a newly verified tool with `tools/registry.py upsert <name> --location <path> --purpose <use> --why <reason> [--aliases a,b]`: upsert preserves every other entry and writes atomically. Keep exact locations, purpose, limits and last verification. No secrets, keys, private prompts or unverified guesses; the real registry never enters releases, only an empty template is distributed.

## Verified learning and reuse
- Before writing a helper, inspect PROJECT.md and the project graph; reuse or adapt a verified existing function unless the owner explicitly requires an independent implementation. Record its path, limits and verification instead of copying source into PROJECT.
- A worker that hits a reusable failure adds a compact lesson candidate to its handoff: environment/version, symptom, verified cause, safe abstract rule, verification and scope. Raw commands may contain secrets and are not copied blindly.
- Main session verifies the lesson before writing it. Project-specific lessons go to PROJECT.md; sanitized cross-project lessons go to `~/.combine/LESSONS.md` (`COMBINE_HOME` overrides the base). Search first and update evidence rather than duplicating rules.
- Shared lessons never contain private paths, prompts, source snippets, credentials or identifying project data and never enter releases. Apply a version-specific lesson only to a matching environment and retest after upgrades.

## Routing work
- One known file or a simple lookup: main session. Broad/multi-file search, reading and fact gathering: `scout`; do not spawn an agent for a trivial lookup.
- Code search starts from `docs/GRAPH.md` when available. Use the query path printed in its header for exact callers/deps; read only files the graph implicates. The graph is approximate: TS/JS/C calls are matched by name.
- New logic with clear spec: `builder`.
- Uncertainty, protocol design, threat model, contested trade-offs: `architect`.
- Security: `security`, plus independent recheck of critical parts.
- After two failed attempts, narrow the task, add evidence or change the route; do not repeat the same call. Use host model/effort controls only when actually supported.
- Keep dependent steps in one context. Split only independent work; every worker receives goal, constraints, exact paths and done-criterion.
- Do not spend a strong/expensive resource on routine search or formatting. Tell every worker explicitly what to verify and how to report.
- Expensive skills (`[expensive]` in description) only on user request.
- Batch local work may use `combine-technical-inkling` only when its configured worker exists. It is a one-shot script, not a subagent; verify its output in the main session.

## docs/TASK.md format
Use `templates/TASK.md` supplied in the installed Combine/plugin. One line per stage: checkbox, owner, done-criterion and short result. Optional host controls may be added where supported. No elaboration: details go to commits and project docs.
