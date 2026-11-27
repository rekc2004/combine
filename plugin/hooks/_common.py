"""Общие функции хуков Комбайна. Только стандартная библиотека."""
import json
import os
import sys

ALL_HOOKS = {"hook-state", "hook-remind", "hook-guard", "hook-compact", "graph"}


def project_dir(data=None):
    """Корень проекта из cwd пейлоада Kimi: хуки плагина запускаются с cwd = корень плагина."""
    if data:
        cwd = data.get("cwd")
        if isinstance(cwd, str) and cwd:
            return cwd
    return os.getcwd()


def is_user_level():
    """Хук запущен из глобальной установки (~/.claude/combine), а не из копии внутри проекта."""
    here = os.path.realpath(__file__)
    root = os.path.realpath(project_dir())
    return not (here == root or here.startswith(root + os.sep))


def disabled_modules(data=None):
    """Отключённые модули/ключи: из .combine.json проекта и из COMBINE_DISABLE.
    COMBINE_DISABLE=all выключает все хуки. Файл .claude/combine-off в проекте выключает
    Комбайн целиком (/combine off). Глобальные хуки молчат, если в проекте своя копия
    (.combine.lock): её хуки уже работают, дублировать не нужно."""
    off = set()
    root = project_dir(data)
    if os.path.exists(os.path.join(root, ".claude", "combine-off")):
        return set(ALL_HOOKS) | {"all"}
    if False:  # Kimi: проектных копий нет, плагин единственный носитель
        return set(ALL_HOOKS) | {"all"}
    try:
        with open(os.path.join(root, ".combine.json"), encoding="utf-8") as f:
            off.update(json.load(f).get("disabled", []))
    except (OSError, ValueError):
        pass
    off.update(x.strip() for x in os.environ.get("COMBINE_DISABLE", "").split(",") if x.strip())
    if "all" in off:
        off |= ALL_HOOKS
    return off


def force_utf8():
    """На Windows stdout по умолчанию в системной кодировке, а host хуков читает UTF-8."""
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
