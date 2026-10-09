#!/usr/bin/env python3
"""Подключает Комбайн к проекту (повторный запуск = обновление).

    python tools/sync.py --target /путь/к/проекту [--packs technical,review]
                         [--with review.deep] [--without hook-guard,review.quick]
                         [--dry-run] [--check]

Трогает только своё: .claude/combine/*, .claude/agents/combine-*.md, .claude/skills/combine-*,
блок между маркерами в CLAUDE.md, свои записи в .claude/settings.json, .combine.json, .combine.lock.
docs/TASK.md создаётся только если его нет. Чужой файл с тем же именем не перезаписывается.
Только стандартная библиотека.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
CORE, SKILLS = SRC / "core", SRC / "skills"
BEGIN, END = "<!-- combine:begin -->", "<!-- combine:end -->"
HOOK_MARK = ".claude/combine/hooks/"
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
STATE_FILE, LOCK_FILE = ".combine.json", ".combine.lock"
SKILL_SUFFIXES = {".md", ".txt"}  # из наборов копируются только текстовые файлы
DEFAULT_PACKS = ["technical", "review"]
HOOK_MODULES = {"hook-state": "state.py", "hook-remind": "remind.py", "hook-guard": "guard.py"}


def die(msg):
    raise SystemExit(msg)


def sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


def read_utf8(path: Path):
    try:
        return path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        die(f"{path} не в UTF-8. Приведите к UTF-8 вручную, ничего не изменено.")


def load_json(path: Path):
    try:
        return json.loads(read_utf8(path))
    except ValueError as e:
        die(f"{path}: некорректный JSON ({e}). Ничего не изменено.")


# ---------- наборы скиллов ----------

def discover_skills():
    """Читает skills/*/pack.json, проверяет пути и имена. Возвращает {ключ: описание}."""
    found = {}
    if not SKILLS.is_dir():
        return found
    for pack_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        manifest = pack_dir / "pack.json"
        if not manifest.exists():
            continue
        pack = pack_dir.name
        if not NAME_RE.match(pack):
            die(f"Недопустимое имя набора: {pack!r}")
        data = load_json(manifest)
        for name, spec in (data.get("skills") or {}).items():
            if not NAME_RE.match(name):
                die(f"Недопустимое имя скилла: {pack}.{name!r}")
            key, base = f"{pack}.{name}", (pack_dir / name).resolve()
            files = spec.get("files") or ["SKILL.md"]
            if "SKILL.md" not in files:
                die(f"{key}: в files обязателен SKILL.md")
            for f in files:
                fp = Path(f)
                if fp.is_absolute() or ".." in fp.parts or fp.suffix not in SKILL_SUFFIXES:
                    die(f"{key}: недопустимый файл в files: {f!r} (только относительные .md/.txt)")
                full = (base / fp).resolve()
                if base not in full.parents or not full.is_file():
                    die(f"{key}: файл не найден внутри скилла: {f}")
            found[key] = {"pack": pack, "name": name, "files": files, "base": base,
                          "default": bool(spec.get("default", False)), "cost": spec.get("cost"),
                          "spec": spec}
    return found


# ---------- вспомогательное ----------

def hook_cmd(script):
    p = f'{HOOK_MARK}{script}'
    return ("sh -c 'p=\"$CLAUDE_PROJECT_DIR/" + p + "\"; "
            "if command -v python3 >/dev/null 2>&1; then exec python3 \"$p\"; else exec python \"$p\"; fi'")


def source_version():
    def git(*a):
        try:
            r = subprocess.run(["git", "-C", str(SRC), *a], capture_output=True, text=True, timeout=10)
            return r.stdout.strip() if r.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            return ""
    return {"commit": git("rev-parse", "HEAD") or "unknown",
            "describe": git("describe", "--tags", "--always") or "unknown",
            "dirty": bool(git("status", "--porcelain"))}


def agent_file(name, spec, models, core_on):
    if not NAME_RE.match(name):
        die(f"Недопустимое имя агента: {name!r}")
    model = models[spec["model"]]["id"]
    rules = "Следуй .claude/combine/CORE.md. " if core_on else ""
    body = (f"Ты агент комбайна `combine-{name}`. {rules}Работай в рамках роли: {spec['description']}\n"
            "Если задача выходит за рамки роли, остановись и верни главной сессии короткое объяснение, "
            "какой агент нужен. Не выдавай непроверенное за проверенное.\n")
    return ("---\n"
            f"name: combine-{name}\n"
            f"description: {json.dumps(spec['description'], ensure_ascii=False)}\n"
            f"tools: {spec['tools']}\n"
            f"model: {model}\n"
            f"effort: {spec['effort']}\n"
            "---\n\n" + body)


def claude_block(enabled, has_skills):
    keep = []
    for line in (CORE / "templates" / "CLAUDE.block.md").read_text(encoding="utf-8").splitlines():
        if "CORE.md" in line and "core" not in enabled:
            continue
        if "pipeline.md" in line and "pipeline" not in enabled:
            continue
        if ("TASK.md" in line or "Состояние задачи" in line) and "pipeline" not in enabled:
            continue
        if "combine-scout" in line and "agents" not in enabled:
            continue
        if "combine-*" in line and not has_skills:
            continue
        keep.append(line)
    return "\n".join(keep).strip()


class Target:
    def __init__(self, root, dry):
        self.root, self.dry, self.log = root, dry, []

    def path(self, rel):
        p = (self.root / rel).resolve()
        if p != self.root and self.root not in p.parents:
            die(f"Отказ: путь вне целевого проекта: {p}")
        return p

    def read(self, rel):
        p = self.path(rel)
        return read_utf8(p) if p.exists() else None

    def write(self, rel, text):
        p = self.path(rel)
        data = text.encode("utf-8")
        if p.exists() and p.read_bytes() == data:
            return False
        self.log.append(f"+ {rel}")
        if not self.dry:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        return True

    def remove(self, rel):
        p = self.path(rel)
        if p.is_file():
            self.log.append(f"- {rel}")
            if not self.dry:
                p.unlink()
                for parent in p.parents:  # убрать опустевшие каталоги комбайна
                    if parent == self.root or "combine" not in parent.name and parent.name != "skills":
                        break
                    try:
                        parent.rmdir()
                    except OSError:
                        break


def merge_claude_md(t, enabled, has_skills):
    raw = t.path("CLAUDE.md").read_bytes().decode("utf-8") if t.path("CLAUDE.md").exists() else ""
    nl = "\r\n" if "\r\n" in raw else "\n"
    old = raw.replace("\r\n", "\n")
    old = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", old, flags=re.S)
    if enabled & {"core", "pipeline", "agents"}:
        new = old.rstrip() + ("\n\n" if old.strip() else "") + f"{BEGIN}\n{claude_block(enabled, has_skills)}\n{END}\n"
    else:
        new = old.rstrip() + "\n" if old.strip() else ""
    if new or raw:
        t.write("CLAUDE.md", new.replace("\n", nl) if nl == "\r\n" else new)


def merge_settings(t, enabled):
    raw = t.read(".claude/settings.json")
    try:
        data = json.loads(raw) if raw is not None else {}
    except ValueError:
        die(".claude/settings.json не является корректным JSON, правьте вручную. Ничего не изменено.")
    if not isinstance(data, dict):
        die(".claude/settings.json: ожидался объект. Ничего не изменено.")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        die(".claude/settings.json: поле hooks должно быть объектом. Ничего не изменено.")
    for event in list(hooks):  # убрать прежние записи комбайна, чужие хуки в тех же группах остаются
        if not isinstance(hooks[event], list):
            die(f".claude/settings.json: hooks.{event} должно быть списком. Ничего не изменено.")
        groups = []
        for g in hooks[event]:
            inner = [h for h in g.get("hooks", []) if HOOK_MARK not in str(h.get("command", ""))]
            if inner or not g.get("hooks"):
                groups.append({**g, "hooks": inner} if g.get("hooks") else g)
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]
    wanted = [("hook-state", "SessionStart", "startup|resume|compact|clear", "state.py"),
              ("hook-remind", "UserPromptSubmit", None, "remind.py"),
              ("hook-guard", "PreToolUse", "Bash|PowerShell", "guard.py")]
    for module, event, matcher, script in wanted:
        if module in enabled:
            group = {"hooks": [{"type": "command", "command": hook_cmd(script)}]}
            if matcher:
                group["matcher"] = matcher
            hooks.setdefault(event, []).append(group)
    if not hooks:
        del data["hooks"]
    if data or raw is not None:
        t.write(".claude/settings.json", json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def do_check(t):
    lock = t.path(LOCK_FILE)
    if not lock.exists():
        die("Нет .combine.lock: комбайн сюда не подключён.")
    bad = 0
    for rel, digest in load_json(lock).get("files", {}).items():
        p = t.path(rel)
        if not p.is_file():
            print(f"ОТСУТСТВУЕТ  {rel}"); bad += 1
        elif sha(p.read_bytes()) != digest:
            print(f"ИЗМЕНЁН      {rel}"); bad += 1
    print("Расхождений нет." if not bad else f"Расхождений: {bad}. Запустите sync, чтобы восстановить, или проверьте изменения.")
    return 1 if bad else 0


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Подключить/обновить Комбайн в проекте")
    ap.add_argument("--target", default=".", help="корень проекта")
    ap.add_argument("--packs", default=None, help=f"наборы скиллов через запятую (по умолчанию {','.join(DEFAULT_PACKS)})")
    ap.add_argument("--with", dest="with_", default=None, help="ключи скиллов, включить поверх default (например review.deep)")
    ap.add_argument("--without", default=None, help="модули или ключи скиллов, которые не ставить")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="сверить файлы проекта с .combine.lock и выйти")
    args = ap.parse_args()

    root = Path(args.target).resolve()
    if not root.is_dir():
        die(f"Нет такой папки: {root}")
    if root == SRC:
        die("Целевой проект не должен быть самим репозиторием комбайна.")
    t = Target(root, args.dry_run)
    if args.check:
        return do_check(t)

    mods = load_json(CORE / "modules.json")["modules"]
    models = load_json(CORE / "models.json")
    skills = discover_skills()

    prev_state = load_json(t.path(STATE_FILE)) if t.path(STATE_FILE).exists() else {}
    csv = lambda s: [x.strip() for x in s.split(",") if x.strip()]
    packs = csv(args.packs) if args.packs is not None else prev_state.get("packs", DEFAULT_PACKS)
    with_ = csv(args.with_) if args.with_ is not None else prev_state.get("with", [])
    disabled = csv(args.without) if args.without is not None else prev_state.get("disabled", [])

    all_packs = {d.name for d in SKILLS.iterdir() if d.is_dir()} if SKILLS.is_dir() else set()
    bad = [p for p in packs if p not in all_packs]
    if bad:
        die(f"Неизвестные наборы: {', '.join(bad)}. Есть: {', '.join(sorted(all_packs)) or 'нет'}")
    bad = [k for k in with_ if k not in skills and k not in mods]
    if bad:
        die(f"Неизвестные скиллы/модули в --with: {', '.join(bad)}")
    bad = [k for k in disabled if k not in mods and k not in skills]
    if bad:
        die(f"Неизвестные модули/скиллы в --without: {', '.join(bad)}")

    enabled = {m for m, v in mods.items() if v["default"]} - set(disabled)
    enabled |= {m for m in with_ if m in mods}

    # желаемое состояние отслеживаемых файлов: путь -> текст
    want = {}
    cm = ".claude/combine/"
    if "core" in enabled:
        want[cm + "CORE.md"] = read_utf8(CORE / "CORE.md")
    if "pipeline" in enabled:
        want[cm + "pipeline.md"] = read_utf8(CORE / "pipeline.md")
    if "agents" in enabled:
        for name, spec in models["agents"].items():
            want[f".claude/agents/combine-{name}.md"] = agent_file(name, spec, models["models"], "core" in enabled)
    for module, script in HOOK_MODULES.items():
        if module in enabled:
            want[f"{cm}hooks/{script}"] = read_utf8(CORE / "hooks" / script)
    if any(m in enabled for m in HOOK_MODULES):
        want[f"{cm}hooks/_common.py"] = read_utf8(CORE / "hooks" / "_common.py")
    chosen = []
    for key, s in skills.items():
        if s["pack"] in packs and key not in disabled and (s["default"] or key in with_):
            chosen.append(key)
            for f in s["files"]:
                want[f".claude/skills/combine-{s['pack']}-{s['name']}/{f}"] = read_utf8(s["base"] / f)

    prev_lock = load_json(t.path(LOCK_FILE)).get("files", {}) if t.path(LOCK_FILE).exists() else {}
    conflicts = [rel for rel, text in want.items()
                 if t.path(rel).exists() and rel not in prev_lock and t.path(rel).read_bytes() != text.encode("utf-8")]
    if conflicts:
        die("Отказ: эти файлы уже есть в проекте и не принадлежат комбайну, ничего не изменено:\n  " + "\n  ".join(conflicts))

    for rel, text in want.items():
        t.write(rel, text)
    for rel in prev_lock:
        if rel not in want:
            t.remove(rel)
    if "pipeline" in enabled and not t.path("docs/TASK.md").exists():
        t.write("docs/TASK.md", read_utf8(CORE / "templates" / "TASK.md"))
    merge_settings(t, enabled)
    merge_claude_md(t, enabled, bool(chosen))
    t.write(STATE_FILE, json.dumps({"version": source_version(), "packs": packs, "with": with_,
                                    "disabled": sorted(disabled)}, indent=2, ensure_ascii=False) + "\n")
    lock = {"files": {rel: sha(text.encode("utf-8")) for rel, text in sorted(want.items())}}
    t.write(LOCK_FILE, json.dumps(lock, indent=2, ensure_ascii=False) + "\n")

    v = source_version()
    print(("[dry-run] " if args.dry_run else "") + f"Комбайн {v['describe']}{' (есть незакоммиченные правки!)' if v['dirty'] else ''} -> {root}")
    print("Модули:", ", ".join(sorted(enabled)) or "нет")
    print("Скиллы:", ", ".join(chosen) or "нет", "| наборы:", ", ".join(packs) or "нет")
    print("Отключено:", ", ".join(sorted(disabled)) or "ничего")
    print("\n".join(t.log) or "Изменений нет.")
    for pack in packs:  # напоминание о внешних скиллах: не ставим и не проверяем, только подсказываем
        manifest = SKILLS / pack / "pack.json"
        rec = load_json(manifest).get("recommends", []) if manifest.exists() else []
        if rec:
            print(f"\nНабор {pack}: рекомендуются внешние скиллы (комбайн их не ставит и не копирует; в облаке их может не быть):")
            for r in rec:
                print(f"  - {r['name']}: {r['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
