---
name: combine-technical-simple-and-surgical
description: "[cheap] Write minimal code for the task, change only what is needed, set verifiable success criteria first."
---

# Simple, surgical, verified

Use when writing, editing or refactoring code. Ideas are common to many analyses of typical LLM coding mistakes (including observations by Andrej Karpathy); the text is written anew.

## 1. Simplicity
- Minimum code that solves the task. Nothing in reserve: no unrequested functions, no abstractions for one-off code, no "future" settings, no handling of impossible cases.
- Wrote 200 lines where 50 would do: rewrite.
- Ask yourself: would a senior engineer call this overbuilt? If yes, simplify.

## 2. Surgical changes
- Editing someone else's code: do not "improve" neighbours, reformat, or refactor what is not broken; keep the existing style even if you would do it differently.
- Notice unrelated dead code: mention it, do not delete it.
- Anything orphaned by YOUR edits (imports, variables, functions): remove it.
- Test: every changed line traces to the user's request.

## 3. Goal with a check
Turn the task into a verifiable criterion and repeat until it holds:
- "Add validation" -> tests for bad inputs, then make them pass.
- "Fix the bug" -> a test reproducing it, then make it pass.
- "Refactor" -> tests pass before and after.
For a multi-step task, write briefly: step -> how I will verify. A weak criterion ("make it work") forces questions back; a strong one lets you finish alone.

## 4. Assumptions
State a non-obvious assumption aloud. Several readings possible: do not pick silently, list them and ask (CORE rule).
