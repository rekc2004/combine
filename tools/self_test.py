#!/usr/bin/env python3
"""Повторяемые контрактные регрессии Combine на временных проектах."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}


def run(*args, cwd=ROOT):
    return subprocess.run([sys.executable, *args], cwd=cwd, env=ENV,
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], env=ENV,
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout.strip()


def init_product(root):
    root.mkdir()
    (root / ".git").mkdir()
    (root / "README.md").write_text("initial\n", encoding="utf-8")
    (root / "PROJECT.md").write_text("owner project data\n", encoding="utf-8")
    (root / "plugin").mkdir()
    (root / "plugin" / "stale.md").write_text("stale\n", encoding="utf-8")
    git(root, "init", "-q")
    git(root, "config", "user.email", "combine-test@example.invalid")
    git(root, "config", "user.name", "Combine Test")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "initial")


def graph_module():
    path = ROOT / "core" / "graph" / "build.py"
    spec = importlib.util.spec_from_file_location("combine_graph_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CombineContracts(unittest.TestCase):
    @unittest.skipUnless((ROOT / "tools" / "release.py").is_file(), "release tool is lab-only")
    def test_release_rejects_dirty_without_writes(self):
        with tempfile.TemporaryDirectory() as d:
            product = Path(d) / "product"
            init_product(product)
            readme = product / "README.md"
            readme.write_text("local uncommitted edit\n", encoding="utf-8")
            result = run(str(ROOT / "tools" / "release.py"), "--product", str(product))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(readme.read_text(encoding="utf-8"), "local uncommitted edit\n")
            self.assertTrue((product / "plugin" / "stale.md").is_file())

    @unittest.skipUnless((ROOT / "tools" / "release.py").is_file(), "release tool is lab-only")
    def test_clean_release_removes_stale_and_preserves_owner_files(self):
        with tempfile.TemporaryDirectory() as d:
            product = Path(d) / "product"
            init_product(product)
            result = run(str(ROOT / "tools" / "release.py"), "--product", str(product))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((product / "plugin" / "stale.md").exists())
            self.assertEqual((product / "PROJECT.md").read_text(encoding="utf-8"), "owner project data\n")
            self.assertTrue((product / "core" / "templates" / "LESSONS.md").is_file())
            self.assertFalse((product / "LESSONS.md").exists())
            self.assertIn("data = read_stdin_json()",
                          (product / "plugin" / "hooks" / "graph.py").read_text(encoding="utf-8"))
            self.assertNotIn("data = read_stdin_json()",
                             (product / "core" / "hooks" / "graph.py").read_text(encoding="utf-8"))
            again = run(str(ROOT / "tools" / "release.py"), "--product", str(product), "--dry-run")
            self.assertIn("Расхождений нет.", again.stdout)

    def test_sync_rollback_and_project_preservation(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            script = str(ROOT / "tools" / "sync.py")
            result = run(script, "--target", str(target))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            project = target / "PROJECT.md"
            project.write_text("owner data\nnew tool entry\n", encoding="utf-8")
            self.assertEqual(run(script, "--target", str(target)).returncode, 0)
            self.assertEqual(project.read_text(encoding="utf-8"), "owner data\nnew tool entry\n")
            lock = json.loads((target / ".combine.lock").read_text(encoding="utf-8"))
            self.assertNotIn("PROJECT.md", lock["files"])
            (target / ".claude" / "settings.json").write_text("{bad", encoding="utf-8")
            before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            failed = run(script, "--target", str(target))
            self.assertNotEqual(failed.returncode, 0)
            after = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_triz_switch_and_optional_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            script = str(ROOT / "tools" / "sync.py")
            result = run(script, "--target", str(target), "--without", "triz")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            navigator = target / ".claude" / "skills" / "combine-triz-navigator" / "SKILL.md"
            self.assertFalse(navigator.exists())
            architect = (target / ".claude" / "agents" / "combine-architect.md").read_text(encoding="utf-8")
            self.assertIn("if combine-triz-navigator is installed and enabled", architect)
            self.assertIn("If TRIZ is off or unavailable", architect)
            scout = (target / ".claude" / "agents" / "combine-scout.md").read_text(encoding="utf-8")
            self.assertIn("Never edit, create or delete files", scout)
            state = json.loads((target / ".combine.json").read_text(encoding="utf-8"))
            self.assertIn("triz", state["disabled"])
            pipeline = (target / ".claude" / "combine" / "pipeline.md").read_text(encoding="utf-8")
            self.assertIn("when installed and not disabled", pipeline)
            self.assertIn("If TRIZ is off or unavailable", pipeline)
            self.assertEqual(run(script, "--target", str(target), "--with", "triz").returncode, 0)
            self.assertTrue(navigator.is_file())
            self.assertEqual(run(script, "--target", str(target), "--without", "pipeline").returncode, 0)
            claude = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertNotIn("PROJECT.md", claude)

    def test_graph_failure_does_not_commit_fresh_stamp(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            (target / "a.py").write_text("a = 1\n", encoding="utf-8")
            module = graph_module()
            module.build(str(target))
            graph_path = target / ".claude" / "combine" / "graph.json"
            old_graph = graph_path.read_bytes()
            old_doc = (target / "docs" / "GRAPH.md").read_bytes()
            (target / "a.py").write_text("a = 2\n", encoding="utf-8")
            original = module.write_markdown

            def fail(*_args):
                raise OSError("simulated markdown failure")

            module.write_markdown = fail
            try:
                with self.assertRaises(OSError):
                    module.build(str(target))
            finally:
                module.write_markdown = original
            self.assertEqual(graph_path.read_bytes(), old_graph)
            self.assertEqual((target / "docs" / "GRAPH.md").read_bytes(), old_doc)
            self.assertFalse((target / "docs" / "GRAPH.md.tmp").exists())

    def test_non_git_graph_stamp_changes(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            (target / "a.py").write_text("a = 1\n", encoding="utf-8")
            module = graph_module()
            first = module.stamp(str(target))
            (target / "b.py").write_text("b = 1\n", encoding="utf-8")
            second = module.stamp(str(target))
            self.assertNotEqual(first, second)
            self.assertEqual(second, module.stamp(str(target)))

    def test_global_tool_registry_and_state(self):
        with tempfile.TemporaryDirectory() as d:
            memory = Path(d) / "memory"
            project = Path(d) / "project"
            project.mkdir()
            (project / "docs").mkdir()
            (project / "docs" / "TASK.md").write_text("registry task\n", encoding="utf-8")
            (project / "PROJECT.md").write_text("local-helper: C:/project/helper.py\n", encoding="utf-8")
            ENV["COMBINE_HOME"] = str(memory)
            script = str(ROOT / "core" / "tools" / "registry.py")
            try:
                first = run(script, "upsert", "ffmpeg", "--location", "C:/tools/ffmpeg.exe",
                            "--purpose", "video conversion", "--why", "verified local binary",
                            "--aliases", "ffmeg,video", "--verified", "self-test")
                self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
                self.assertEqual(run(script, "upsert", "other", "--location", "D:/other/tool.exe").returncode, 0)
                updated = run(script, "upsert", "ffmpeg", "--location", "D:/media/ffmpeg.exe",
                              "--purpose", "video conversion", "--why", "moved installation")
                self.assertEqual(updated.returncode, 0, updated.stdout + updated.stderr)
                found = run(script, "find", "ffmeg", "--project", str(project))
                self.assertIn("D:/media/ffmpeg.exe", found.stdout)
                local = run(script, "find", "helper", "--project", str(project))
                self.assertIn("local-helper", local.stdout)
                records = json.loads((memory / "TOOLS.json").read_text(encoding="utf-8"))["tools"]
                self.assertEqual(len(records), 2)
                ffmpeg = next(record for record in records if record["name"] == "ffmpeg")
                self.assertEqual(ffmpeg["verified"], "self-test")
                self.assertIn("ffmeg", ffmpeg["aliases"])
                state_env = dict(ENV)
                state_env["CLAUDE_PROJECT_DIR"] = str(project)
                state = subprocess.run([sys.executable, str(ROOT / "core" / "hooks" / "state.py")],
                                       input="{}", text=True, encoding="utf-8", capture_output=True,
                                       cwd=ROOT, env=state_env, timeout=30)
                self.assertIn("D:/media/ffmpeg.exe", state.stdout)
                (memory / "TOOLS.json").write_text("{broken", encoding="utf-8")
                before = (memory / "TOOLS.json").read_bytes()
                corrupt = run(script, "upsert", "new", "--location", "E:/new/tool.exe")
                self.assertNotEqual(corrupt.returncode, 0)
                self.assertEqual((memory / "TOOLS.json").read_bytes(), before)
            finally:
                ENV.pop("COMBINE_HOME", None)

    def test_plugin_layout_and_kimi_system(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import build_plugin
        built = build_plugin.build()
        self.assertIn("plugin/hooks/graph.py", built)
        self.assertNotIn("core/hooks/graph.py", built)
        system = built["plugin/SYSTEM.md"]
        self.assertIn("# Kimi capabilities", system)
        self.assertNotIn("~/.claude/combine/graph/query.py", system)
        self.assertIn("Never Ask", system)
        self.assertIn("TRIZ route by Combine stage", system)
        self.assertIn("Dialogue | M1/A1", system)
        self.assertIn("Closing | A10/A11", system)
        navigator = built["plugin/skills/combine-triz-navigator/SKILL.md"]
        self.assertIn("Combine stage entry points", navigator)
        self.assertIn("Skeleton | P9/P10/P16/P26", navigator)
        architect = built["plugin/agents/combine-architect.md"]
        self.assertIn("if combine-triz-navigator is installed and enabled", architect)
        self.assertIn("If TRIZ is off or unavailable", architect)
        for template in ("TASK.md", "PROJECT.md", "LESSONS.md"):
            self.assertIn(f"plugin/templates/{template}", built)
        self.assertIn("plugin/templates/TOOLS.json", built)
        self.assertIn("plugin/tools/registry.py", built)
        without = build_plugin.build({"triz"})
        self.assertFalse(any(path.startswith("plugin/skills/combine-triz-") for path in without))
        self.assertIn("If TRIZ is off or unavailable", without["plugin/agents/combine-architect.md"])
        with self.assertRaises(SystemExit):
            build_plugin.build({"unknown-pack"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
