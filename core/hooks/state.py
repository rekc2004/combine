"""SessionStart: выводит статус комбайна и docs/TASK.md (его stdout попадает в контекст)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import disabled_modules, is_user_level, project_dir, read_stdin_json  # noqa: E402

MAX_CHARS = 8000


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
    if data.get("source") == "compact":
        saved = last_compaction()
        if saved:
            lines.append(f"Last compaction summary saved in {saved} (read on demand, not whole; may be incomplete).")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
