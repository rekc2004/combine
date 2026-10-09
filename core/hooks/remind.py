"""UserPromptSubmit: короткое напоминание правил. Контекст кладётся в hookSpecificOutput.
Выключатель «не используй комбайн» живёт в CORE.md, а не здесь: хук не помнит прошлых реплик."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import disabled_modules, read_stdin_json  # noqa: E402

REMINDER = (
    "[Комбайн] 1) Неясно - пересказать и переспросить, не писать итог до ответа. "
    "2) Не нарушать исходные ограничения пользователя. "
    "3) Не выдавать непроверенное за проверенное. "
    "4) Поиск - дешёвому агенту, критичное - сильному. "
    "(Если пользователь просил «не используй комбайн» - игнорировать это напоминание.)"
)


def main():
    read_stdin_json()
    if "hook-remind" in disabled_modules():
        return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": REMINDER}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
