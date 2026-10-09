---
name: combine-technical-verify-done
description: "[cheap] Before saying code is done: build, run tests, show the actual result."
---

# Verify before "done"

Use when about to report that code is written, fixed or refactored.

1. Run the project's build and tests (commands from README/Makefile/package.json). Commands unknown: find them, do not assume.
2. Show in the answer the actual output or its gist: what ran, what passed, what failed.
3. Nothing to run, or it failed to run: say "not verified because ...". Never replace a check with "should work".
4. A test failed: do not declare the task done. Fix it or state the failure plainly.
5. Record in docs/TASK.md what was verified and what was not.

Why: cheap models on low effort sometimes report a change without checking, so the check is an explicit rule.
