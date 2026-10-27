"""Combine code graph builder.

Writes two files into the project:
  docs/GRAPH.md                 one-two page map for the model: areas, files, who depends on whom, hubs
  .claude/combine/graph.json    full graph for queries (query.py: callers, deps, users, find)

Standard library only, nothing to install. Two layers:
  files    imports of TS/JS/Python, #include of C/C++
  symbols  definitions and calls. Python through `ast` (exact); TS/JS/C by brace spans and names
           (approximate: a call is matched to a definition by name, so same-named functions in
           different files merge, and calls through objects or pointers are invisible).
mcp-context-graph 0.1.0 was evaluated for the symbol layer and dropped: its ingest creates only
module/class/function nodes and "contains" edges, no calls or imports (scout, 2026-10-27).

Untrusted input: the project's files. They are only read and parsed, never executed.
Usage: python build.py <project root>
"""
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict

CODE_EXT = {".ts", ".tsx", ".js", ".mjs", ".cjs", ".jsx", ".py", ".c", ".h", ".cpp", ".hpp", ".cc"}
C_EXT = {".c", ".h", ".cpp", ".hpp", ".cc"}
SKIP_DIRS = {"node_modules", ".git", "build", "dist", "__pycache__", ".venv", "venv", "managed_components",
             ".toolchain", "generated", "coverage", ".next", "out", "target"}
MAX_FILE_BYTES = 400_000          # bigger files are generated or vendored; skip
MD_MAX_LINES = 160                # GRAPH.md stays one-two pages


def lang_ext(root, f):
    """Extension that picks the parser. Scripts without one (e.g. tools/linux/some-agent) count as
    Python when their first line says so; shell scripts have no parser and stay out."""
    ext = os.path.splitext(f)[1].lower()
    if ext:
        return ext
    try:
        with open(os.path.join(root, f), "rb") as h:
            first = h.readline(200)
    except OSError:
        return ""
    return ".py" if first.startswith(b"#!") and b"python" in first else ""


def project_files(root):
    """Tracked files from git when available (respects .gitignore), else a filtered walk."""
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, timeout=30, check=True).stdout
        files = [f for f in out.decode("utf-8", "replace").split("\0") if f]
    except (OSError, subprocess.SubprocessError):
        files = []
        for d, dirs, names in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
            files += [os.path.relpath(os.path.join(d, n), root).replace("\\", "/") for n in names]
    keep = []
    for f in files:
        if any(part in SKIP_DIRS for part in f.split("/")[:-1]) or f.startswith(".claude/"):
            continue
        if lang_ext(root, f) not in CODE_EXT:
            continue
        try:
            if os.path.getsize(os.path.join(root, f)) > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        keep.append(f)
    return sorted(keep)


def read(root, f):
    try:
        with open(os.path.join(root, f), encoding="utf-8", errors="replace") as h:
            return h.read()
    except OSError:
        return ""


# --- file layer -------------------------------------------------------------------------------

JS_IMPORT = re.compile(r"""(?:import\s[^'"]*?from\s*|import\s*\(\s*|require\s*\(\s*|export\s[^'"]*?from\s*|import\s+)['"]([^'"]+)['"]""")
PY_IMPORT = re.compile(r"^\s*(?:from\s+([.\w]+)\s+import|import\s+([\w.]+))", re.M)
C_INCLUDE = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.M)


def resolve_js(src, spec, known):
    if not spec.startswith("."):
        return None
    base = os.path.normpath(os.path.join(os.path.dirname(src), spec)).replace("\\", "/")
    stem = re.sub(r"\.(js|mjs|cjs|jsx)$", "", base)          # TS sources import "./x.js"
    for cand in (base, stem + ".ts", stem + ".tsx", base + ".ts", base + ".tsx", base + ".js", base + ".mjs",
                 base + "/index.ts", base + "/index.tsx", base + "/index.js"):
        if cand in known:
            return cand
    return None


