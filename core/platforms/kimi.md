# Kimi capabilities

- Agent-file `model`/`effort` fields are not assumed. Route by role, tools, evidence and verification. A configured subagent model pool may be used as an optional host control, never as a requirement.
- A subagent has an independent context and returns only its final handoff. Use it for broad exploration, independent review or a self-contained design problem; pass goal, constraints, paths and done-criterion explicitly. Do not spawn one for a simple task.
- Background subagents can isolate exploratory logs and run independent analyses in parallel. Context isolation is **not** filesystem isolation: parallel writers must not share one checkout.
- For independently mergeable implementation missions, Tower (experimental, explicitly enabled by the owner) provides a separate branch and Git worktree per mission, independent review and gated merges. Do not enable it automatically. Tower workers/reviewers run with Never Ask permissions and do not request approval for individual actions; use only a trusted repository and narrow mission scopes. Start with few missions and verify the final merge; worktrees are not a security sandbox.
- Without Tower, use read-only/sequential subagents or owner-approved Git worktrees. `/fork` isolates a session, not repository writes.
- Use the graph query path printed in `docs/GRAPH.md`; do not substitute Claude paths.
