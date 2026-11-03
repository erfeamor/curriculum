"""Tests for the release scripts (T-504): release-manifest.sh, release-tag.sh,
release-checkout.sh, release-verify.sh and release-protect.sh.

Each test builds a throwaway workspace shaped like this one: a meta repo with
the eight siblings as plain subdirectories, every repo cloned from its own
local bare "origin". The scripts are pointed at it through CV_RELEASE_ROOT, so
nothing here touches the real checkouts or GitHub. release-protect.sh is run
against a stub `gh` on PATH that records its calls.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SIBLINGS = [
    "cv-database",
    "cv-domain-service",
    "cv-bff-node",
    "cv-admin-react",
    "cv-public-vanilla",
    "cv-public-react",
    "cv-observability",
    "cv-infra",
]


class Workspace:
    def __init__(self, base: Path):
        self.base = base
        self.origins = base / "origins"
        self.meta = base / "work"
        self.env = {
            **os.environ,
            "HOME": str(base),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(base / "gitconfig"),
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
            "CV_RELEASE_ROOT": str(base / "work"),
        }
        (base / "gitconfig").write_text("[init]\n\tdefaultBranch = master\n[advice]\n\tdetachedHead = false\n")
        self._repo("curriculum", self.meta)
        for name in SIBLINGS:
            self._repo(name, self.meta / name)

    def git(self, cwd, *args, check=True):
        return subprocess.run(
            ["git", *args], cwd=cwd, env=self.env, check=check, capture_output=True, text=True
        )

    def _repo(self, name, path: Path):
        origin = self.origins / f"{name}.git"
        origin.mkdir(parents=True)
        self.git(origin, "init", "-q", "--bare")
        self.git(self.base, "clone", "-q", str(origin), str(path))
        (path / "README").write_text(name + "\n")
        if name == "curriculum":
            (path / ".gitignore").write_text("".join(f"{s}/\n" for s in SIBLINGS))
        self.git(path, "add", "-A")
        self.git(path, "commit", "-q", "-m", "init")
        self.git(path, "push", "-q", "origin", "master")

    def commit(self, path: Path, msg="change", push=True):
        with open(path / "README", "a") as f:
            f.write(msg + "\n")
        self.git(path, "commit", "-q", "-am", msg)
        if push:
            self.git(path, "push", "-q", "origin", "master")
        return self.head(path)

    def head(self, path: Path):
        return self.git(path, "rev-parse", "HEAD").stdout.strip()

    def run(self, script, *args, env=None):
        return subprocess.run(
            ["bash", str(SCRIPTS / script), *args],
            cwd=self.meta,
            env={**self.env, **(env or {})},
            capture_output=True,
            text=True,
        )

    def manifest_and_merge(self, name="M2"):
        """Generate the manifest and land it on the meta repo's master, the way
        the real flow does through a PR."""
        r = self.run("release-manifest.sh", name)
        assert r.returncode == 0, r.stdout + r.stderr
        self.git(self.meta, "add", f"releases/{name}.json")
        self.git(self.meta, "commit", "-q", "-m", f"release {name} manifest")
        self.git(self.meta, "push", "-q", "origin", "master")

    def release(self, name="M2"):
        self.manifest_and_merge(name)
        r = self.run("release-tag.sh", name)
        assert r.returncode == 0, r.stdout + r.stderr

    def remote_tag(self, repo, name="M2"):
        origin = self.origins / f"{repo}.git"
        r = self.git(origin, "rev-parse", "-q", "--verify", f"refs/tags/{name}^{{commit}}", check=False)
        return r.stdout.strip() or None


class ReleaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="release-test-"))
        self.ws = Workspace(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sib(self, name):
        return self.ws.meta / name

    def tag_short_manifest(self, name="M3"):
        """A meta tag whose manifest omits cv-infra, made by hand: the
        scripts would never produce one, but verify and checkout read
        whatever the tag holds."""
        path = self.ws.meta / "releases" / f"{name}.json"
        path.parent.mkdir(exist_ok=True)
        repos = {n: {"github": f"erfeamor/{n}", "commit": self.ws.head(self.sib(n))} for n in SIBLINGS[:-1]}
        path.write_text(json.dumps({"release": name, "repos": repos}))
        self.ws.git(self.ws.meta, "add", str(path))
        self.ws.git(self.ws.meta, "commit", "-q", "-m", "short manifest")
        self.ws.git(self.ws.meta, "tag", "-a", name, "-m", name)
        for n in SIBLINGS[:-1]:
            self.ws.git(self.sib(n), "tag", "-a", name, "-m", name)
            self.ws.git(self.sib(n), "push", "-q", "origin", f"refs/tags/{name}")
        self.ws.git(self.ws.meta, "push", "-q", "origin", "master", f"refs/tags/{name}")


class TestManifest(ReleaseTestCase):
    def test_records_each_siblings_origin_master_after_fetching(self):
        # A commit pushed from another clone: only a fetch makes it visible.
        other = self.tmp / "other"
        self.ws.git(self.tmp, "clone", "-q", str(self.ws.origins / "cv-bff-node.git"), str(other))
        moved = self.ws.commit(other, "elsewhere")

        r = self.ws.run("release-manifest.sh", "M2")
        self.assertEqual(r.returncode, 0, r.stderr)

        data = json.loads((self.ws.meta / "releases" / "M2.json").read_text())
        self.assertEqual(data["release"], "M2")
        self.assertEqual(sorted(data["repos"]), sorted(SIBLINGS))
        self.assertEqual(data["repos"]["cv-bff-node"]["commit"], moved)
        self.assertEqual(data["repos"]["cv-infra"]["commit"], self.ws.head(self.sib("cv-infra")))
        self.assertEqual(data["repos"]["cv-infra"]["github"], "erfeamor/cv-infra")

    def test_refuses_to_overwrite_an_existing_manifest(self):
        self.assertEqual(self.ws.run("release-manifest.sh", "M2").returncode, 0)
        r = self.ws.run("release-manifest.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already exists", r.stderr)

    def test_rejects_a_name_outside_the_protected_pattern(self):
        r = self.ws.run("release-manifest.sh", "v2")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.ws.meta / "releases").exists())

    def test_leaves_no_file_behind_when_writing_fails(self):
        bin_dir = self.tmp / "failing-python"
        bin_dir.mkdir()
        (bin_dir / "python3").write_text("#!/bin/sh\nexit 1\n")
        (bin_dir / "python3").chmod(0o755)
        r = self.ws.run("release-manifest.sh", "M2", env={"PATH": f"{bin_dir}:{os.environ['PATH']}"})
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.ws.meta / "releases" / "M2.json").exists())
        self.assertEqual(self.ws.run("release-manifest.sh", "M2").returncode, 0)

    def test_refuses_a_missing_sibling(self):
        shutil.rmtree(self.sib("cv-observability"))
        r = self.ws.run("release-manifest.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-observability", r.stderr)


class TestTag(ReleaseTestCase):
    def test_tags_every_repo_on_the_manifest_and_pushes(self):
        self.ws.manifest_and_merge()
        meta_head = self.ws.head(self.ws.meta)
        manifest = json.loads((self.ws.meta / "releases" / "M2.json").read_text())

        r = self.ws.run("release-tag.sh", "M2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        self.assertEqual(self.ws.remote_tag("curriculum"), meta_head)
        for name in SIBLINGS:
            self.assertEqual(self.ws.remote_tag(name), manifest["repos"][name]["commit"], name)

    def test_tags_the_manifest_commit_even_after_master_moves_on(self):
        self.ws.manifest_and_merge()
        pinned = json.loads((self.ws.meta / "releases" / "M2.json").read_text())["repos"]["cv-database"]["commit"]
        self.ws.commit(self.sib("cv-database"), "after the manifest")

        self.assertEqual(self.ws.run("release-tag.sh", "M2").returncode, 0)
        self.assertEqual(self.ws.remote_tag("cv-database"), pinned)

    def test_is_idempotent(self):
        self.ws.release()
        r = self.ws.run("release-tag.sh", "M2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_refuses_when_meta_head_lacks_the_manifest(self):
        r = self.ws.run("release-tag.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("releases/M2.json", r.stderr)
        self.assertIsNone(self.ws.remote_tag("cv-infra"))

    def test_tags_the_meta_commit_that_added_the_manifest_not_a_later_one(self):
        self.ws.manifest_and_merge()
        added = self.ws.head(self.ws.meta)
        self.ws.commit(self.ws.meta, "a later board update")

        r = self.ws.run("release-tag.sh", "M2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.ws.remote_tag("curriculum"), added)

    def test_refuses_a_manifest_that_is_not_on_origin_master(self):
        r = self.ws.run("release-manifest.sh", "M2")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.ws.git(self.ws.meta, "add", "releases/M2.json")
        self.ws.git(self.ws.meta, "commit", "-q", "-m", "unmerged manifest")
        r = self.ws.run("release-tag.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("origin/master", r.stderr)
        self.assertIsNone(self.ws.remote_tag("curriculum"))

    def test_refuses_a_manifest_changed_after_it_was_added(self):
        self.ws.manifest_and_merge()
        path = self.ws.meta / "releases" / "M2.json"
        data = json.loads(path.read_text())
        data["repos"]["cv-infra"]["commit"] = self.ws.head(self.ws.meta)
        path.write_text(json.dumps(data))
        self.ws.git(self.ws.meta, "commit", "-q", "-am", "hand edit")
        self.ws.git(self.ws.meta, "push", "-q", "origin", "master")
        r = self.ws.run("release-tag.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("changed", r.stderr)

    def _merge_broken_manifest(self, mutate):
        self.ws.manifest_and_merge()
        path = self.ws.meta / "releases" / "M2.json"
        # Replace the manifest with a broken one in the commit that adds it.
        self.ws.git(self.ws.meta, "reset", "-q", "--hard", "HEAD~1")
        self.ws.run("release-manifest.sh", "M2")
        data = json.loads(path.read_text())
        path.write_text(mutate(data))
        self.ws.git(self.ws.meta, "add", "releases/M2.json")
        self.ws.git(self.ws.meta, "commit", "-q", "-m", "broken manifest")
        self.ws.git(self.ws.meta, "push", "-q", "-f", "origin", "master")

    def _assert_tag_refused_and_nothing_tagged(self):
        r = self.ws.run("release-tag.sh", "M2")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("manifest", r.stderr)
        for name in ["curriculum", *SIBLINGS]:
            self.assertIsNone(self.ws.remote_tag(name), name)

    def test_refuses_a_manifest_missing_a_sibling(self):
        def drop(d):
            del d["repos"]["cv-infra"]
            return json.dumps(d)
        self._merge_broken_manifest(drop)
        self._assert_tag_refused_and_nothing_tagged()

    def test_refuses_a_manifest_with_an_unknown_repo(self):
        def extra(d):
            d["repos"]["../elsewhere"] = dict(d["repos"]["cv-infra"])
            return json.dumps(d)
        self._merge_broken_manifest(extra)
        self._assert_tag_refused_and_nothing_tagged()

    def test_refuses_malformed_json(self):
        self._merge_broken_manifest(lambda d: "{not json")
        self._assert_tag_refused_and_nothing_tagged()

    def test_refuses_when_a_remote_is_unreachable_and_tags_nothing(self):
        self.ws.manifest_and_merge()
        origin = self.ws.origins / "cv-observability.git"
        origin.rename(origin.with_suffix(".gone"))
        r = self.ws.run("release-tag.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-observability", r.stderr)
        origin.with_suffix(".gone").rename(origin)
        for name in ["curriculum", *SIBLINGS]:
            self.assertIsNone(self.ws.remote_tag(name), name)

    def test_refuses_a_sibling_that_is_not_cloned(self):
        self.ws.manifest_and_merge()
        shutil.rmtree(self.sib("cv-bff-node"))
        r = self.ws.run("release-tag.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-bff-node", r.stderr)
        self.assertIsNone(self.ws.remote_tag("cv-database"))

    def test_a_push_rejected_midway_leaves_meta_untagged_and_a_rerun_completes(self):
        self.ws.manifest_and_merge()
        hook = self.ws.origins / "cv-public-react.git" / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\necho rejected >&2\nexit 1\n")
        hook.chmod(0o755)

        r = self.ws.run("release-tag.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIsNone(self.ws.remote_tag("curriculum"))  # meta goes last

        hook.unlink()
        r = self.ws.run("release-tag.sh", "M2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for name in ["curriculum", *SIBLINGS]:
            self.assertIsNotNone(self.ws.remote_tag(name), name)

    def test_refuses_an_existing_tag_on_another_commit_and_tags_nothing(self):
        self.ws.manifest_and_merge()
        self.ws.git(self.sib("cv-admin-react"), "tag", "M2", "HEAD")
        self.ws.commit(self.sib("cv-admin-react"), "moves past the stray tag")
        # The stray tag is on the manifest's commit: make it point elsewhere.
        self.ws.git(self.sib("cv-admin-react"), "tag", "-f", "M2", "HEAD")

        r = self.ws.run("release-tag.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-admin-react", r.stderr)
        for name in ["curriculum", *SIBLINGS]:
            self.assertIsNone(self.ws.remote_tag(name), name)


class TestVerify(ReleaseTestCase):
    def test_passes_on_a_fresh_clone_set_at_the_release(self):
        self.ws.release()
        fresh = Workspace.__new__(Workspace)
        fresh.__dict__.update(self.ws.__dict__)
        fresh.meta = self.tmp / "fresh"
        fresh.env = {**self.ws.env, "CV_RELEASE_ROOT": str(fresh.meta)}
        self.ws.git(self.tmp, "clone", "-q", str(self.ws.origins / "curriculum.git"), str(fresh.meta))
        for name in SIBLINGS:
            self.ws.git(self.tmp, "clone", "-q", str(self.ws.origins / f"{name}.git"), str(fresh.meta / name))
        self.ws.git(fresh.meta, "checkout", "-q", "M2")
        self.assertEqual(fresh.run("release-checkout.sh", "M2").returncode, 0)

        r = fresh.run("release-verify.sh", "M2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_fails_and_names_a_sibling_checked_out_elsewhere(self):
        self.ws.release()
        self.ws.git(self.ws.meta, "checkout", "-q", "M2")
        self.ws.run("release-checkout.sh", "M2")
        self.ws.git(self.sib("cv-public-react"), "checkout", "-q", "master")
        self.ws.commit(self.sib("cv-public-react"), "newer work")

        r = self.ws.run("release-verify.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-public-react", r.stdout + r.stderr)
        self.assertNotIn("cv-database:", r.stderr)

    def test_fails_when_the_meta_repo_is_not_at_the_release(self):
        self.ws.release()
        self.ws.run("release-checkout.sh", "M2")  # meta stays on master
        self.ws.commit(self.ws.meta, "after the release")

        r = self.ws.run("release-verify.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("curriculum", r.stdout + r.stderr)

    def test_fails_when_the_tag_is_missing_on_the_remote(self):
        self.ws.release()
        self.ws.git(self.ws.meta, "checkout", "-q", "M2")
        self.ws.run("release-checkout.sh", "M2")
        self.ws.git(self.ws.origins / "cv-observability.git", "tag", "-d", "M2")

        r = self.ws.run("release-verify.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-observability", r.stdout + r.stderr)

    def test_fails_when_a_local_tag_differs_from_the_manifest(self):
        self.ws.release()
        self.ws.git(self.ws.meta, "checkout", "-q", "M2")
        self.ws.run("release-checkout.sh", "M2")
        sib = self.sib("cv-domain-service")
        self.ws.git(sib, "checkout", "-q", "master")
        self.ws.git(sib, "tag", "-f", "M2", self.ws.commit(sib, "moved", push=False))

        r = self.ws.run("release-verify.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-domain-service", r.stdout + r.stderr)

    def test_changes_nothing(self):
        self.ws.release()
        before = {n: self.ws.head(self.sib(n)) for n in SIBLINGS}
        self.ws.run("release-verify.sh", "M2")
        self.assertEqual(before, {n: self.ws.head(self.sib(n)) for n in SIBLINGS})


    def test_fails_on_a_manifest_missing_a_sibling(self):
        self.tag_short_manifest()
        self.ws.git(self.ws.meta, "checkout", "-q", "M3")
        r = self.ws.run("release-verify.sh", "M3")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("manifest", r.stderr)
        self.assertNotIn("all 9 repos", r.stdout)

    def test_fails_when_origin_is_unreachable(self):
        self.ws.release()
        self.ws.git(self.ws.meta, "checkout", "-q", "M2")
        self.ws.run("release-checkout.sh", "M2")
        origin = self.ws.origins / "cv-infra.git"
        origin.rename(origin.with_suffix(".gone"))
        r = self.ws.run("release-verify.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("FAIL cv-infra: can't read origin", r.stdout)
        # Every other repo is still reported, not cut short.
        self.assertIn("ok   cv-database", r.stdout)

class TestCheckout(ReleaseTestCase):
    def test_puts_every_sibling_on_its_tag_detached(self):
        self.ws.release()
        manifest = json.loads((self.ws.meta / "releases" / "M2.json").read_text())
        for name in SIBLINGS:
            self.ws.commit(self.sib(name), "after the release")

        r = self.ws.run("release-checkout.sh", "M2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for name in SIBLINGS:
            self.assertEqual(self.ws.head(self.sib(name)), manifest["repos"][name]["commit"], name)
            branch = self.ws.git(self.sib(name), "branch", "--show-current").stdout.strip()
            self.assertEqual(branch, "", name)
        # master is untouched: it still has the post-release commit.
        master = self.ws.git(self.sib("cv-infra"), "rev-parse", "master").stdout.strip()
        self.assertNotEqual(master, manifest["repos"]["cv-infra"]["commit"])

    def test_fetches_tags_a_sibling_does_not_have_yet(self):
        self.ws.release()
        sib = self.sib("cv-bff-node")
        self.ws.git(sib, "tag", "-d", "M2")
        r = self.ws.run("release-checkout.sh", "M2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_refuses_a_dirty_sibling_and_moves_none(self):
        self.ws.release()
        for name in SIBLINGS:
            self.ws.commit(self.sib(name), "after the release")
        before = {n: self.ws.head(self.sib(n)) for n in SIBLINGS}
        with open(self.sib("cv-admin-react") / "README", "a") as f:
            f.write("uncommitted\n")

        r = self.ws.run("release-checkout.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-admin-react", r.stderr)
        self.assertEqual(before, {n: self.ws.head(self.sib(n)) for n in SIBLINGS})

    def test_refuses_a_tag_that_differs_from_the_manifest(self):
        self.ws.release()
        sib = self.sib("cv-public-vanilla")
        self.ws.git(sib, "tag", "-f", "M2", self.ws.commit(sib, "moved", push=False))

        r = self.ws.run("release-checkout.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-public-vanilla", r.stderr)

    def test_refuses_an_unknown_release(self):
        r = self.ws.run("release-checkout.sh", "M3")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("M3", r.stderr)


    def test_refuses_an_untracked_file_and_moves_none(self):
        self.ws.release()
        for name in SIBLINGS:
            self.ws.commit(self.sib(name), "after the release")
        before = {n: self.ws.head(self.sib(n)) for n in SIBLINGS}
        (self.sib("cv-infra") / "stray.txt").write_text("untracked\n")

        r = self.ws.run("release-checkout.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-infra", r.stderr)
        self.assertEqual(before, {n: self.ws.head(self.sib(n)) for n in SIBLINGS})

    def test_refuses_a_local_meta_tag_that_differs_from_origins(self):
        self.ws.release()
        self.ws.commit(self.ws.meta, "after the release")
        self.ws.git(self.ws.meta, "tag", "-f", "M2", "HEAD")  # stale local tag

        r = self.ws.run("release-checkout.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("origin", r.stderr)

    def test_refuses_a_local_sibling_tag_that_differs_from_origins(self):
        self.ws.release()
        sib = self.sib("cv-observability")
        self.ws.git(sib, "tag", "-f", "M2", self.ws.commit(sib, "moved", push=False))
        r = self.ws.run("release-checkout.sh", "M2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cv-observability", r.stderr)

    def test_refuses_a_manifest_missing_a_sibling(self):
        self.tag_short_manifest()
        r = self.ws.run("release-checkout.sh", "M3")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("manifest", r.stderr)

class TestProtect(ReleaseTestCase):
    def setUp(self):
        super().setUp()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.log = self.tmp / "gh.log"
        self.existing = self.tmp / "existing"  # repos that already have the ruleset
        stub = self.bin / "gh"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            f'log="{self.log}"; existing="{self.existing}"\n'
            'printf "%s\\n" "$*" >> "$log"\n'
            'case "$*" in\n'
            '  *"--method POST"*|*"--method PUT"*) cat >> "$log"; echo >> "$log" ;;\n'
            '  *rulesets*) repo=$(echo "$2" | cut -d/ -f3)\n'
            '    if grep -qx "$repo" "$existing" 2>/dev/null; then echo 77; fi ;;\n'
            "esac\n"
        )
        stub.chmod(0o755)
        self.env = {"PATH": f"{self.bin}:{os.environ['PATH']}"}

    def test_creates_the_ruleset_in_all_nine_repos(self):
        r = self.ws.run("release-protect.sh", env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log = self.log.read_text()
        for repo in ["curriculum", *SIBLINGS]:
            self.assertIn(f"api repos/erfeamor/{repo}/rulesets --method POST", log)
        payload = json.loads(log.split("--method POST")[1].split("\n", 1)[1].split("\n")[0])
        self.assertEqual(payload["target"], "tag")
        self.assertEqual(payload["enforcement"], "active")
        self.assertEqual(payload["bypass_actors"], [])
        self.assertEqual(payload["conditions"]["ref_name"]["include"], ["refs/tags/M*"])
        self.assertEqual(sorted(r["type"] for r in payload["rules"]), ["deletion", "update"])

    def test_lists_only_the_repos_own_rulesets_across_all_pages(self):
        self.ws.run("release-protect.sh", env=self.env)
        log = self.log.read_text()
        self.assertIn("api repos/erfeamor/cv-infra/rulesets?includes_parents=false --paginate", log)

    def test_updates_an_existing_ruleset_in_place(self):
        self.existing.write_text("cv-infra\n")
        r = self.ws.run("release-protect.sh", env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log = self.log.read_text()
        self.assertIn("api repos/erfeamor/cv-infra/rulesets/77 --method PUT", log)
        self.assertNotIn("api repos/erfeamor/cv-infra/rulesets --method POST", log)


if __name__ == "__main__":
    unittest.main()
