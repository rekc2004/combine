## Combine
Project is connected to Combine. Rules: @.claude/combine/CORE.md
Pipeline and model choice: @.claude/combine/pipeline.md
Task state: docs/TASK.md (read at start, update after each stage).
Repo search goes to `combine-scout`, not the strong model. Critical parts (network, crypto, untrusted input) never go to cheap agents.
Combine skills live in .claude/skills/combine-*. Expensive ones are marked [expensive] in the description: call only on direct user request.
If the user says "don't use combine" (any language), ignore pipeline and agents in this chat until "turn combine on".
On context compaction keep: owner decisions, task state (docs/TASK.md), open questions, changed files, check commands.
