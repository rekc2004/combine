#!/usr/bin/env python3
"""Проверяет манифесты скиллов и обновляет таблицу скиллов в README.

    python tools/check.py          проверить и показать таблицу
    python tools/check.py --write  заодно обновить таблицу между маркерами в README.md
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync  # noqa: E402

COSTS = {"дёшево", "средне", "дорого"}
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


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    write = "--write" in sys.argv
    skills, errors, rows = sync.discover_skills(), [], []
    for key, s in sorted(skills.items()):
        spec = s["spec"]
        if s["cost"] not in COSTS:
            errors.append(f"{key}: cost должен быть одним из {sorted(COSTS)}")
        if s["cost"] == "дорого" and s["default"]:
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
        for f in s["files"]:
            if SUSPICIOUS.search((s["base"] / f).read_text(encoding="utf-8")):
                errors.append(f"{key}/{f}: подозрительная фраза (инъекция или запуск скачанного), проверьте вручную")
        src = spec.get("source")
        rows.append(f"| `{key}` | {s['cost']} | {'да' if s['default'] else 'нет, `--with ' + key + '`'} | "
                    f"{desc.split('] ', 1)[-1]} | {(src or {}).get('license', 'свой')} |")
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
