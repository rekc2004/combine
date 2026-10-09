---
name: combine-review-quick
description: "[cheap] Quick review of your own changes against a short checklist before commit."
---

# Quick review

Run your diff through this checklist, invent nothing beyond it:

1. Does the code do what was asked, and only that? No extra changes.
2. Is untrusted input (files, network, paths, names) treated as hostile?
3. No secrets, keys or personal data in code or logs?
4. Is there a test or check for the new behavior and for the error case?
5. Is the public interface intact?

Result: list of findings with file and line, or "no findings". For deep security review use agent `combine-security`, not this skill.

Heavy reviewer: add it as a separate skill `review.deep` with `"cost": "expensive"` and `"default": false`; it is then installed only via `--with review.deep`.
