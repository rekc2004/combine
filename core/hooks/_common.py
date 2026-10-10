"""Общие функции хуков Комбайна. Только стандартная библиотека."""
import json
import os
import sys

ALL_HOOKS = {"hook-state", "hook-remind", "hook-guard", "hook-compact"}


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def is_user_level():
    """Хук запущен из глобальной установки (~/.claude/combine), а не из копии внутри проекта."""
    here = os.path.realpath(__file__)
    root = os.path.realpath(project_dir())
    return not (here == root or here.startswith(root + os.sep))


def disabled_modules():
    """Отключённые модули/ключи: из .combine.json проекта и из COMBINE_DISABLE.
    COMBINE_DISABLE=all выключает все хуки. Файл .claude/combine-off в проекте выключает
    Комбайн целиком (/combine off). Глобальные хуки молчат, если в проекте своя копия
    (.combine.lock): её хуки уже работают, дублировать не нужно."""
    off = set()
    if os.path.exists(os.path.join(project_dir(), ".claude", "combine-off")):
        return set(ALL_HOOKS) | {"all"}
    if is_user_level() and os.path.exists(os.path.join(project_dir(), ".combine.lock")):
        return set(ALL_HOOKS) | {"all"}
    try:
        with open(os.path.join(project_dir(), ".combine.json"), encoding="utf-8") as f:
            off.update(json.load(f).get("disabled", []))
    except (OSError, ValueError):
        pass
    off.update(x.strip() for x in os.environ.get("COMBINE_DISABLE", "").split(",") if x.strip())
    if "all" in off:
        off |= ALL_HOOKS
    return off


def force_utf8():
    """На Windows stdout по умолчанию в системной кодировке, а Claude Code читает UTF-8."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def read_stdin_json():
    force_utf8()
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        return json.loads(raw or "{}")
    except (ValueError, OSError):
        return {}
