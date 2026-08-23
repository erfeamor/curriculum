#!/usr/bin/env python3
"""Tests for scripts/board-check.py.

Each of the seven checks gets a red-then-green pair: a crafted fixture that
fails, and the same fixture with the defect removed, passing (per this
board's standing practice of confirming red first). The four regression
fixtures reproduce the real incidents named in T-031's task file verbatim
enough to trip on the same shape; the live-board assertions guard against the
duplicate-key false positives verified against T-002 and T-103.

Run:  python3 -m unittest discover -s scripts -p 'test_*.py'
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "board-check.py"
_spec = importlib.util.spec_from_file_location("board_check", SCRIPT)
bc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bc)

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_TASKS_DIR = REPO_ROOT / ".claude" / "tasks"


def board_line(task_id: str, title: str, status: str, extra_cols=("", "", "")) -> str:
    owner, deps, pr = extra_cols
    return f"| [{task_id}]({task_id}-x.md) | {title} | repo | {status} | {owner} | {deps} | {pr} |"


TABLE_HEADER = "| ID | Title | Repo | Status | Owner | Depends on | PR |"
TABLE_SEP = "|----|-------|------|--------|-------|------------|----|"


class Board:
    """A throwaway .claude/tasks/-shaped directory for one test."""

    def __init__(self, tmp: Path):
        self.dir = tmp
        self.dir.mkdir(parents=True, exist_ok=True)
        self._rows = []

    def add_task(self, task_id: str, frontmatter: str, title="Task", status="todo",
                 in_board=True, board_status=None):
        fname = f"{task_id}-x.md"
        (self.dir / fname).write_text(f"---\n{frontmatter}---\nbody\n")
        if in_board:
            self._rows.append(board_line(
                task_id, title, board_status if board_status is not None else status))

    def add_raw_board_row(self, row: str):
        self._rows.append(row)

    def write_board(self):
        lines = ["# Board", "", TABLE_HEADER, TABLE_SEP, *self._rows]
        (self.dir / "TASKS.md").write_text("\n".join(lines) + "\n")

    def check(self, **kw):
        return bc.run(self.dir)


def make_board(tmp: Path) -> Board:
    return Board(tmp)


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)


# --------------------------------------------------------------------------
# Check 1 — duplicate keys, raw-line detection
# --------------------------------------------------------------------------

class DuplicateKeys(TempDirCase):
    def test_red_top_level_duplicate(self):
        b = make_board(self.root)
        b.add_task("T-900", textwrap.dedent("""\
            id: T-900
            status: todo
            owner:
            status: in_progress
            """))
        b.write_board()
        findings = b.check()
        dup = [f for f in findings if f.key == "status"]
        self.assertTrue(dup, "expected a duplicate-key finding for status:")
        self.assertIn("duplicate key", dup[0].message)
        self.assertEqual(dup[0].line, 5)  # the SECOND occurrence

    def test_green_no_duplicate(self):
        b = make_board(self.root)
        b.add_task("T-900", textwrap.dedent("""\
            id: T-900
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: []
            """))
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key == "status" for f in findings))

    def test_red_nested_duplicate_under_checkpoint(self):
        b = make_board(self.root)
        b.add_task("T-901", textwrap.dedent("""\
            id: T-901
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              worktree: /some/path
              worktree: none
            """), status="done")
        b.write_board()
        findings = b.check()
        dup = [f for f in findings if f.key == "worktree"]
        self.assertTrue(dup, "expected a duplicate-key finding nested under checkpoint:")

    def test_no_false_positive_on_sequence_items(self):
        """The exact false-positive shape check 1 must not produce: a literal
        YAML block sequence of mappings where sibling items legitimately
        repeat the same key names."""
        b = make_board(self.root)
        b.add_task("T-902", textwrap.dedent("""\
            id: T-902
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              worktree: none
              review_trail:
                - round: 1
                  finding: first issue
                - round: 2
                  finding: second issue
                - round: 3
                  finding: third issue
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key in ("round", "finding") for f in findings),
                          f"false positive on sequence items: {[str(f) for f in findings]}")

    def test_no_false_positive_on_sibling_nested_mappings(self):
        """T-002's real shape: pre_apply_gate / apply / post_apply are three
        DIFFERENT nested mappings under checkpoint, each with its own `run:`
        / `commit:` / `evidence:` — not one mapping with duplicates. A flat
        per-indent-level counter (rather than a scope-aware one) flags this."""
        b = make_board(self.root)
        b.add_task("T-903", textwrap.dedent("""\
            id: T-903
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              worktree: none
              pre_apply_gate:
                run: 2026-08-08
                commit: abc123
                evidence: link-one
              apply:
                run: 2026-08-08
                commit: def456
                evidence: link-two
              post_apply:
                run: 2026-08-08
                commit: ghi789
                evidence: link-three
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key in ("run", "commit", "evidence") for f in findings),
                          f"false positive on sibling nested mappings: {[str(f) for f in findings]}")

    def test_live_board_t002_and_t103_no_false_positive(self):
        """Assert directly against the real files named in the spec."""
        fm = bc.read_frontmatter(LIVE_TASKS_DIR / "T-002-jenkins-on-drone-host.md")
        findings = bc.find_duplicate_keys(fm[0], fm[1], LIVE_TASKS_DIR / "T-002-jenkins-on-drone-host.md")
        self.assertEqual(findings, [], [str(f) for f in findings])

        fm = bc.read_frontmatter(LIVE_TASKS_DIR / "T-103-skills-catalog-and-assignments.md")
        findings = bc.find_duplicate_keys(fm[0], fm[1], LIVE_TASKS_DIR / "T-103-skills-catalog-and-assignments.md")
        self.assertEqual(findings, [], [str(f) for f in findings])


class DuplicateKeyRegressions(TempDirCase):
    """The four incidents named in T-031's acceptance criteria, reproduced
    at the shape that made each one invisible to a plain yaml.safe_load."""

    def test_t152_triple_worktree(self):
        b = make_board(self.root)
        b.add_task("T-910", textwrap.dedent("""\
            id: T-910
            status: done
            owner: backend-developer
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/9
            checkpoint:
              stage: done
              worktree: none               # cleared at close-out
              worktree: /home/erfeamor/work/cvdl-worktrees/T-910
              worktree: pending
            """), status="done")
        b.write_board()
        findings = b.check()
        dup = [f for f in findings if f.key == "worktree"]
        # Three occurrences -> two duplicate findings (2nd shadows 1st, 3rd
        # shadows 2nd) -- both must be reported, not just the first.
        self.assertEqual(len(dup), 2, [str(f) for f in findings])

    def test_t202_second_security_review(self):
        b = make_board(self.root)
        b.add_task("T-911", textwrap.dedent("""\
            id: T-911
            status: done
            owner: fullstack-developer
            risk: normal
            security_review: true
            depends_on: []
            pr: https://example.invalid/pr/9
            checkpoint:
              stage: done
              worktree: none
              security_review: true
              security_review: done
            """), status="done")
        b.write_board()
        findings = b.check()
        dup = [f for f in findings if f.key == "security_review"]
        self.assertTrue(dup, [str(f) for f in findings])

    def test_t104_review_round_shadowing(self):
        b = make_board(self.root)
        b.add_task("T-912", textwrap.dedent("""\
            id: T-912
            status: in_review
            owner: backend-developer
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/9
            checkpoint:
              stage: pr
              worktree: /wt/T-912
              review_round: 1
              review_round: 0
            """), status="in_review")
        b.write_board()
        findings = b.check()
        dup = [f for f in findings if f.key == "review_round"]
        self.assertTrue(dup, [str(f) for f in findings])
        self.assertIn("shadow", dup[0].message)

    def test_t002_style_board_file_status_mismatch(self):
        b = make_board(self.root)
        b.add_task("T-913", textwrap.dedent("""\
            id: T-913
            status: done
            owner: infrastructure-engineer
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/9
            checkpoint:
              stage: done
              worktree: none
            """), status="done", board_status="in_review")
        b.write_board()
        findings = b.check()
        mismatch = [f for f in findings
                    if "board row reads status" in f.message]
        self.assertTrue(mismatch, [str(f) for f in findings])
        self.assertIn("'in_review'", mismatch[0].message)
        self.assertIn("'done'", mismatch[0].message)


# --------------------------------------------------------------------------
# Check 2 — board row <-> file agreement
# --------------------------------------------------------------------------

class BoardFileAgreement(TempDirCase):
    def base_fm(self, status="todo", owner=""):
        return textwrap.dedent(f"""\
            id: T-920
            status: {status}
            owner: {owner}
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """)

    def test_red_missing_board_row(self):
        b = make_board(self.root)
        b.add_task("T-920", self.base_fm(), in_board=False)
        b.write_board()
        findings = b.check()
        self.assertTrue(any("no row in any Status-bearing" in f.message for f in findings))

    def test_red_orphan_board_row(self):
        b = make_board(self.root)
        b.write_board()  # no task files at all
        b.add_raw_board_row(board_line("T-921", "Ghost", "todo"))
        b.write_board()
        findings = b.check()
        self.assertTrue(any("no task file" in f.message for f in findings))

    def test_red_status_mismatch(self):
        b = make_board(self.root)
        b.add_task("T-920", self.base_fm(status="done", owner="someone"),
                   status="done", board_status="in_review")
        b.write_board()
        findings = b.check()
        self.assertTrue(any("board row reads status" in f.message for f in findings))

    def test_green_agrees(self):
        b = make_board(self.root)
        b.add_task("T-920", self.base_fm(status="todo"), status="todo")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.file.name == "TASKS.md" for f in findings))

    def test_ignores_non_status_tables(self):
        """A summary table with no Status column (e.g. 'filed from this run')
        must not be read as a board row, even if it names a task id."""
        b = make_board(self.root)
        b.add_task("T-920", self.base_fm(status="todo"), status="todo")
        b.write_board()
        extra = "\n\n| ID | What it is |\n|---|---|\n| [T-920](T-920-x.md) | some summary text |\n"
        p = b.dir / "TASKS.md"
        p.write_text(p.read_text() + extra)
        findings = b.check()
        dupes = [f for f in findings if "expected exactly one" in f.message]
        self.assertEqual(dupes, [], [str(f) for f in findings])


# --------------------------------------------------------------------------
# Check 3 — status/owner coherence
# --------------------------------------------------------------------------

class StatusOwnerCoherence(TempDirCase):
    def test_red_todo_with_owner(self):
        b = make_board(self.root)
        b.add_task("T-930", textwrap.dedent("""\
            id: T-930
            status: todo
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertTrue(any("must be unowned" in f.message for f in findings))

    def test_red_in_progress_without_owner(self):
        b = make_board(self.root)
        b.add_task("T-931", textwrap.dedent("""\
            id: T-931
            status: in_progress
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="in_progress")
        b.write_board()
        findings = b.check()
        self.assertTrue(any("requires an owner" in f.message for f in findings))

    def test_green(self):
        b = make_board(self.root)
        b.add_task("T-932", textwrap.dedent("""\
            id: T-932
            status: in_progress
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="in_progress")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key == "owner" for f in findings))


# --------------------------------------------------------------------------
# Check 4 — checkpoint.worktree cleared on done
# --------------------------------------------------------------------------

class WorktreeCleared(TempDirCase):
    def test_red_done_with_worktree_path(self):
        b = make_board(self.root)
        b.add_task("T-940", textwrap.dedent("""\
            id: T-940
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              worktree: /home/erfeamor/work/cvdl-worktrees/T-940
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "checkpoint.worktree" for f in findings))

    def test_green_done_with_worktree_none(self):
        b = make_board(self.root)
        b.add_task("T-941", textwrap.dedent("""\
            id: T-941
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              worktree: none
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key == "checkpoint.worktree" for f in findings))

    def test_unclaimed_task_pre_claim_worktree_not_flagged(self):
        """checkpoint.worktree on a non-done task is a pre-claim convention,
        not close-out drift (board rule confirmed 2026-08-22 for T-104)."""
        b = make_board(self.root)
        b.add_task("T-942", textwrap.dedent("""\
            id: T-942
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            checkpoint:
              worktree: /home/erfeamor/work/cvdl-worktrees/T-942
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key == "checkpoint.worktree" for f in findings))


# --------------------------------------------------------------------------
# Check 5 — pr: present on in_review/done
# --------------------------------------------------------------------------

class PrPresence(TempDirCase):
    def test_red_done_missing_pr_key_entirely(self):
        b = make_board(self.root)
        b.add_task("T-950", textwrap.dedent("""\
            id: T-950
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "pr" for f in findings))

    def test_red_in_review_empty_pr(self):
        b = make_board(self.root)
        b.add_task("T-951", textwrap.dedent("""\
            id: T-951
            status: in_review
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="in_review")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "pr" for f in findings))

    def test_red_checkpoint_pr_disagrees(self):
        b = make_board(self.root)
        b.add_task("T-952", textwrap.dedent("""\
            id: T-952
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              pr: https://example.invalid/pr/2
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "checkpoint.pr" for f in findings))

    def test_green_done_with_pr(self):
        b = make_board(self.root)
        b.add_task("T-953", textwrap.dedent("""\
            id: T-953
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key in ("pr", "checkpoint.pr") for f in findings))

    def test_green_done_with_explicit_none_sentinel(self):
        """The T-010 live-board case: a done task whose work shipped
        entirely through OTHER tasks' PRs. `pr: none` is a recorded
        decision, not the T-011/T-009/T-019 omission bug."""
        b = make_board(self.root)
        b.add_task("T-954", textwrap.dedent("""\
            id: T-954
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: none
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key == "pr" for f in findings))

    def test_red_in_review_cannot_use_none_sentinel(self):
        """A PR is definitionally open at in_review -- the sentinel is only
        legitimate on done."""
        b = make_board(self.root)
        b.add_task("T-955", textwrap.dedent("""\
            id: T-955
            status: in_review
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: none
            """), status="in_review")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "pr" for f in findings))


