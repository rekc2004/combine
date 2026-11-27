#!/usr/bin/env python3
"""Собирает плагин Kimi из канонических (Claude-формата) исходников: dist/kimi-plugin/.

    python tools/build_plugin.py           собрать
    python tools/build_plugin.py --check   сверить dist с исходниками, ничего не писать
    python tools/build_plugin.py --without triz   собрать без набора TRIZ (жёсткое off)

Идея слияния: продуктовые хуки (core/hooks/*.py) — канон в формате Claude Code.
Kimi-варианты не хранятся отдельно: они выводятся трансформацией при сборке
(таблица HOOK_TRANSFORMS ниже). Каждый якорь обязан встретиться ровно один раз:
если канон уедет, сборка падает — двойная правка хуков невозможна молча.

Дерево плагина (dist/kimi-plugin/):
  kimi.plugin.json         манифест (корень лаборатории)
  plugin/SYSTEM.md         core/CORE.md + общий pipeline + core/platforms/kimi.md
  plugin/templates/        пустые шаблоны TASK/PROJECT/LESSONS/TOOLS
  plugin/tools/registry.py точный lookup/upsert глобального реестра инструментов
  plugin/agents/*.md       файлы субагентов из core/agents.json (роли; model/effort Kimi игнорирует)
  plugin/skills/*/         скиллы из skills/<набор>/<имя>/ (имена combine-<набор>-<имя>)
  plugin/hooks/*.py        хуки, трансформированные под пейлоады Kimi
  plugin/graph/*.py        построитель и запросы графа (общие пути .claude/combine)

Только стандартная библиотека.
"""
import argparse
import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
OUT = LAB / "dist" / "kimi-plugin"

AGENT_TAIL = (
    "\n\nYou are a sub-agent: no direct user contact, only the main session. "
    "Your final message is the complete, self-contained report for it: result, what verified it, "
    "what is not verified; short, one page max. Never present unverified as verified: "
    "ran it — show the output; did not run — say so. If the task is outside your role, stop and "
    "tell the main session which agent is needed."
)

# (якорь из канонического файла, замена для Kimi). Якорь должен быть уникален.
HOOK_TRANSFORMS = {
    "core/hooks/_common.py": [
        ('def project_dir():\n    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()',
         'def project_dir(data=None):\n'
         '    """Корень проекта из cwd пейлоада Kimi: хуки плагина запускаются с cwd = корень плагина."""\n'
         '    if data:\n'
         '        cwd = data.get("cwd")\n'
         '        if isinstance(cwd, str) and cwd:\n'
         '            return cwd\n'
         '    return os.getcwd()'),
        ('def disabled_modules():', 'def disabled_modules(data=None):'),
        ('    if os.path.exists(os.path.join(project_dir(), ".claude", "combine-off")):',
         '    root = project_dir(data)\n'
         '    if os.path.exists(os.path.join(root, ".claude", "combine-off")):'),
        ('    if is_user_level() and os.path.exists(os.path.join(project_dir(), ".combine.lock")):',
         '    if False:  # Kimi: проектных копий нет, плагин единственный носитель'),
        ('        with open(os.path.join(project_dir(), ".combine.json"), encoding="utf-8") as f:',
         '        with open(os.path.join(root, ".combine.json"), encoding="utf-8") as f:'),
    ],
    "core/hooks/state.py": [
        ('    off = disabled_modules()\n    if "hook-state" in off:',
         '    off = disabled_modules(data)\n    if "hook-state" in off:'),
        ('    if is_user_level():\n'
         '        lines = ["[Combine] active globally (from ~/.claude/combine). Disable for this project: /combine off. Rules:"]\n'
         '        lines += global_rules()\n'
         '    else:\n'
         '        lines = ["[Combine] active. Rules: .claude/combine/CORE.md, pipeline: .claude/combine/pipeline.md."]',
         '    lines = ["[Комбайн] активен (плагин combine). Правила и конвейер — в системном промпте."]'),
        ('    task = os.path.join(project_dir(), "docs", "TASK.md")',
         '    task = os.path.join(project_dir(data), "docs", "TASK.md")'),
        ('    project = os.path.join(project_dir(), "PROJECT.md")',
         '    project = os.path.join(project_dir(data), "PROJECT.md")'),
        ('    if data.get("source") == "compact":\n'
         '        saved = last_compaction()\n'
         '        if saved:\n'
         '            lines.append(f"Last compaction summary saved in {saved} (read on demand, not whole; may be incomplete).")',
         ''),
    ],
    "core/hooks/remind.py": [
        ('"""UserPromptSubmit: короткое напоминание правил. Контекст кладётся в hookSpecificOutput.',
         '"""UserPromptSubmit: короткое напоминание правил. stdout добавляется в контекст (Kimi).'),
        ('    read_stdin_json()\n    if "hook-remind" in disabled_modules():\n        return',
         '    data = read_stdin_json()\n'
         '    if "hook-remind" in disabled_modules(data):\n'
         '        return\n'
         '    if "hook-remind" not in {x.strip() for x in os.environ.get("COMBINE_ENABLE", "").split(",") if x.strip()}:\n'
         '        return  # в Kimi нет state.json: включение только явным COMBINE_ENABLE=hook-remind'),
        ('    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": REMINDER}}, ensure_ascii=False))',
         '    print(REMINDER)'),
    ],
    "core/hooks/guard.py": [
        ('    if "hook-guard" in disabled_modules():',
         '    if "hook-guard" in disabled_modules(data):'),
    ],
    "core/hooks/graph.py": [
        ('    read_stdin_json()\n    off = disabled_modules()',
         '    data = read_stdin_json()\n    off = disabled_modules(data)'),
        ('    root = project_dir()', '    root = project_dir(data)'),
    ],
    "core/hooks/compact.py": [
        ('    if "hook-compact" in disabled_modules():',
         '    if "hook-compact" in disabled_modules(data):'),
        ('    folder = os.path.join(project_dir(), ".claude", "combine", "compactions")',
         '    folder = os.path.join(project_dir(data), ".claude", "combine", "compactions")'),
        ('        f.write(f"# Compaction summary ({trigger}, {stamp}, session {session or \'unknown\'})\\n\\n{summary}\\n")',
         '        f.write(f"# Compaction summary ({trigger}, {stamp}, session {session or \'unknown\'})\\n\\n{summary}\\n")\n'
         '    print(f"Compaction summary saved: {os.path.relpath(path, project_dir(data))} '
         '(read on demand; may be incomplete).")'),
    ],
}