def resolve_py(src, mod, known):
    if mod.startswith("."):
        up = len(mod) - len(mod.lstrip("."))
        base = os.path.dirname(src)
        for _ in range(up - 1):
            base = os.path.dirname(base)
        rel = mod.lstrip(".").replace(".", "/")
        cands = [f"{base}/{rel}.py".lstrip("/"), f"{base}/{rel}/__init__.py".lstrip("/")] if rel else [f"{base}/__init__.py".lstrip("/")]
    else:
        rel = mod.replace(".", "/")
        cands = [f"{rel}.py", f"{rel}/__init__.py", f"{os.path.dirname(src)}/{rel}.py".lstrip("/")]
    for c in cands:
        if c in known:
            return c
    return None


def resolve_c(src, inc, by_name, known):
    local = os.path.normpath(os.path.join(os.path.dirname(src), inc)).replace("\\", "/")
    if local in known:
        return local
    hits = by_name.get(os.path.basename(inc), [])
    if len(hits) == 1:
        return hits[0]
    # same component first, then the shortest path: header names repeat across firmwares
    same = [h for h in hits if h.split("/")[:2] == src.split("/")[:2]]
    return (same or sorted(hits, key=len) or [None])[0]


def file_edges(root, files, texts):
    known = set(files)
    by_name = defaultdict(list)
    for f in files:
        by_name[os.path.basename(f)].append(f)
    edges = set()
    for f in files:
        ext = lang_ext(root, f)
        text = texts[f]
        if ext in C_EXT:
            targets = [resolve_c(f, m, by_name, known) for m in C_INCLUDE.findall(text)]
        elif ext == ".py":
            targets = [resolve_py(f, a or b, known) for a, b in PY_IMPORT.findall(text)]
        else:
            targets = [resolve_js(f, m, known) for m in JS_IMPORT.findall(text)]
        edges.update((f, t) for t in targets if t and t != f)
    return sorted(edges)


# --- symbols ------------------------------------------------------------------------------------

KEYWORDS = {"if", "for", "while", "switch", "return", "sizeof", "else", "do", "case", "defined", "catch",
            "function", "typeof", "new", "await", "super", "constructor", "_Static_assert"}
C_DEF = re.compile(r"^(?!\s)(?:static\s+|inline\s+|extern\s+|const\s+|unsigned\s+|signed\s+|struct\s+|enum\s+)*"
                   r"[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{)]*\)\s*\{", re.M)
# function f(...) {   const f = (...) => {   const f = async function(   class C {   method(...) {   async m(...): T {
JS_DEF = re.compile(
    r"(?:^|\n)[ \t]*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*[<(][^{]*?\{"
    r"|(?:^|\n)[ \t]*(?:export\s+)?(?:const|let)\s+([A-Za-z_$][\w$]*)\s*(?::[^=\n]+)?=\s*(?:async\s+)?(?:function\b[^{]*|\([^)]*\)[^=\n{]*=>\s*|[A-Za-z_$][\w$]*\s*=>\s*)\{"
    r"|(?:^|\n)[ \t]*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)[^{]*\{"
    r"|(?:^|\n)[ \t]+(?:(?:public|private|protected|static|async|readonly|override|get|set)\s+)*(#?[A-Za-z_$][\w$]*)\s*(?:<[^>\n]*>)?\([^)\n]*\)\s*(?::\s*[^{\n]+)?\{")
# Only bare calls: `x.push(` or `p->send(` would match every same-named method in the project.
CALL = re.compile(r"(?<![.\w$>#])([A-Za-z_$][\w$]*)\s*\(")


