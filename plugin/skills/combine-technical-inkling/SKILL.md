---
name: combine-technical-inkling
description: "[cheap] Local free model Inkling 2 Mini: batch read/summarize/draft via script, offline, private code stays on machine."
---

# Local worker: Inkling 2 Mini

One-shot calls to a local model (llama.cpp on this machine, port 11550). Free, works offline, code never leaves the machine. Profile and limits: `core/agents.json` -> `models.inkling`.

Before calling, check that `F:/models/inkling-2-mini/ask.py` exists. If this owner-specific worker is unavailable, say so and use the normal main/scout route; do not install or invent a replacement.

## Use for
- Digesting many files at once ("for each file output: path + 2-line summary").
- Drafts: skeleton stubs, commit messages, release notes.
- Log triage, bulk classification, extracting facts from tool output.

## Not for
- Architecture, protocols, threat model, security review: `architect`/`security`.
- Final code accepted without a run.
- Multi-constraint instructions or long dialog: it is one-shot and weak there.

## Call
```
python F:/models/inkling-2-mini/ask.py "PROMPT" [--file PATH ...] [--system TEXT] [--max-tokens N]
```
- Prompt must be self-contained: the model sees only what you send. No repo, no chat history, no tools.
- Attach files with `--file` (repeatable), do not paste big text.
- A one-shot call starts the server if needed (~1 min) and stops it after the call. An already running server is left running. Use `--keep-server` or start it manually for repeated batch calls; stop manually with `stop-inkling.ps1`.
- Batch items into one call; a call is independent of other calls.
- Default output is final content only. `--include-reasoning` is a diagnostic option, not a worker response format.
- For agent handoffs, use `--system` to require: result, evidence, changed files, checks actually run, not verified, and an optional sanitized lesson candidate. Prose compliance is not proof; main session verifies it.

## Verify
Treat output like any cheap model: facts need a source, code needs a run, and Skeleton acceptance stays with the main session.
