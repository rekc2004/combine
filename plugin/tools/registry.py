#!/usr/bin/env python3
"""Детерминированный реестр инструментов Claude/Kimi без сети и embeddings."""
import argparse
import json
import os
from pathlib import Path


def registry_path():
    base = os.environ.get("COMBINE_HOME") or os.path.join(os.path.expanduser("~"), ".combine")
    return Path(base) / "TOOLS.json"


def load(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        data = {"version": 1, "tools": []}
    except (OSError, ValueError):
        raise SystemExit(f"{path}: не удалось прочитать реестр; он не изменён")
    if not isinstance(data.get("tools"), list):
        raise SystemExit(f"{path}: ожидается объект с массивом tools")
    return data


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def text(record):
    return " | ".join(str(record.get(k, "")) for k in ("name", "location", "purpose", "why", "limits", "verified"))


def score(record, query):
    name = str(record.get("name", "")).casefold()
    aliases = [str(x).casefold() for x in record.get("aliases", [])]
    if query == name:
        return 100
    if query in aliases:
        return 90
    if query in name:
        return 80
    haystack = json.dumps(record, ensure_ascii=False).casefold()
    terms = query.split()
    return 60 if all(term in haystack for term in terms) else 0


def find(path, query, project=None):
    q = query.casefold().strip()
    scored = sorted(((score(record, q), record) for record in load(path)["tools"]),
                    key=lambda item: (-item[0], str(item[1].get("name", "")).casefold()))
    found = False
    for value, record in scored:
        if value:
            print(f"GLOBAL {text(record)}")
            found = True
    if project:
        project_file = Path(project) / "PROJECT.md"
        try:
            lines = project_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
        terms = q.split()
        for number, line in enumerate(lines, 1):
            if all(term in line.casefold() for term in terms):
                print(f"PROJECT {project_file}:{number}: {line.strip()}")
                found = True
    if not found:
        print("(not found; registry and project were not modified)")
    return 0 if found else 1


def main():
    parser = argparse.ArgumentParser(description="Глобальный индекс инструментов и PROJECT.md")
    sub = parser.add_subparsers(dest="action", required=True)
    find_parser = sub.add_parser("find")
    find_parser.add_argument("query", nargs="+")
    find_parser.add_argument("--project")
    sub.add_parser("list")
    upsert = sub.add_parser("upsert")
    upsert.add_argument("name")
    upsert.add_argument("--type", default="program")
    upsert.add_argument("--location")
    upsert.add_argument("--command")
    upsert.add_argument("--purpose", default="")
    upsert.add_argument("--why", default="")
    upsert.add_argument("--limits", default="")
    upsert.add_argument("--verified", default="NOT VERIFIED")
    upsert.add_argument("--aliases", default="")
    args = parser.parse_args()
    path = registry_path()
    if args.action == "find":
        return find(path, " ".join(args.query), args.project)
    data = load(path)
    if args.action == "list":
        for record in sorted(data["tools"], key=lambda r: str(r.get("name", "")).casefold()):
            print(text(record))
        return 0
    if not args.location:
        parser.error("upsert требует --location (путь или не-secret endpoint)")
    record = {"name": args.name, "type": args.type, "location": args.location,
              "command": args.command or args.location, "purpose": args.purpose,
              "why": args.why, "limits": args.limits, "verified": args.verified,
              "aliases": [x.strip() for x in args.aliases.split(",") if x.strip()]}
    records = data["tools"]
    for index, old in enumerate(records):
        if str(old.get("name", "")).casefold() == args.name.casefold():
            merged = dict(old)
            for key, value in record.items():
                if key == "aliases" and not value:
                    continue
                if key in {"purpose", "why", "limits"} and not value:
                    continue
                if key == "verified" and value == "NOT VERIFIED" and old.get("verified") not in {None, "", "NOT VERIFIED"}:
                    continue
                if key == "command" and args.command is None and "command" in old:
                    continue
                merged[key] = value
            records[index] = merged
            break
    else:
        records.append(record)
    save(path, data)
    print("UPSERT " + text(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