def strip_code(text):
    """Comments and string contents out, line breaks kept, so braces and names in them do not count."""
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"(?m)(?<![:\\])//[^\n]*", "", text)
    return re.sub(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|`(?:\\.|[^`\\])*`',
                  lambda m: m.group(0)[0] + "\n" * m.group(0).count("\n") + m.group(0)[0], text)


def brace_defs(f, code, pattern):
    for m in pattern.finditer(code):
        name = next((g for g in m.groups() if g), None)
        if not name or name.lstrip("#") in KEYWORDS:
            continue
        depth, i = 1, m.end()
        while i < len(code) and depth:
            depth += {"{": 1, "}": -1}.get(code[i], 0)
            i += 1
        kind = "class" if "class " in m.group(0) else "function"
        yield name, code.count("\n", 0, m.start() + (1 if code[m.start()] == "\n" else 0)) + 1, kind, code[m.end():i]


def py_defs(f, text):
    import ast
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return
    lines = text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = "\n".join(lines[node.lineno - 1:(node.end_lineno or node.lineno)])
            yield node.name, node.lineno, "class" if isinstance(node, ast.ClassDef) else "function", body


def symbols(root, files, texts):
    """Definitions with their bodies, then calls inside each body to names defined somewhere in the project."""
    defs, bodies = defaultdict(list), []
    for f in files:
        ext = lang_ext(root, f)
        if ext == ".py":
            found, lang = py_defs(f, texts[f]), "py"
        elif ext in C_EXT:
            found, lang = brace_defs(f, strip_code(texts[f]), C_DEF), "c"
        else:
            found, lang = brace_defs(f, strip_code(texts[f]), JS_DEF), "js"
        for name, line, kind, body in found:
            defs[name].append({"name": name, "file": f, "line": line, "kind": kind, "lang": lang})
            bodies.append((f, name, body))
    calls = set()
    for f, name, body in bodies:
        for callee in set(CALL.findall(body)):
            if callee in defs and callee != name:
                calls.add((f"{f}::{name}", callee))
    return [s for v in defs.values() for s in v], sorted(calls)


# --- output -------------------------------------------------------------------------------------

def area(f):
    parts = f.split("/")
    return "/".join(parts[:2]) if len(parts) > 2 else (parts[0] if len(parts) > 1 else ".")


def is_test(f):
    return bool(re.search(r"(^|/)(tests?|__tests__|spec)(/|$)|\.(test|spec)\.\w+$|(^|/)test_\w+\.py$", f))


def stamp(root):
    """What the graph was built from: HEAD plus the list of changed files. The hook compares it."""
    def git(*args):
        try:
            return subprocess.run(["git", "-C", root, *args], capture_output=True, timeout=10,
                                  check=True).stdout.decode("utf-8", "replace").strip()
        except (OSError, subprocess.SubprocessError):
            return ""
    # Changed files with size and mtime: a second edit of an already changed file must count too.
    # The graph's own files and Combine's directory are left out, or every build would make the
    # next one look stale.
    changes = []
    for l in git("status", "--porcelain", "--untracked-files=all").splitlines():
        path = l[3:].split(" -> ")[-1].strip('"')
        if path in ("docs/GRAPH.md",) or path.startswith(".claude/"):
            continue
        try:
            st = os.stat(os.path.join(root, path))
            changes.append(f"{l[:2]} {path} {st.st_size} {int(st.st_mtime)}")
        except OSError:
            changes.append(f"{l[:2]} {path} gone")
    return {"head": git("rev-parse", "HEAD"), "changes": "\n".join(changes)}


def query_path(root):
    """Where query.py of this install lives, as the model should type it."""
    q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "query.py")
    home, rel = os.path.expanduser("~"), os.path.relpath(q, root) if os.path.splitdrive(q)[0] == os.path.splitdrive(root)[0] else q
    if q.startswith(home + os.sep):
        return "~/" + os.path.relpath(q, home).replace(os.sep, "/")
    return rel.replace(os.sep, "/")


def write_markdown(path, root, files, fedges, syms, calls, built, head):
    users, uses = Counter(t for _, t in fedges), defaultdict(list)
    for s, t in fedges:
        uses[s].append(t)
    per_area = defaultdict(list)
    for f in files:
        per_area[area(f)].append(f)
    cross = Counter((area(s), area(t)) for s, t in fedges if area(s) != area(t))
    callers = Counter(c for src, c in calls if not is_test(src.split("::")[0]))
    sym_per_file = Counter(s["file"] for s in syms)

    out = ["# Code graph", "",
           f"Built by Combine `hook-graph` {built} from the working tree at `{head[:8] or 'no git'}` "
           "(uncommitted changes included). "
           f"{len(files)} files, {len(fedges)} file links, {len(syms)} definitions, {len(calls)} calls. "
           "Do not edit: rebuilt automatically when the code changes.",
           "",
           "Read this before searching the code. Exact questions go to the full graph:",
           f"`python {query_path(root)} users|deps <file>` and `callers|calls|find <name>`.",
           "Calls in TS/JS/C are matched by name: same-named functions merge, calls through objects are not seen.",
           "", "## Areas", "",
           "| Area | Files | Definitions | Uses areas |", "|---|---|---|---|"]
    for a in sorted(per_area):
        deps = ", ".join(f"{b} ({n})" for (x, b), n in sorted(cross.items(), key=lambda kv: -kv[1]) if x == a)
        out.append(f"| `{a}` | {len(per_area[a])} | {sum(sym_per_file[f] for f in per_area[a])} | {deps or '—'} |")
    out += ["", "## Most used files", "", "Imported or included by the most other files (tests not counted).", ""]
    prod_users = Counter(t for s, t in fedges if not is_test(s))
    for f, n in prod_users.most_common(15):
        out.append(f"- `{f}` ← {n}")
    out += ["", "## Most called functions", ""]
    for name, n in callers.most_common(15):
        where = ", ".join(sorted({f"`{s['file']}:{s['line']}`" for s in syms if s["name"] == name})[:3])
        out.append(f"- `{name}` ← {n} callers; defined {where}")
    out += ["", "## Files by area", "", "`file` ← used by N → uses (first 4). Tests left out.", ""]
    for a in sorted(per_area):
        prod = [f for f in per_area[a] if not is_test(f)]
        if not prod:
            continue
        out.append(f"### `{a}`")
        for f in sorted(prod, key=lambda x: (-users[x], x))[:12]:
            u = ", ".join(f"`{t.split('/')[-1]}`" for t in sorted(uses[f])[:4])
            short = f[len(a) + 1:] if f.startswith(a + "/") else f
            out.append(f"- `{short}` ← {users[f]}" + (f" → {u}" if u else ""))
        if len(prod) > 12:
            out.append(f"- … and {len(prod) - 12} more")
        out.append("")
    if len(out) > MD_MAX_LINES:
        # Cut at a blank line (a section boundary) so the note fits inside the limit and no heading is
        # left without its list.
        limit = MD_MAX_LINES - 1
        cut = max((i for i in range(limit) if out[i] == ""), default=limit)
        out = out[:cut] + ["", "…cut here to keep this page short; the full graph is in `.claude/combine/graph.json`."]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as h:
        h.write("\n".join(out) + "\n")


def main():
    args = sys.argv[1:]
    unlock = None
    if "--unlock" in args:                  # the hook passes its lock file; removed when done
        i = args.index("--unlock")
        unlock = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
    try:
        build(os.path.abspath(args[0] if args else "."))
    finally:
        if unlock:
            try:
                os.remove(unlock)
            except OSError:
                pass


def build(root):
    t0 = time.time()
    st = stamp(root)
    files = project_files(root)
    texts = {f: read(root, f) for f in files}
    fedges = file_edges(root, files, texts)
    syms, calls = symbols(root, files, texts)
    built = time.strftime("%Y-%m-%d %H:%M")
    graph = {"version": 1, "built": built, "stamp": st, "files": files,
             "fileEdges": fedges, "symbols": syms, "calls": calls}
    jpath = os.path.join(root, ".claude", "combine", "graph.json")
    os.makedirs(os.path.dirname(jpath), exist_ok=True)
    tmp = jpath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as h:
        json.dump(graph, h, ensure_ascii=False)
    os.replace(tmp, jpath)
    write_markdown(os.path.join(root, "docs", "GRAPH.md"), root, files, fedges, syms, calls, built, st["head"])
    print(f"graph: {len(files)} files, {len(fedges)} links, {len(syms)} definitions, {len(calls)} calls, "
          f"{time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
