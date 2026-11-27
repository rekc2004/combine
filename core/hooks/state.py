"""SessionStart: выводит статус, TASK, PROJECT, проверенные уроки и реестр инструментов."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import disabled_modules, is_user_level, project_dir, read_stdin_json  # noqa: E402

MAX_CHARS = 8000
PROJECT_MAX_CHARS = 4000
LESSONS_MAX_CHARS = 3000
TOOLS_MAX_CHARS = 3000


def global_rules():
    """Глобальная установка не правит CLAUDE.md проектов: правила подаём сюда, а не через @-импорт.
    Так выключатель (.claude/combine-off) убирает и правила, и хуки."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parts = []
    for name in ("CORE.md", "pipeline.md"):
        try:
            with open(os.path.join(base, name), encoding="utf-8") as f:
                parts.append(f"=== {name} ===\n{f.read().strip()}")
        except OSError:
            pass
    return parts


def last_compaction():
    """Path of the newest saved compaction summary (written by compact.py) or None."""
    d = os.path.join(project_dir(), ".claude", "combine", "compactions")
    try:
        files = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    except OSError:
        return None
    return os.path.join(".claude", "combine", "compactions", files[-1]) if files else None


def combine_home():
    return os.environ.get("COMBINE_HOME") or os.path.join(os.path.expanduser("~"), ".combine")


def lessons_path():
    return os.path.join(combine_home(), "LESSONS.md")


def tools_path():
    return os.path.join(combine_home(), "TOOLS.json")


def registered_tools():
    try:
        with open(tools_path(), encoding="utf-8") as f:
            records = json.load(f).get("tools", [])
    except (OSError, ValueError):
        return ""
    lines = []
    for record in records:
        lines.append(f"{record.get('name', '?')}: {record.get('location', '?')} | "
                     f"{record.get('purpose', '')} | why: {record.get('why', '')} | verified: {record.get('verified', 'NOT VERIFIED')}")
    text = "\n".join(lines)
    if len(text) > TOOLS_MAX_CHARS:
        text = text[:TOOLS_MAX_CHARS] + "\n...[truncated; exact lookup: registry.py find <name>]"
    return text


def main():
    data = read_stdin_json()
    off = disabled_modules()
    if "hook-state" in off:
        return
    if is_user_level():
        lines = ["[Combine] active globally (from ~/.claude/combine). Disable for this project: /combine off. Rules:"]
        lines += global_rules()
    else:
        lines = ["[Combine] active. Rules: .claude/combine/CORE.md, pipeline: .claude/combine/pipeline.md."]
    if off - {"all"}:
        lines.append("Disabled by the user (do not use): " + ", ".join(sorted(off - {"all"})) + ".")
    task = os.path.join(project_dir(), "docs", "TASK.md")
    try:
        with open(task, encoding="utf-8") as f:
            text = f.read()
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n...[truncated, full file: docs/TASK.md]"
        lines.append("Current task state (docs/TASK.md):\n" + text)
    except OSError:
        lines.append("docs/TASK.md missing: task not started or file not created.")
    project = os.path.join(project_dir(), "PROJECT.md")
    try:
        with open(project, encoding="utf-8") as f:
            text = f.read()
        if len(text) > PROJECT_MAX_CHARS:
            text = text[:PROJECT_MAX_CHARS] + "\n...[truncated, full file: PROJECT.md]"
        lines.append("Durable project context (PROJECT.md):\n" + text)
    except OSError:
        lines.append("PROJECT.md missing: create from the supplied template when durable project/tool context is available; never invent paths.")
    try:
        with open(lessons_path(), encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            if len(text) > LESSONS_MAX_CHARS:
                text = text[:LESSONS_MAX_CHARS] + "\n...[truncated, full file: LESSONS.md]"
            lines.append("Verified reusable lessons (apply only to matching environments):\n" + text)
    except OSError:
        pass
    tools = registered_tools()
    if tools:
        lines.append("Registered global tools (exact lookup: registry.py find <name>):\n" + tools)
    if data.get("source") == "compact":
        saved = last_compaction()
        if saved:
            lines.append(f"Last compaction summary saved in {saved} (read on demand, not whole; may be incomplete).")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
