# Claude capabilities

- Add model and effort to each stage owner using `core/agents.json` as the source of profiles. These are controls, not the purpose of Combine.
- Raise effort first, then model when a capable worker lacks depth. Keep dependent steps on one model when that is cheaper and more reliable.
- Strong models do architecture and critical review; cheap models do bounded search/skeleton work with explicit verification. Main-session acceptance remains mandatory.
- Subagents work in their own context and return a summary. Use them for self-contained stages whose exploration/implementation would flood the main conversation; keep only their compact final handoff.
- Project/global graph query paths are supplied in `docs/GRAPH.md`; the Claude block may also point to the installed `.claude/combine/graph/query.py`.
