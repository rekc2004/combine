#!/usr/bin/env python3
"""Проверяет манифесты скиллов и обновляет таблицу скиллов в README.

    python tools/check.py          проверить и показать таблицу
    python tools/check.py --write  заодно обновить таблицу между маркерами в README.md
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync  # noqa: E402

COSTS = {"cheap", "medium", "expensive", "дёшево", "средне", "дорого"}
MARK_BEGIN, MARK_END = "<!-- skills-table:begin -->", "<!-- skills-table:end -->"
SUSPICIOUS = re.compile(r"(?i)ignore (all |any )?(previous|prior) instructions|игнорируй (все )?предыдущие инструкции|curl[^\n]*\|\s*(ba)?sh")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


KNOWN_TOOLS = {"Read", "Grep", "Glob", "Edit", "Write", "Bash"}


def check_agents(errors):
    """Валидирует core/agents.json: единая схема моделей и ролей (Claude и Kimi читают одно место)."""
    path = sync.CORE / "agents.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        errors.append(f"agents.json: не читается ({e})")
        return
    models, agents = data.get("models"), data.get("agents")
    if not isinstance(models, dict) or not models:
        errors.append("agents.json: нет непустого объекта models")
        return
    if not isinstance(agents, dict) or not agents:
        errors.append("agents.json: нет непустого объекта agents")
        return
    for name, spec in agents.items():
        key = f"агент {name}"
        if not sync.NAME_RE.match(name):
            errors.append(f"{key}: имя должно быть kebab-case из [a-z0-9-]")
        if not isinstance(spec, dict):
            errors.append(f"{key}: спецификация должна быть объектом")
            continue
        for field in ("description", "whenToUse", "role"):
            if not isinstance(spec.get(field), str) or not spec[field].strip():
                errors.append(f"{key}: обязательное строковое поле {field}")
        desc = spec.get("description", "")
        if "\n" in desc or len(desc) > 300:
            errors.append(f"{key}: description одной строкой до 300 символов")
        model = spec.get("model")
        if model not in models:
            errors.append(f"{key}: model {model!r} нет в models")
        tools = spec.get("tools")
        if not isinstance(tools, str) or not tools.strip():
            errors.append(f"{key}: tools — непустая строка")
        else:
            unknown = [t for t in (x.strip() for x in tools.split(","))
                       if t and not t.startswith("mcp__") and t not in KNOWN_TOOLS]
            if unknown:
                errors.append(f"{key}: неизвестные инструменты: {', '.join(unknown)}")
        if "${" in str(spec.get("role", "")):
            errors.append(f"{key}: role содержит ${{...}} — тело агента это шаблон, плейсхолдер сломается")


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    write = "--write" in sys.argv
    skills, errors, rows = sync.discover_skills(), [], []
    check_agents(errors)
    for key, s in sorted(skills.items()):
        spec = s["spec"]
        if s["cost"] not in COSTS:
            errors.append(f"{key}: cost должен быть одним из {sorted(COSTS)}")
        if s["cost"] == "expensive" and s["default"]:
            errors.append(f"{key}: дорогой скилл не может быть default:true")
        if "source" in spec and not (spec["source"].get("license") and spec["source"].get("url")):
            errors.append(f"{key}: для чужого скилла обязательны source.url и source.license")
        text = (s["base"] / "SKILL.md").read_text(encoding="utf-8")
        fm = frontmatter(text)
        want = f"combine-{s['pack']}-{s['name']}"
        if fm.get("name") != want:
            errors.append(f"{key}: в SKILL.md name должен быть {want!r}, а там {fm.get('name')!r}")
        desc = fm.get("description", "")
        if not desc.startswith("[" + (s["cost"] or "?") + "]"):
            errors.append(f"{key}: description должен начинаться с маркера стоимости [{s['cost']}]")
        if "\n" in desc or len(desc) > 200:
            errors.append(f"{key}: description должно быть одной строкой до 200 символов")
        for ref in re.findall(r"`(references/[^`]+)`", text):
            if ref not in s["files"]:
                errors.append(f"{key}: reference {ref!r} не перечислен в files")
        for f in s["files"]:
            body = (s["base"] / f).read_text(encoding="utf-8")
            if f.startswith("references/"):
                for ref in re.findall(r"`([^`/\n]+\.md)`", body):
                    if not ((s["base"] / f).parent / ref).is_file():
                        errors.append(f"{key}/{f}: локальная ссылка не найдена: {ref}")
            if SUSPICIOUS.search(body):
                errors.append(f"{key}/{f}: подозрительная фраза (инъекция или запуск скачанного), проверьте вручную")
        src = spec.get("source")
        rows.append(f"| `{key}` | {s['cost']} | {'да' if s['default'] else 'нет, `--with ' + key + '`'} | "
                    f"{spec.get('about_ru') or desc.split('] ', 1)[-1]} | {(src or {}).get('license', 'свой')} |")
    for pack_dir in sorted(p for p in sync.SKILLS.iterdir() if p.is_dir()):
        manifest = pack_dir / "pack.json"
        if manifest.exists():
            for r in sync.load_json(manifest).get("recommends", []):
                if not (isinstance(r, dict) and r.get("name") and r.get("note")):
                    errors.append(f"{pack_dir.name}: каждая запись recommends обязана иметь name и note")
    table = ("| Ключ | Стоимость | Ставится по умолчанию | Что делает | Лицензия |\n|---|---|---|---|---|\n"
             + "\n".join(rows)) if rows else "_Скиллов пока нет._"
    print(table)
    if errors:
        print("\nОШИБКИ:\n  " + "\n  ".join(errors))
        return 1
    if write:
        readme = Path(__file__).resolve().parent.parent / "README.md"
        text = readme.read_text(encoding="utf-8")
        if MARK_BEGIN not in text or MARK_END not in text:
            print("В README нет маркеров таблицы скиллов.")
            return 1
        new = re.sub(re.escape(MARK_BEGIN) + r".*?" + re.escape(MARK_END),
                     lambda _m: f"{MARK_BEGIN}\n{table}\n{MARK_END}", text, flags=re.S)
        readme.write_text(new, encoding="utf-8")
        print("\nREADME.md обновлён.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
