#!/usr/bin/env python3
"""Tests for scripts/qa-env-override.py.

The defect this tool fixes (T-028) is SILENT: a stack that builds `master`
instead of the worktree under test answers every request plausibly. So the
regressions worth guarding are the ones nothing else would notice — a compose
service renamed, a build context moved to long form, a repo that is bind-mounted
rather than built. Each of those has a case here.

Run:  python3 -m unittest discover -s scripts -p 'test_*.py'
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parent / "qa-env-override.py"
_spec = importlib.util.spec_from_file_location("qa_env_override", SCRIPT)
qeo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qeo)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_COMPOSE = yaml.safe_load((REPO_ROOT / "docker-compose.dev.yml").read_text())


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                   capture_output=True, text=True)


def make_repo(path: Path, origin: str, branch: str = "master") -> Path:
    """A throwaway git repo that looks like a product checkout."""
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "test@example.invalid")
    git(path, "config", "user.name", "test")
    (path / "README.md").write_text("x\n")
    (path / "sql").mkdir(exist_ok=True)
    (path / "sql" / "V1__x.sql").write_text("-- x\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "init")
    git(path, "branch", "-M", branch)
    git(path, "remote", "add", "origin", origin)
    return path


class BuildContextDiscovery(unittest.TestCase):
    def test_short_and_long_form(self):
        compose = {"services": {
            "a": {"build": "./cv-a"},
            "b": {"build": {"context": "./cv-b", "dockerfile": "Dockerfile"}},
            "c": {"image": "nginx"},
        }}
        self.assertEqual(qeo.service_build_contexts(compose),
                         {"a": "./cv-a", "b": "./cv-b"})

    def test_match_is_by_basename_not_by_table(self):
        compose = {"services": {
            "domain-service": {"build": "./cv-domain-service"},
            "bff": {"build": {"context": "../repos/cv-bff-node/"}},
        }}
        self.assertEqual(qeo.match_build_services(compose, "cv-bff-node"), ["bff"])
        self.assertEqual(qeo.match_build_services(compose, "cv-domain-service"),
                         ["domain-service"])
        self.assertEqual(qeo.match_build_services(compose, "cv-infra"), [])

    def test_live_compose_still_matches_both_buildable_repos(self):
        # Guards a rename or a context move in docker-compose.dev.yml.
        self.assertEqual(qeo.match_build_services(DEV_COMPOSE, "cv-domain-service"),
                         ["domain-service"])
        self.assertEqual(qeo.match_build_services(DEV_COMPOSE, "cv-bff-node"), ["bff"])


class MountRewriting(unittest.TestCase):
    WT = Path("/wt/T-151")

    def test_rewrites_only_the_host_side(self):
        new, reason = qeo.rewrite_mount_source("./cv-database/sql", "cv-database", self.WT)
        self.assertEqual(new, "/wt/T-151/sql")
        self.assertEqual(reason, "repointed")

    def test_absolute_source(self):
        new, _ = qeo.rewrite_mount_source(
            "/home/u/work/curriculum/cv-observability/grafana/provisioning",
            "cv-observability", self.WT)
        self.assertEqual(new, "/wt/T-151/grafana/provisioning")

    def test_named_volume_and_unrelated_and_interpolated(self):
        self.assertIsNone(qeo.rewrite_mount_source("cv-dev-mysql-data", "cv-database", self.WT)[0])
        self.assertIsNone(qeo.rewrite_mount_source("./devstack/prometheus.dev.yml",
                                                   "cv-database", self.WT)[0])
        new, reason = qeo.rewrite_mount_source("${SQL_DIR}/cv-database/sql",
                                               "cv-database", self.WT)
        self.assertIsNone(new)
        self.assertIn("interpolation", reason)

    def test_regression_finding_1_cv_database_is_mounted_not_built(self):
        """A repo with no build context is still under test when it is mounted."""
        services, rewrites, _ = qeo.match_mount_services(DEV_COMPOSE, "cv-database", self.WT)
        self.assertEqual(sorted(services), ["flyway"])
        self.assertEqual(services["flyway"], ["/wt/T-151/sql:/flyway/sql:ro"])
        self.assertEqual(rewrites[0]["from"], "./cv-database/sql")

    def test_regression_finding_1_cv_observability(self):
        services, _, _ = qeo.match_mount_services(DEV_COMPOSE, "cv-observability", self.WT)
        self.assertEqual(sorted(services), ["grafana"])
        # the named volume and the container path are untouched
        self.assertIn("cv-dev-grafana-data:/var/lib/grafana", services["grafana"])
        self.assertIn("/wt/T-151/grafana/provisioning:/etc/grafana/provisioning:ro",
                      services["grafana"])

    def test_long_form_mount(self):
        compose = {"services": {"s": {"volumes": [
            {"type": "bind", "source": "./cv-database/sql", "target": "/sql",
             "read_only": True},
            {"type": "volume", "source": "data", "target": "/var"},
        ]}}}
        services, _, _ = qeo.match_mount_services(compose, "cv-database", self.WT)
        self.assertEqual(services["s"][0]["source"], "/wt/T-151/sql")
        self.assertEqual(services["s"][0]["target"], "/sql")
        self.assertTrue(services["s"][0]["read_only"])
        self.assertEqual(services["s"][1]["source"], "data")

    def test_exposure_is_visible_even_when_not_rewritable(self):
        compose = {"services": {"s": {"volumes": ["${D}/cv-database/sql:/sql:ro"]}}}
        services, _, exposures = qeo.match_mount_services(compose, "cv-database", self.WT)
        self.assertEqual(services, {})
        self.assertEqual(exposures[0]["service"], "s")
        self.assertEqual(qeo.mount_exposures(DEV_COMPOSE, "cv-database"),
                         [{"service": "flyway", "source": "./cv-database/sql"}])


class OverrideDocument(unittest.TestCase):
    def render(self, doc):
        return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)

    def test_ports_only_when_nothing_is_repointed(self):
        doc, ports, build, mounts = qeo.build_override(DEV_COMPOSE, 30)
        self.assertIsNone(build)
        self.assertIsNone(mounts)
        self.assertEqual(doc["services"]["domain-service"]["ports"], ["8110:8080"])
        self.assertNotIn("build", doc["services"]["domain-service"])
        self.assertIn("!override", self.render(doc))

    def test_build_repoint_keeps_port_isolation(self):
        target = {"services": ["domain-service"], "context": "/wt/T-1",
                  "labels": {"x": "y"}}
        doc, _, build, _ = qeo.build_override(DEV_COMPOSE, 30, target)
        svc = doc["services"]["domain-service"]
        self.assertEqual(svc["build"], {"context": "/wt/T-1", "labels": {"x": "y"}})
        self.assertEqual(svc["ports"], ["8110:8080"])   # isolation not traded away
        self.assertEqual(build["services"], ["domain-service"])

    def test_mount_repoint_on_a_service_with_no_ports(self):
        # flyway publishes nothing: the repoint must still land.
        doc, _, _, mounts = qeo.build_override(
            DEV_COMPOSE, 30, None, {"flyway": ["/wt/T-151/sql:/flyway/sql:ro"]})
        self.assertEqual(doc["services"]["flyway"]["volumes"],
                         ["/wt/T-151/sql:/flyway/sql:ro"])
        self.assertEqual(mounts["services"], ["flyway"])
        self.assertIn("volumes: !override", self.render(doc))


class WorktreeResolution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_identity_from_git_including_dirty(self):
        wt = make_repo(self.root / "cv-database", "git@github.com:erfeamor/cv-database.git")
        ident = qeo.repo_identity(wt)
        self.assertEqual(ident["repo"], "cv-database")
        self.assertEqual(ident["branch"], "master")
        self.assertFalse(ident["dirty"])
        (wt / "sql" / "V1__x.sql").write_text("-- changed\n")
        self.assertTrue(qeo.repo_identity(wt)["dirty"])

    def test_finding_3_subdirectory_is_rejected(self):
        wt = make_repo(self.root / "cv-database", "git@github.com:erfeamor/cv-database.git")
        with self.assertRaises(qeo.WorktreeError) as cm:
            qeo.repo_identity(wt / "sql")
        self.assertIn("not the root of a git work tree", str(cm.exception))

    def test_finding_3_empty_and_missing_paths_are_fatal(self):
        with self.assertRaises(qeo.WorktreeError):
            qeo.resolve_worktree("T-1", "", self.root)
        with self.assertRaises(qeo.WorktreeError):
            qeo.resolve_worktree("T-1", str(self.root / "nope"), self.root)

    def test_conventional_path_present_and_absent(self):
        # The branch the real pipeline uses: --task only, no --worktree.
        wt = make_repo(self.root / "T-151", "git@github.com:erfeamor/cv-database.git")
        got, note = qeo.resolve_worktree("T-151", None, self.root)
        self.assertEqual(got, wt.resolve())
        self.assertIn("conventional path", note)
        got, note = qeo.resolve_worktree("T-999", None, self.root)
        self.assertIsNone(got)
        self.assertIn("no worktree", note)

    def test_declared_branch_reads_board_frontmatter(self):
        tasks = self.root / "tasks"
        tasks.mkdir()
        (tasks / "T-151-dev-seeds.md").write_text(textwrap.dedent("""\
            ---
            id: T-151
            branch: feat/dev-seeds-idempotent
            ---
            body
            """))
        branch, path = qeo.declared_branch("T-151", tasks)
        self.assertEqual(branch, "feat/dev-seeds-idempotent")
        self.assertEqual(path.name, "T-151-dev-seeds.md")
        self.assertEqual(qeo.declared_branch("T-999", tasks), (None, None))


class CommandLine(unittest.TestCase):
    """End-to-end: the failure modes must be non-zero, not merely mentioned."""

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_missing_worktree_is_non_zero(self):
        r = self.run_cli("--task", "T-1", "--worktree", str(self.root / "nope"), "--stdout")
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not exist", r.stderr)

    def test_require_worktree_is_non_zero_when_nothing_repointed(self):
        r = self.run_cli("--task", "T-999", "--slot", "9", "--stdout", "--require-worktree",
                         "--worktree-root", str(self.root))
        self.assertEqual(r.returncode, 1)
        self.assertIn("--require-worktree", r.stderr)

    def test_branch_mismatch_is_non_zero(self):
        wt = make_repo(self.root / "cv-database", "git@github.com:erfeamor/cv-database.git")
        r = self.run_cli("--task", "T-151", "--worktree", str(wt), "--stdout")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("branch mismatch", r.stderr)
        # ...and the escape hatch works
        r = self.run_cli("--task", "T-151", "--worktree", str(wt), "--stdout",
                         "--no-branch-check")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_note_is_persisted_in_the_artifact_when_nothing_is_repointed(self):
        r = self.run_cli("--task", "T-999", "--slot", "9", "--stdout",
                         "--worktree-root", str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("# Worktree repoint (T-028):", r.stdout)
        self.assertIn("MAIN CHECKOUT", r.stdout)

    def test_mounted_repo_is_repointed_end_to_end(self):
        wt = make_repo(self.root / "T-151", "git@github.com:erfeamor/cv-database.git",
                       branch="feat/whatever")
        r = self.run_cli("--task", "T-151", "--slot", "9", "--stdout",
                         "--worktree-root", str(self.root), "--no-branch-check",
                         "--require-worktree")
        self.assertEqual(r.returncode, 0, r.stderr)
        doc = yaml.safe_load(r.stdout.replace("!override", ""))
        self.assertEqual(doc["services"]["flyway"]["volumes"],
                         [f"{wt}/sql:/flyway/sql:ro"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
