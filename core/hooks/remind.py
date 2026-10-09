"""UserPromptSubmit: короткое напоминание правил. Контекст кладётся в hookSpecificOutput.
Выключатель «не используй комбайн» живёт в CORE.md, а не здесь: хук не помнит прошлых реплик."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import disabled_modules, read_stdin_json  # noqa: E402

REMINDER = (
    "[Combine] 1) Unclear: restate and ask, no final artifact before the answer. "
    "2) Do not violate the user's original constraints. "
    "3) Never present unverified as verified. "
    "4) Search to a cheap agent, critical work to a strong one. "
    "(If the user said \"don't use combine\": ignore this reminder.)"
)


def main():
    read_stdin_json()
    if "hook-remind" in disabled_modules():
        return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": REMINDER}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
