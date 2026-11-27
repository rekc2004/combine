# VERIFIED LESSONS

Shared local memory for Claude and Kimi. Default location: `~/.combine/LESSONS.md`; `COMBINE_HOME` may override `~/.combine`. Keep entries short, generalized and evidence-backed. This file is never distributed in a release.

## Entry format
### <short reusable rule>
- Environment: <OS, shell/tool and relevant version>
- Symptom: <observable failure, without private data>
- Verified cause: <mechanism proved by a test>
- Safe rule: <what to do instead; abstract pattern, not copied source>
- Verification: <command/test that distinguishes fixed from broken>
- Scope: <when the rule applies and when it stops applying>
- Evidence/date: <repeatable check and date>

## Rules
- Main session verifies and writes a lesson; a worker only proposes it in its final handoff.
- Search for an existing rule before appending. Update its evidence instead of adding duplicates.
- Record project-specific details in that project's PROJECT.md, not in shared lessons.
- Never include credentials, private paths/prompts, source snippets, proprietary data or identifying project details.
- A version-specific rule applies only to the recorded environment. Retest it after relevant upgrades; mark failed rules stale instead of generalizing them.
- An unverified hypothesis is not a lesson and is not written here.
