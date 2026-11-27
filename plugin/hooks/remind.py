"""UserPromptSubmit: короткое напоминание правил. stdout добавляется в контекст (Kimi).
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
    data = read_stdin_json()
    if "hook-remind" in disabled_modules(data):
        return
    if "hook-remind" not in {x.strip() for x in os.environ.get("COMBINE_ENABLE", "").split(",") if x.strip()}:
        return  # в Kimi нет state.json: включение только явным COMBINE_ENABLE=hook-remind
    print(REMINDER)


if __name__ == "__main__":
    main()
