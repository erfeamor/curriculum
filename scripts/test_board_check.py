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
import os
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


def git_show(commit: str, relpath: str) -> str:
    """The exact historical content of a tracked file, straight from git —
    not a hand-built approximation of it. The PO's escalation exists because
    a hand-built T-152 fixture used indent-2 dashes while the real file's
    lists (h1_rulings:, reviewers:, etc.) all indent to 4; the approximation
    passed while the artifact it was supposed to stand in for was never
    actually run through the checker."""
    proc = subprocess.run(
        ["git", "show", f"{commit}:{relpath}"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, check=True)
    return proc.stdout


class RealHistoricalIncidents(unittest.TestCase):
    """Check 1 against the ACTUAL commits, not reconstructions of them.
    Each commit below is the last one carrying the bug, verified by hand
    with `git show <commit>:<path> | grep -n <key>` before being pinned
    here — see the task report for the transcript."""

    def duplicates_in(self, commit: str, relpath: str):
        text = git_show(commit, relpath)
        lines = text.split("\n")
        assert lines[0].strip() == "---", "not a frontmatter-fenced file"
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
        fm_lines, first_line = lines[1:end], 2
        return bc.find_duplicate_keys(fm_lines, first_line,
                                       Path(relpath.rsplit("/", 1)[-1]))

    def test_t152_real_triple_worktree_and_shadowed_pr(self):
        """dd7bfe7: T-152 as merged, before the 05387a5 sweep demoted the
        shadowing keys. Three `worktree:` + a second, empty `pr:` under
        checkpoint: — the close-out's clearing of worktree was inert and the
        merged PR URL was shadowed by a blank, and nothing complained until
        this incident was found by hand."""
        findings = self.duplicates_in(
            "dd7bfe7", ".claude/tasks/T-152-mysql-84-parity-cv-database.md")
        by_key = {}
        for f in findings:
            by_key.setdefault(f.key, []).append(f)
        self.assertEqual(len(by_key.get("worktree", [])), 2,
                          "3 worktree: keys -> 2 shadow findings (2nd shadows "
                          f"1st, 3rd shadows 2nd): {[str(f) for f in findings]}")
        self.assertEqual(len(by_key.get("pr", [])), 1,
                          [str(f) for f in findings])
        self.assertIn("first seen at line 17", by_key["pr"][0].message)

    def test_t202_real_second_security_review(self):
        """05387a5^ (the sweep's parent): T-202 carrying a THIRD vocabulary
        for security_review ('done'), shadowing the boolean the 2026-08-17
        sweep had already normalized the rest of the board to."""
        findings = self.duplicates_in(
            "05387a5^", ".claude/tasks/T-202-bff-public-routing-and-auth.md")
        dup = [f for f in findings if f.key == "security_review"]
        self.assertEqual(len(dup), 1, [str(f) for f in findings])
        self.assertIn("first seen at line 21", dup[0].message)

    def test_t104_real_review_round_shadowing(self):
        """51bc931^ (the fix commit's parent): T-104's review_round: 0
        reintroduced BY THE DRIVER hours after sweeping for this exact bug —
        the incident that got this whole validator filed."""
        findings = self.duplicates_in(
            "51bc931^", ".claude/tasks/T-104-project-resource.md")
        dup = [f for f in findings if f.key == "review_round"]
        self.assertEqual(len(dup), 1, [str(f) for f in findings])
        self.assertIn("first seen at line 20", dup[0].message)

    def test_t151_real_review_round_shadowing(self):
        """Same incident, same commit, the sibling file (T-104 and T-151
        were shadowed the same way in the same sweep)."""
        findings = self.duplicates_in(
            "51bc931^", ".claude/tasks/T-151-dev-seeds-cv-sections.md")
        dup = [f for f in findings if f.key == "review_round"]
        self.assertEqual(len(dup), 1, [str(f) for f in findings])
        self.assertIn("first seen at line 17", dup[0].message)


class CompactSequences(TempDirCase):
    """The HIGH finding: a compact-style sequence (dash at the SAME column
    as its sibling keys, e.g. `depends_on:\n- T-001`) must not destroy the
    key registry of the mapping that owns it. Every existing fixture before
    this used INDENTED (`  - `) sequences, which never exposed the bug —
    matching this board's own real lists, all of which happen to indent."""

    def test_compact_sequence_at_top_level_does_not_hide_a_straddling_duplicate(self):
        b = make_board(self.root)
        b.add_task("T-990", textwrap.dedent("""            id: T-990
            status: todo
            depends_on:
            - T-001
            - T-002
            status: in_progress
            owner: someone
            risk: normal
            security_review: false
            pr:
            """), status="in_progress")
        b.write_board()
        findings = b.check()
        dup = [f for f in findings if f.key == "status"]
        self.assertEqual(len(dup), 1,
                          f"compact sequence ate the parent scope: {[str(f) for f in findings]}")

    def test_compact_sequence_inside_checkpoint_does_not_hide_a_straddling_duplicate(self):
        b = make_board(self.root)
        b.add_task("T-991", textwrap.dedent("""            id: T-991
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              blockers:
              - none currently
              stage: pr
              worktree: none
            """), status="done")
        b.write_board()
        findings = b.check()
        dup = [f for f in findings if f.key == "stage"]
        self.assertEqual(len(dup), 1,
                          f"compact sequence ate checkpoint's scope: {[str(f) for f in findings]}")

    def test_compact_sequence_still_avoids_the_sibling_item_false_positive(self):
        """The fix must not regress the OTHER direction: sibling compact
        items still legitimately repeat keys without being flagged."""
        b = make_board(self.root)
        b.add_task("T-992", textwrap.dedent("""            id: T-992
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
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key in ("round", "finding") for f in findings),
                          f"false positive on compact sequence items: {[str(f) for f in findings]}")


class FallbackParserWithoutYAML(unittest.TestCase):
    """The MEDIUM finding: without PyYAML, security_review: true/false must
    coerce to real booleans, not the strings 'true'/'false' — otherwise
    check 7 fails isinstance(sr, bool) for every task that has one."""

    def test_true_false_coerce_to_bool(self):
        # Exercise the coercion function directly so this test doesn't
        # depend on whether PyYAML happens to be installed on the machine
        # running it -- parse_frontmatter_dict dispatches on _HAVE_YAML,
        # captured at import time.
        self.assertIs(bc._coerce_fallback_scalar("true"), True)
        self.assertIs(bc._coerce_fallback_scalar("false"), False)
        self.assertIs(bc._coerce_fallback_scalar("TRUE"), True)
        self.assertIsNone(bc._coerce_fallback_scalar(""))

    def test_non_boolean_vocabulary_still_fails_the_check(self):
        # 'required' was a real historical value for this key (2026-08-17
        # sweep) — coercion must not swallow it into looking valid.
        self.assertEqual(bc._coerce_fallback_scalar("required"), "required")

    def test_fallback_produces_no_false_positives_on_the_live_board(self):
        """End-to-end: force the no-PyYAML code path and confirm the live
        board's real security_review values (all true/false) don't trip
        check 7 the way they did before the coercion fix."""
        had_yaml = bc._HAVE_YAML
        bc._HAVE_YAML = False
        try:
            findings = bc.run(LIVE_TASKS_DIR)
        finally:
            bc._HAVE_YAML = had_yaml
        bool_coercion_findings = [
            f for f in findings
            if f.key == "security_review" and "not a real boolean" in f.message]
        self.assertEqual(bool_coercion_findings, [],
                          f"fallback parser still misreads true/false: "
                          f"{[str(f) for f in bool_coercion_findings]}")


class BoardRowIdColumn(TempDirCase):
    """The LOW finding: a row's id comes from the header's ID column, not
    from wherever a [T-nnn] link first appears in the row."""

    def test_a_link_to_another_task_in_an_earlier_cell_does_not_misattribute(self):
        b = make_board(self.root)
        b.add_task("T-993", textwrap.dedent("""            id: T-993
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="todo", in_board=False)
        b.add_task("T-994", textwrap.dedent("""            id: T-994
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="todo", in_board=False)
        b.write_board()
        # Hand-write a row whose Title cell links T-993 BEFORE the row's own
        # ID cell resolves to T-994 -- the shape that misfired under
        # "first [T-nnn] anywhere in the row".
        row = "| [T-994](T-994-x.md) | see also [T-993](T-993-x.md) | repo | todo | | | |"
        p = b.dir / "TASKS.md"
        p.write_text("\n".join([TABLE_HEADER, TABLE_SEP, row]) + "\n")
        findings = b.check()
        wrong = [f for f in findings
                 if "TASKS.md row names T-993" in f.message]
        self.assertEqual(wrong, [], [str(f) for f in findings])
        missing_994 = [f for f in findings
                        if "T-994" in f.message and "no row" in f.message]
        self.assertEqual(missing_994, [], [str(f) for f in findings])


class ParseFailureRegistration(TempDirCase):
    """The LOW finding: a frontmatter parse failure must not ALSO make
    check 2 claim the file doesn't exist (or that the board row is an
    orphan) — that's a second, misdirected finding on top of the real one."""

    def test_unparseable_frontmatter_does_not_also_report_missing_file(self):
        b = make_board(self.root)
        # Invalid YAML: an unclosed flow sequence.
        b.add_task("T-995", "id: T-995\nstatus: todo\ndepends_on: [T-001\n",
                   status="todo")
        b.write_board()
        findings = b.check()
        parse_errors = [f for f in findings if f.key is None and "error" in f.message.lower()]
        self.assertTrue(parse_errors, "expected a parse-error finding")
        misdirected = [f for f in findings if "no task file" in f.message
                        or "no row in any Status-bearing" in f.message]
        self.assertEqual(misdirected, [], [str(f) for f in findings])


class DependsOnScalarForm(TempDirCase):
    """The LOW finding: depends_on as a bare scalar or a comma-separated
    string is hand-editable YAML too, and was silently never validated."""

    def test_bare_scalar_depends_on_is_validated(self):
        b = make_board(self.root)
        b.add_task("T-996", textwrap.dedent("""            id: T-996
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: T-999
            pr:
            """), status="todo")
        b.write_board()
        findings = b.check()
        self.assertTrue(any(f.key == "depends_on" and "T-999" in f.message
                             for f in findings), [str(f) for f in findings])

    def test_comma_separated_depends_on_is_validated(self):
        b = make_board(self.root)
        b.add_task("T-997", textwrap.dedent("""            id: T-997
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: T-001, T-999
            pr:
            """), status="todo")
        b.add_task("T-001x", "id: T-001x\nstatus: todo\nowner:\nrisk: normal\n"
                              "security_review: false\ndepends_on: []\npr:\n",
                   status="todo", in_board=False)
        b.write_board()
        findings = b.check()
        names = [f.message for f in findings if f.key == "depends_on"]
        self.assertTrue(any("T-999" in m for m in names), names)


class ReadFailureExitCode(unittest.TestCase):
    """The LOW finding: a board that cannot be READ (not a single malformed
    file, but an I/O failure) must exit 2, per the tool's own documented
    contract -- not leak a traceback that a caller (test-all.sh, the
    PostToolUse hook) misreads as ordinary content drift."""

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT))

    def test_unreadable_task_file_exits_2_not_1_and_no_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "T-998-x.md"
            bad.write_text("---\nid: T-998\nstatus: todo\n---\nbody\n")
            (root / "TASKS.md").write_text(
                "\n".join([TABLE_HEADER, TABLE_SEP,
                           board_line("T-998", "x", "todo")]) + "\n")
            bad.chmod(0o000)
            try:
                if os.access(bad, os.R_OK):
                    self.skipTest("running as a user that ignores file permissions (e.g. root)")
                r = self.run_cli("--tasks-dir", str(root))
            finally:
                bad.chmod(0o644)
            self.assertEqual(r.returncode, 2, f"stdout={r.stdout!r} stderr={r.stderr!r}")
            self.assertNotIn("Traceback", r.stderr)
            self.assertIn("could not read the board", r.stderr)


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