def yq(s):
    return json.dumps(s, ensure_ascii=False)


def agent_md(name, spec):
    tools = [t.strip() for t in spec["tools"].split(",") if t.strip()]
    fm = ["---",
          f"name: combine-{name}",
          f"description: {yq(spec['description'])}",
          f"whenToUse: {yq(spec['whenToUse'])}",
          "tools:",
          *[f"  - {t}" for t in tools],
          "subagents: []",
          "---", ""]
    return "\n".join(fm) + spec["role"].rstrip() + AGENT_TAIL + "\n"


def apply_transforms(rel, text):
    for anchor, repl in HOOK_TRANSFORMS.get(rel, []):
        n = text.count(anchor)
        if n != 1:
            raise SystemExit(f"Сборка прервана: якорь встречается {n} раз (нужен ровно 1) в {rel}:\n{anchor[:120]}...")
        text = text.replace(anchor, repl)
    return text


def build(without=()):
    agents = json.loads((LAB / "core" / "agents.json").read_text(encoding="utf-8"))["agents"]
    out = {}
    out["kimi.plugin.json"] = (LAB / "kimi.plugin.json").read_text(encoding="utf-8")
    system = (LAB / "core" / "CORE.md").read_text(encoding="utf-8").strip() + "\n\n"
    system += (LAB / "core" / "pipeline.md").read_text(encoding="utf-8").strip() + "\n\n"
    system += (LAB / "core" / "platforms" / "kimi.md").read_text(encoding="utf-8").strip() + "\n"
    out["plugin/SYSTEM.md"] = system
    for template in ("TASK.md", "PROJECT.md", "LESSONS.md"):
        out[f"plugin/templates/{template}"] = (LAB / "core" / "templates" / template).read_text(encoding="utf-8")
    out["plugin/templates/TOOLS.json"] = (LAB / "core" / "templates" / "TOOLS.json").read_text(encoding="utf-8")
    out["plugin/tools/registry.py"] = (LAB / "core" / "tools" / "registry.py").read_text(encoding="utf-8")
    for name, spec in agents.items():
        out[f"plugin/agents/combine-{name}.md"] = agent_md(name, spec)
    sys.path.insert(0, str(LAB / "tools"))
    import sync  # noqa: E402
    skills = sync.discover_skills()
    unknown = set(without) - {s["pack"] for s in skills.values()}
    if unknown:
        raise SystemExit("Неизвестные наборы в --without: " + ", ".join(sorted(unknown)))
    for key, s in sorted(skills.items()):
        if s["pack"] in without:
            continue
        for f in s["files"]:
            out[f"plugin/skills/combine-{s['pack']}-{s['name']}/{f}"] = (s["base"] / f).read_text(encoding="utf-8")
    for script in ("_common.py", "state.py", "guard.py", "remind.py", "compact.py", "graph.py"):
        rel = f"core/hooks/{script}"
        out[f"plugin/hooks/{script}"] = apply_transforms(rel, (LAB / rel).read_text(encoding="utf-8"))
    for script in ("build.py", "query.py"):
        rel = f"core/graph/{script}"
        out[f"plugin/graph/{script}"] = (LAB / rel).read_text(encoding="utf-8")
    return out


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="Собрать Kimi plugin")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--without", default="", help="наборы скиллов через запятую, например triz")
    args = parser.parse_args()
    check = args.check
    want = build({x.strip() for x in args.without.split(",") if x.strip()})
    if check:
        bad = []
        for rel, text in sorted(want.items()):
            p = OUT / rel
            if not p.is_file():
                bad.append(f"ОТСУТСТВУЕТ  {rel}")
            elif p.read_text(encoding="utf-8") != text:
                bad.append(f"УСТАРЕЛ      {rel}")
        on_disk = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()} if OUT.is_dir() else set()
        bad += ["ЛИШНИЙ      " + rel for rel in sorted(on_disk - set(want))]
        if bad:
            print("dist/kimi-plugin не совпадает с исходниками:\n  " + "\n  ".join(bad)
                  + "\nЗапустите python tools/build_plugin.py.")
            return 1
        print(f"dist/kimi-plugin актуален ({len(want)} файлов).")
        return 0
    for rel, text in want.items():
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    for p in sorted(OUT.rglob("*"), reverse=True) if OUT.is_dir() else []:
        if p.is_file() and p.relative_to(OUT).as_posix() not in want:
            p.unlink()
        elif p.is_dir():
            try:
                p.rmdir()
            except OSError:
                pass
    print(f"Собрано: {OUT} ({len(want)} файлов). Установка: /plugins install {OUT}")


if __name__ == "__main__":
    sys.exit(main())
