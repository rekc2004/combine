"""Questions to the full code graph (.claude/combine/graph.json) without reading files.

  users <file>     who imports / includes this file
  deps <file>      what this file imports / includes
  callers <name>   which functions call <name> (by name: same-named functions merge)
  calls <name>     what <name> calls
  find <name>      where <name> is defined
<file> may be a path suffix (e.g. ports/light.ts). Run from the project root or pass --root <dir>.
"""
import json
import os
import sys


def main():
    args = sys.argv[1:]
    root = os.getcwd()
    if "--root" in args:
        i = args.index("--root")
        root = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2 or args[0] not in {"users", "deps", "callers", "calls", "find"}:
        print(__doc__.strip())
        return 2
    cmd, arg = args
    try:
        with open(os.path.join(root, ".claude", "combine", "graph.json"), encoding="utf-8") as f:
            g = json.load(f)
    except (OSError, ValueError):
        print("No graph: .claude/combine/graph.json is missing. It is built at session start (hook-graph).")
        return 1

    def match_file(x):
        hits = [f for f in g["files"] if f == arg or f.endswith("/" + arg)]
        if len(hits) > 1:
            print(f"Ambiguous: {', '.join(hits[:10])}")
        return hits

    out = []
    if cmd in {"users", "deps"}:
        for f in match_file(arg):
            out += [s if cmd == "users" else t for s, t in g["fileEdges"] if (t if cmd == "users" else s) == f]
    elif cmd == "callers":
        out = [src for src, callee in g["calls"] if callee == arg]
    elif cmd == "calls":
        out = [callee for src, callee in g["calls"] if src.split("::")[-1] == arg]
    else:
        out = [f"{s['file']}:{s['line']} {s['kind']}" for s in g["symbols"] if s["name"] == arg]
    print("\n".join(sorted(set(out))) or "(none)")
    print(f"-- graph built {g.get('built')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
