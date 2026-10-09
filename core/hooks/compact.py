"""PostCompact: saves the compaction summary to a file on disk (not into context).
Files go to .claude/combine/compactions/ with a .gitignore ('*'), so they never reach commits:
the summary may contain personal data. Keeps the last KEEP files."""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import disabled_modules, project_dir, read_stdin_json  # noqa: E402

KEEP = 10


def main():
    data = read_stdin_json()
    if "hook-compact" in disabled_modules():
        return
    summary = str(data.get("compact_summary", "")).strip()
    if not summary:
        return
    trigger = re.sub(r"[^a-z]", "", str(data.get("trigger", "unknown")).lower()) or "unknown"
    folder = os.path.join(project_dir(), ".claude", "combine", "compactions")
    os.makedirs(folder, exist_ok=True)
    ignore = os.path.join(folder, ".gitignore")
    if not os.path.exists(ignore):
        with open(ignore, "w", encoding="utf-8", newline="\n") as f:
            f.write("*\n")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = os.path.join(folder, f"{stamp}-{trigger}.md")
    session = re.sub(r"[^A-Za-z0-9_-]", "", str(data.get("session_id", "")))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# Compaction summary ({trigger}, {stamp}, session {session or 'unknown'})\n\n{summary}\n")
    files = sorted(n for n in os.listdir(folder) if n.endswith(".md"))
    for old in files[:-KEEP]:
        try:
            os.remove(os.path.join(folder, old))
        except OSError:
            pass


if __name__ == "__main__":
    main()