# --------------------------------------------------------------------------
# Check 6 — depends_on resolves
# --------------------------------------------------------------------------

class DependsOnResolves(TempDirCase):
    def test_red_unresolved_dependency(self):
        b = make_board(self.root)
        b.add_task("T-960", textwrap.dedent("""\
            id: T-960
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: [T-999]
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "depends_on" and "T-999" in f.message for f in findings))

    def test_green_resolved_dependency(self):
        b = make_board(self.root)
        b.add_task("T-961", textwrap.dedent("""\
            id: T-961
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="todo")
        b.add_task("T-962", textwrap.dedent("""\
            id: T-962
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: [T-961]
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key == "depends_on" for f in findings))


# --------------------------------------------------------------------------
# Check 7 — controlled vocabularies
# --------------------------------------------------------------------------

class ControlledVocabularies(TempDirCase):
    def test_red_bad_status(self):
        b = make_board(self.root)
        b.add_task("T-970", textwrap.dedent("""\
            id: T-970
            status: closed
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="closed")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "status" and "not one of" in f.message for f in findings))

    def test_red_bad_risk(self):
        b = make_board(self.root)
        b.add_task("T-971", textwrap.dedent("""\
            id: T-971
            status: todo
            owner:
            risk: extreme
            security_review: false
            depends_on: []
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "risk" for f in findings))

    def test_red_security_review_wrong_vocabulary(self):
        b = make_board(self.root)
        b.add_task("T-972", textwrap.dedent("""\
            id: T-972
            status: todo
            owner:
            risk: normal
            security_review: required
            depends_on: []
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "security_review" and "not a real boolean" in f.message
                             for f in findings))

    def test_red_missing_risk_and_security_review_when_not_exempt(self):
        b = make_board(self.root)
        b.add_task("T-973", textwrap.dedent("""\
            id: T-973
            status: todo
            owner:
            depends_on: []
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "risk" for f in findings))
        self.assertTrue(any(f.key == "security_review" for f in findings))

    def test_green(self):
        b = make_board(self.root)
        b.add_task("T-974", textwrap.dedent("""\
            id: T-974
            status: todo
            owner:
            risk: trivial
            security_review: false
            depends_on: []
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key in ("status", "risk", "security_review") for f in findings))

    def test_exemption_does_not_require_risk_or_security_review(self):
        """The 2026-08-17 sweep ruling: five deliberately-unrefined tasks
        carry neither key, on purpose."""
        b = make_board(self.root)
        b.add_task("T-201", textwrap.dedent("""\
            id: T-201
            status: todo
            owner:
            depends_on: []
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key in ("risk", "security_review") for f in findings))

    def test_exemption_does_not_suppress_a_present_but_wrong_value(self):
        """The exemption is 'do not require', not 'never check' -- if an
        exempt task DOES carry the key, it still has to be well-formed."""
        b = make_board(self.root)
        b.add_task("T-301", textwrap.dedent("""\
            id: T-301
            status: todo
            owner:
            risk: super-high
            depends_on: []
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "risk" for f in findings))


# --------------------------------------------------------------------------
# End-to-end / CLI
# --------------------------------------------------------------------------

class CommandLine(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT))

    def test_live_board_exits_zero(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, f"stdout={r.stdout!r} stderr={r.stderr!r}")
        self.assertIn("clean", r.stderr)

    def test_help(self):
        r = self.run_cli("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("board-check", r.stdout)

    def test_bad_tasks_dir_is_a_usage_error(self):
        r = self.run_cli("--tasks-dir", "/does/not/exist")
        self.assertNotEqual(r.returncode, 0)

    def test_finding_names_file_key_and_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "T-980-x.md").write_text(textwrap.dedent("""\
                ---
                id: T-980
                status: todo
                owner: someone
                risk: normal
                security_review: false
                depends_on: []
                pr:
                ---
                body
                """))
            (root / "TASKS.md").write_text(
                "\n".join([TABLE_HEADER, TABLE_SEP,
                           board_line("T-980", "x", "todo")]) + "\n")
            r = self.run_cli("--tasks-dir", str(root))
            self.assertEqual(r.returncode, 1)
            self.assertIn("T-980-x.md:", r.stdout)
            self.assertIn("[owner]", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
