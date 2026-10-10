---
name: combine
description: "Manage Combine: status, turn off or on for this project, connect as a copy into the project, update. Call: /combine [status|off|on|here|update]."
---

# /combine

Combine is installed globally (`~/.claude/combine`) and works in all projects until a project is switched off. The source (Combine folder) is in `~/.claude/combine/state.json`, field `source`. Python: `python3`, else `python`.

The user's argument after `/combine` picks the action; none means `status`. Reply briefly, in the user's language.

## status
1. Run `python <source>/tools/sync.py --user --status` (version, source, packs, file count).
2. Check the project: `.claude/combine-off` exists (switched off); `.combine.lock` exists (project has its own Combine copy: global hooks stay silent, the copy works).
3. Output one short table: version, source, state in this project (global on / off / project copy).

## off
Switch Combine off for this project.
1. Create an empty `.claude/combine-off` in the project root (create `.claude` if missing).
2. If the project is under git, add the line `.claude/combine-off` to `.git/info/exclude` if absent (local switch, stays out of commits).
3. Say: takes effect from the next session (hooks and rules load at start); in this session the rules are already in context, so do not follow them and do not call `combine-*` agents until the user turns it on.

## on
Delete `.claude/combine-off` if present. Say the rules return from the next session.

## here
Connect Combine as a **copy into the project** (needed for cloud and teams: a cloud session does not read `~/.claude`).
1. Never for the Combine repository itself (the installer refuses).
2. Show what changes first: `python <source>/tools/sync.py --target . --dry-run`.
3. After user confirmation run it without `--dry-run`. Warn that changes to `CLAUDE.md`, `.claude/` and `.combine.*` go into commits if the user commits.

## update
Update the whole global install to the latest **released tag**, from any project. Works from your own managed copy `~/.claude/combine/src`, not from a dev folder (the `source` in state.json may be a lab checkout whose branch is unknown).
1. Managed copy: if `~/.claude/combine/src` is missing, `git clone https://github.com/rekc2004/combine ~/.claude/combine/src`; else `git -C ~/.claude/combine/src fetch --tags --force`. Only this repo; never other URLs.
2. Latest tag: highest `vX.Y.Z` from `git -C ~/.claude/combine/src tag -l 'v*' --sort=-v:refname`. Installed: `python <src>/tools/sync.py --user --status`. Equal: say "up to date", stop.
3. Show what changes: `git -C <src> diff --stat <installed tag>..<latest>` and CHANGELOG entries between them (short, owner's language). Warn the update installs hooks that run code on this machine, so the owner should read the diff (`git -C <src> diff <installed>..<latest>`).
4. Ask for confirmation, unless the user said "no questions". Then `git -C <src> checkout <latest>` (detached tag, never a branch), `python <src>/tools/sync.py --user --dry-run`, then without `--dry-run`. Source in state.json becomes the managed copy.
5. Report the new version and `--user --check` result. New hooks and agents load at session start; a running session may not pick them up.
Fails or tag missing: change nothing, report.

## Never
- Touch anything outside `~/.claude/combine`, `~/.claude/agents/combine-*`, `~/.claude/skills/combine*` and Combine's hook entries in `~/.claude/settings.json`; the installer tracks its files itself.
- Enable modules or packs on your own: only on user request (`--with`, `--without`).
- Present unverified as verified: hooks and agents load at session start, whether a running session picks up new ones depends on the Claude Code version. If not checked in this session, say so.
