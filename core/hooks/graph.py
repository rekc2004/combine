"""SessionStart: keep the code graph fresh (docs/GRAPH.md, .claude/combine/graph.json).

Fresh graph: one line pointing at it. Stale or missing: start the builder detached and return at once,
so the session start never waits for it. Standard library only.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "graph"))
from _common import disabled_modules, project_dir, read_stdin_json  # noqa: E402

BUILDER = os.path.join(os.path.dirname(HERE), "graph", "build.py")
LOCK_TTL_S = 300          # a build older than this is considered dead


def main():
    read_stdin_json()
    off = disabled_modules()
    if "graph" in off or "all" in off:      # older _common.py does not list graph in ALL_HOOKS
        return
    root = project_dir()
    if not os.path.isfile(BUILDER):
        return
    from build import query_path, stamp  # noqa: E402  same comparison the builder records
    gpath = os.path.join(root, ".claude", "combine", "graph.json")
    try:
        with open(gpath, encoding="utf-8") as f:
            old = json.load(f)
    except (OSError, ValueError):
        old = None
    if old and old.get("stamp") == stamp(root):
        print(f"[Combine] Code graph is fresh: docs/GRAPH.md (built {old.get('built')}). "
              f"Read it before searching code; exact callers/deps: python {query_path(root)} --help.")
        return

    lock = os.path.join(root, ".claude", "combine", "graph.lock")
    try:
        if time.time() - os.path.getmtime(lock) < LOCK_TTL_S:
            print("[Combine] Code graph is being rebuilt by another session; docs/GRAPH.md may be stale for a few seconds.")
            return
    except OSError:
        pass
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    with open(lock, "w") as f:
        f.write(str(time.time()))
    kwargs = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "cwd": root}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen([sys.executable, "-I", BUILDER, root, "--unlock", lock], **kwargs)
    state = "stale" if old else "missing"
    print(f"[Combine] Code graph was {state}; rebuilding in the background (seconds). "
          "Read docs/GRAPH.md once it is updated" + (" (the current one is older than the code)." if old else "."))


if __name__ == "__main__":
    main()
