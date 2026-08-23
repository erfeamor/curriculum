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

    def test_block_scalar_digit_before_sign_chomping_indicator_recognized(self):
        """YAML permits the chomping/indentation indicators in EITHER order
        (`|2-` and `|-2` are both legal -- confirmed against yaml.safe_load).
        The original _BLOCK_SCALAR_RE matched sign-before-digit only, so a
        `|2-` block scalar was never recognized as one and its prose content
        was walked as structure -- a FALSE duplicate-key finding between two
        lines of prose that happen to both start with the same word."""
        b = make_board(self.root)
        b.add_task("T-904", textwrap.dedent("""\
            id: T-904
            status: done
            owner: carlos
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              worktree: none
              notes: |2-
                status: fake
                status: fake2
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key == "status" for f in findings),
                          f"false positive: |2- block scalar not recognized, "
                          f"prose walked as structure: {[str(f) for f in findings]}")

    def test_block_scalar_digit_before_sign_chomping_indicator_on_folded_scalar(self):
        """Same bug, the `>` (folded) form with sign-before-digit reversed
        the other way (`>2+`)."""
        b = make_board(self.root)
        b.add_task("T-905", textwrap.dedent("""\
            id: T-905
            status: done
            owner: carlos
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              worktree: none
              notes: >2+
                owner: fake
                owner: fake2
            """), status="done")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.key == "owner" for f in findings),
                          f"false positive: >2+ block scalar not recognized: "
                          f"{[str(f) for f in findings]}")

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

    def test_real_duplicate_inside_a_single_sequence_item_is_still_caught(self):
        """Round 4 review, MEDIUM: only the "siblings legitimately repeat"
        NEGATIVE case was ever tested for sequences -- a real shadow
        INSIDE one list item (`- round: 1\\n  round: 2`, exactly the shape
        this board writes in checkpoint.review_trail-style lists) was
        never asserted to be caught. Deleting the SequenceNode recursion
        in _walk_compose_node would have survived every prior test."""
        b = make_board(self.root)
        b.add_task("T-906", textwrap.dedent("""\
            id: T-906
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
                  round: 2
                  finding: shadowed round
            """), status="done")
        b.write_board()
        findings = b.check()
        dup = [f for f in findings if f.key == "round"]
        self.assertEqual(len(dup), 1, f"duplicate inside a sequence item "
                                       f"was not caught: {[str(f) for f in findings]}")

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

    def _live_file(self, task_id: str) -> Path:
        """Locate by glob rather than a hardcoded filename -- a rename
        (this board's title suffixes DO change, e.g. T-017's did) must
        fail this test with a clear message, not silently stop testing
        the file the spec actually named."""
        matches = sorted(LIVE_TASKS_DIR.glob(f"{task_id}-*.md"))
        self.assertTrue(matches, f"no file matches {task_id}-*.md under "
                                  f"{LIVE_TASKS_DIR} -- renamed or removed?")
        return matches[0]

    def test_live_board_t002_and_t103_no_false_positive(self):
        """Assert directly against the real files named in the spec."""
        for task_id in ("T-002", "T-103"):
            path = self._live_file(task_id)
            fm = bc.read_frontmatter(path)
            self.assertIsNotNone(fm, f"{path.name}: no `---`-fenced "
                                      f"frontmatter found -- lost its fence?")
            findings = bc.find_duplicate_keys(fm[0], fm[1], path)
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
        """Uses bc.read_frontmatter -- the REAL fence detector, not a
        second, independent .strip()-based reimplementation of it. An
        inline `.strip()` copy here would carry the exact bug
        FrontmatterFenceTruncation exists to catch (an indented "---"
        inside a block scalar truncating the frontmatter early), silently
        analyzing a truncated mapping in these four real-file regression
        tests specifically -- the ones this round's escalation was ABOUT
        being faithful to the real artifact."""
        text = git_show(commit, relpath)
        name = relpath.rsplit("/", 1)[-1]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / name
            p.write_text(text)
            fm = bc.read_frontmatter(p)
            self.assertIsNotNone(fm, f"{relpath}@{commit}: no `---`-fenced "
                                      f"frontmatter found -- file renamed, "
                                      f"restructured, or the commit is stale")
            fm_lines, first_line, _ = fm
            return bc.find_duplicate_keys(fm_lines, first_line, Path(name))

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

        # Round 4 review, LOW: the two `worktree:` findings above were
        # only ever COUNTED, never LOCATED -- keeping the first-seen line
        # fixed (instead of advancing it to the newest, as the comment in
        # find_duplicate_keys/_walk_compose_node explicitly promises for a
        # third occurrence) would still produce a count of 2 and pass
        # every assertion before this one. The real, distinct lines: each
        # finding sits at the NEXT worktree: line and blames the one
        # immediately before it, not the original first at line 15.
        worktree_findings = sorted(by_key["worktree"], key=lambda f: f.line)
        self.assertEqual([f.line for f in worktree_findings], [19, 27])
        self.assertIn("first seen at line 15", worktree_findings[0].message)
        self.assertIn("first seen at line 19", worktree_findings[1].message)

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


class FrontmatterFenceTruncation(TempDirCase):
    """Review round 3, HIGH #1: `read_frontmatter` used `.strip()` (which
    also eats LEADING indentation) rather than `.rstrip()` to recognize the
    closing `---` fence, so an INDENTED `---` inside a block scalar (a
    markdown horizontal rule in hand-authored prose -- exactly what
    checkpoint.review_trail and checkpoint.enforcement_propagation are)
    truncated the frontmatter early. Everything after the fake fence,
    including the file's real problems, was invisible to checks 1/4/5."""

    def test_realistic_prose_block_with_indented_horizontal_rule(self):
        b = make_board(self.root)
        # A realistic review_trail: two rounds of findings separated by a
        # markdown horizontal rule, the way this board's own task files
        # actually write them -- plus a REAL defect (checkpoint.worktree
        # still set on a done task) positioned AFTER the fake fence, so a
        # truncation bug would hide it.
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
              review_trail: |
                Round 1 (2026-08-20): two findings, both fixed.

                ---

                Round 2 (2026-08-21): converged, zero blocking.
              worktree: /home/erfeamor/work/cvdl-worktrees/T-940
            """), status="done")
        b.write_board()
        findings = b.check()
        wt = [f for f in findings if f.key == "checkpoint.worktree"]
        self.assertTrue(wt, f"real defect after the fake '---' was hidden by "
                             f"truncation: {[str(f) for f in findings]}")

    def test_frontmatter_still_closes_at_the_real_fence(self):
        """The body (after the REAL closing ---) must not be mistaken for
        frontmatter either -- confirms the fix didn't just stop matching
        ANY '---', only indented ones."""
        b = make_board(self.root)
        b.add_task("T-941", textwrap.dedent("""\
            id: T-941
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="todo")
        p = b.dir / "T-941-x.md"
        p.write_text(p.read_text() + "\n## Not frontmatter\n\nstatus: this text is body prose, not YAML\n")
        b.write_board()
        findings = b.check()
        self.assertFalse(any(f.file.name == "T-941-x.md" and f.key == "status"
                              for f in findings),
                          f"body content after the real fence was parsed as "
                          f"frontmatter: {[str(f) for f in findings]}")


class YamlComposeSurfaceForms(unittest.TestCase):
    """Review round 3, design change (#11): check 1 is re-based on
    yaml.compose() -- now the ONLY implementation (round 4: the fallback
    scanner was deleted and PyYAML made a hard requirement, see the
    module docstring's Ruling section) -- closing three YAML surface
    forms a hand-rolled line scanner is structurally blind to: quoted
    keys, hyphenated keys, and flow mappings, all of which
    yaml.safe_load() shadows silently, same failure class as the four
    incidents check 1 exists to catch."""

    def test_quoted_key_duplicate_detected(self):
        fm = ['id: T-950', 'status: todo', '"status": in_progress']
        findings = bc.find_duplicate_keys(fm, 2, Path("x.md"))
        self.assertTrue(any(f.key == "status" for f in findings),
                         [str(f) for f in findings])

    def test_hyphenated_key_duplicate_detected(self):
        fm = ['id: T-951', 'review-round: 1', 'review-round: 2']
        findings = bc.find_duplicate_keys(fm, 2, Path("x.md"))
        self.assertTrue(any(f.key == "review-round" for f in findings),
                         [str(f) for f in findings])

    def test_flow_mapping_duplicate_detected(self):
        fm = ['id: T-952', 'checkpoint: {worktree: a, worktree: none}']
        findings = bc.find_duplicate_keys(fm, 2, Path("x.md"))
        self.assertTrue(any(f.key == "worktree" for f in findings),
                         [str(f) for f in findings])

    def test_malformed_yaml_reports_nothing_from_check_1(self):
        """compose() raising must not crash check 1 -- parse_frontmatter_dict's
        own yaml.safe_load call is what reports the parse error."""
        fm = ['id: T-953', 'depends_on: [T-001']
        findings = bc.find_duplicate_keys(fm, 2, Path("x.md"))
        self.assertEqual(findings, [])


class ComposeResolvedValueFalsePositives(unittest.TestCase):
    """Round 4 review, the reviewer's own findings: _walk_compose_node
    compared key_node.value (the raw scalar TEXT) rather than the
    resolved identity, so a bare `yes`/`1`/`~` and its QUOTED counterpart
    ("yes"/"1"/"~") -- which YAML resolves to bool/int/null vs string,
    two genuinely different keys, confirmed via yaml.safe_load producing
    {True: ..., 'yes': ...} etc, not a shadow at all -- were reported as
    a duplicate. Fixed by comparing (tag, value) instead of value alone."""

    def test_bool_resolved_key_vs_quoted_string_is_not_a_duplicate(self):
        fm = ['a:', '  yes: x', '  "yes": y']
        findings = bc.find_duplicate_keys(fm, 1, Path("x.md"))
        self.assertEqual(findings, [], [str(f) for f in findings])

    def test_int_resolved_key_vs_quoted_string_is_not_a_duplicate(self):
        fm = ['a:', '  1: x', '  "1": y']
        findings = bc.find_duplicate_keys(fm, 1, Path("x.md"))
        self.assertEqual(findings, [], [str(f) for f in findings])

    def test_null_resolved_key_vs_quoted_string_is_not_a_duplicate(self):
        fm = ['a:', '  ~: x', '  "~": y']
        findings = bc.find_duplicate_keys(fm, 1, Path("x.md"))
        self.assertEqual(findings, [], [str(f) for f in findings])

    def test_a_real_duplicate_of_the_same_resolved_type_is_still_caught(self):
        """The fix must not overcorrect into missing genuine duplicates
        that happen to share a resolved type."""
        fm = ['a:', '  status: x', '  status: y']
        findings = bc.find_duplicate_keys(fm, 1, Path("x.md"))
        self.assertEqual(len(findings), 1, [str(f) for f in findings])
        self.assertEqual(findings[0].key, "status")


class ComposeAliasDoubleReporting(unittest.TestCase):
    """Round 4 review, the reviewer's own finding: an alias to a mapping
    (`a: &x {...}` / `b: *x`) made _walk_compose_node visit the SAME node
    object twice (confirmed: compose() resolves an alias to the identical
    Python object as its anchor), double-reporting one real duplicate.
    De-duplicated by node id in a `visited` set, since that is exactly
    what makes two references to the SAME anchored mapping distinguishable
    from two independent, coincidentally-similar mappings (which must
    each still be walked and checked on their own)."""

    def test_alias_to_a_duplicate_bearing_mapping_reports_once_not_twice(self):
        fm = ['a: &x', '  worktree: p', '  worktree: q', 'b: *x']
        findings = bc.find_duplicate_keys(fm, 1, Path("x.md"))
        self.assertEqual(len(findings), 1, [str(f) for f in findings])

    def test_two_independent_mappings_are_each_still_checked(self):
        """Not de-duplicating by CONTENT -- two structurally identical but
        independently-written mappings are two different node objects and
        must each be checked for their own duplicates."""
        fm = ['a:', '  worktree: p', '  worktree: q',
              'b:', '  worktree: p', '  worktree: q']
        findings = bc.find_duplicate_keys(fm, 1, Path("x.md"))
        self.assertEqual(len(findings), 2, [str(f) for f in findings])


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


class BoardRowIdColumn(TempDirCase):
    """The LOW finding: a row's id comes from the header's ID column, not
    from wherever a [T-nnn] link first appears in the row."""

    def test_a_link_to_another_task_in_an_earlier_cell_does_not_misattribute(self):
        """Round 4 review, MEDIUM: with TABLE_HEADER, ID is column 0, so
        "first [T-nnn] link anywhere in the row" still lands on the
        correct cell by ACCIDENT (it's the first cell checked either way)
        -- reverting parse_board_rows to scan the whole row left this
        test green. Needs a header where ID is genuinely NOT first, and a
        row whose non-ID cell links a DIFFERENT task ahead of the real ID
        cell, to actually exercise the bug."""
        b = make_board(self.root)
        b.add_task("T-993", textwrap.dedent("""\
            id: T-993
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="todo", in_board=False)
        b.add_task("T-994", textwrap.dedent("""\
            id: T-994
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="todo", in_board=False)
        # Title BEFORE ID -- the shape "first [T-nnn] anywhere" misfires on.
        header = "| Title | ID | Repo | Status | Owner | Depends on | PR |"
        sep = "|-------|----|------|--------|-------|------------|----|"
        row = "| see also [T-993](T-993-x.md) | [T-994](T-994-x.md) | repo | todo | | | |"
        p = b.dir / "TASKS.md"
        p.write_text("\n".join([header, sep, row]) + "\n")
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


class NoFrontmatterFenceRegistration(TempDirCase):
    """Review round 3, MEDIUM #3: mirror of ParseFailureRegistration, but
    for the OTHER early-exit in run() -- a file with NO `---`-fenced
    frontmatter at all. That branch didn't register the task id either,
    so check 2 additionally (and falsely) reported "no task file" about a
    file that was just read successfully (its frontmatter block is simply
    absent/malformed, which is already its own finding)."""

    def test_no_frontmatter_fence_does_not_also_report_missing_file(self):
        b = make_board(self.root)
        (b.dir / "T-996-x.md").write_text("no frontmatter fence in this file at all\n")
        b.add_raw_board_row(board_line("T-996", "x", "todo"))
        b.write_board()
        findings = b.check()
        fence_errors = [f for f in findings if "no `---`-fenced" in f.message]
        self.assertTrue(fence_errors, "expected the no-fence finding")
        misdirected = [f for f in findings if "no task file" in f.message]
        self.assertEqual(misdirected, [], [str(f) for f in findings])


class IdCollision(TempDirCase):
    """Review round 3, MEDIUM #4: two files sharing a T-nnn id used to
    shadow each other via plain dict assignment in run() -- whichever file
    was processed LAST silently won every id-keyed check, and the LOSER's
    real defects were never validated at all. A FALSE GREEN, reproduced
    with a stale renamed file still carrying a checkpoint.worktree
    violation that check 4 never got a chance to see."""

    def test_collision_is_reported_and_the_shadowed_files_defect_still_surfaces(self):
        b = make_board(self.root)
        # "aaa" sorts first; under the OLD last-writer-wins code its defect
        # was silently overwritten by "zzz", which sorts last and is clean.
        b.add_task("T-901-aaa-stale", textwrap.dedent("""\
            id: T-901
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              worktree: /home/erfeamor/work/cvdl-worktrees/T-901
            """), status="done", in_board=False)
        b.add_task("T-901-zzz-current", textwrap.dedent("""\
            id: T-901
            status: done
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: https://example.invalid/pr/1
            checkpoint:
              stage: done
              worktree: none
            """), status="done", in_board=False)
        b.add_raw_board_row(board_line("T-901", "x", "done"))
        b.write_board()
        findings = b.check()
        collision = [f for f in findings if "is claimed by 2 task files" in f.message]
        self.assertTrue(collision, [str(f) for f in findings])
        worktree_defect = [f for f in findings if f.key == "checkpoint.worktree"]
        self.assertTrue(worktree_defect,
                         f"the shadowed file's real defect was still lost: "
                         f"{[str(f) for f in findings]}")



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
        """Round 4 review, MEDIUM: the dependency-target fixture was named
        'T-001x' -- filename 'T-001x-x.md' fails run()'s own
        `^T-\\d+-.+\\.md$` filter, so it never entered known_ids at all, and
        the loose `any("T-999" in m ...)` assertion was satisfied even by
        the UNSPLIT string 'T-001, T-999' (which literally contains
        'T-999' as a substring). Mutating _normalize_depends_on to skip
        comma-splitting entirely left this test green. Fixed: a
        filename the glob filter actually matches, plus an exact-match
        assertion that only a real split can satisfy."""
        b = make_board(self.root)
        b.add_task("T-997", textwrap.dedent("""\
            id: T-997
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: T-001, T-999
            pr:
            """), status="todo")
        b.add_task("T-001", textwrap.dedent("""\
            id: T-001
            status: todo
            owner:
            risk: normal
            security_review: false
            depends_on: []
            pr:
            """), status="todo", in_board=False)
        b.write_board()
        findings = b.check()
        dep_ids = sorted(
            m.split("names ", 1)[1].split(",", 1)[0].strip("'")
            for f in findings if f.key == "depends_on"
            for m in [f.message] if "names" in m)
        self.assertEqual(dep_ids, ["T-999"],
                          f"T-001 must resolve (real file, not flagged) and "
                          f"T-999 must not (no file): {[str(f) for f in findings]}")


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

    def test_one_row_per_file_fires_on_a_genuine_duplicate_row(self):
        """Round 4 review, MEDIUM: `if len(occurrences) > 1:` had only
        NEGATIVE coverage (every existing fixture puts a task in exactly
        one Status-bearing table) -- `if False:` survives unnoticed.
        Duplicate rows across two Status-bearing tables is one of the
        recurrences check 2 is explicitly named for."""
        b = make_board(self.root)
        b.add_task("T-920", self.base_fm(status="todo"), status="todo")
        b.write_board()
        # A SECOND Status-bearing table also naming T-920 -- a hand-edit
        # slip (copy-pasted into the wrong section) this board has made.
        extra = "\n\n" + TABLE_HEADER + "\n" + TABLE_SEP + "\n" + \
            board_line("T-920", "x (duplicated into a second table)", "todo") + "\n"
        p = b.dir / "TASKS.md"
        p.write_text(p.read_text() + extra)
        findings = b.check()
        dupes = [f for f in findings if "expected exactly one" in f.message]
        self.assertEqual(len(dupes), 1, [str(f) for f in findings])
        self.assertIn("2 rows in TASKS.md", dupes[0].message)

    def test_malformed_row_cell_count_mismatch_is_reported(self):
        """Round 4 review, MEDIUM: no fixture ever produced a row whose
        cell count disagrees with its header -- iterating an empty
        `malformed` list survives unnoticed. A stray or missing `|` is
        the common hand-edit slip on this board."""
        b = make_board(self.root)
        b.add_task("T-920", self.base_fm(status="todo"), status="todo", in_board=False)
        # One cell short of the 7-column header -- a dropped "|".
        bad_row = "| [T-920](T-920-x.md) | x | repo | todo | | |"
        (b.dir / "TASKS.md").write_text(
            "\n".join([TABLE_HEADER, TABLE_SEP, bad_row]) + "\n")
        findings = b.check()
        malformed = [f for f in findings
                     if "column count does not match" in f.message]
        self.assertEqual(len(malformed), 1, [str(f) for f in findings])

    def test_header_immediately_followed_by_a_data_row_no_separator(self):
        """Review round 3, LOW #7: `i += 2` unconditionally skipped a line
        after a recognized header, assuming it was always the `|---|---|`
        separator. A header with NO separator row (or a malformed one)
        swallowed the very next real row outright."""
        b = make_board(self.root)
        b.add_task("T-920", self.base_fm(status="in_review", owner="someone"),
                   status="in_review", in_board=False)
        # Header directly followed by a DATA row -- no separator line at all.
        board_text = (TABLE_HEADER + "\n" +
                      board_line("T-920", "x", "in_review") + "\n")
        (b.dir / "TASKS.md").write_text(board_text)
        findings = b.check()
        self.assertFalse(any("no row in any Status-bearing" in f.message
                              for f in findings),
                          f"the header-adjacent row was swallowed: "
                          f"{[str(f) for f in findings]}")



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

    def test_sentinel_message_does_not_claim_it_is_empty(self):
        """Review round 3, LOW #8: pr: is a SENTINEL (a truthy value, e.g.
        'none'), not an empty one -- the message must not say "is empty"
        about a value that plainly is not."""
        b = make_board(self.root)
        b.add_task("T-956", textwrap.dedent("""\
            id: T-956
            status: in_review
            owner: someone
            risk: normal
            security_review: false
            depends_on: []
            pr: none
            """), status="in_review")
        b.write_board()
        findings = b.check()
        pr_findings = [f for f in findings if f.key == "pr"]
        self.assertTrue(pr_findings)
        self.assertNotIn("is empty", pr_findings[0].message,
                          pr_findings[0].message)
        self.assertIn("sentinel", pr_findings[0].message)



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


class NestedLineOfDepth(unittest.TestCase):
    """Review round 3, LOW #10: `nested_line_of` matched a same-named key
    at ANY depth under `parent:`, not just the immediate child level -- a
    finding could cite a line whose value is not the one it complains
    about, and the PostToolUse hook feeds that wrong line to the model as
    the place to edit."""

    def test_only_the_direct_child_key_matches_not_a_deeper_one(self):
        fm = textwrap.dedent("""\
            id: T-930
            status: done
            checkpoint:
              stage: done
              pre_apply_gate:
                pr: https://example.invalid/deep-nested-not-the-real-one
              pr: https://example.invalid/real-checkpoint-pr
            """).split("\n")
        line = bc.nested_line_of(fm, 2, "checkpoint", "pr")
        self.assertEqual(line, 8, f"got line {line}, expected 8 (the direct "
                                   f"child), not 7 (the deeper one)")

    def test_still_finds_a_key_that_is_genuinely_the_direct_child(self):
        fm = textwrap.dedent("""\
            id: T-931
            checkpoint:
              worktree: none
            """).split("\n")
        line = bc.nested_line_of(fm, 2, "checkpoint", "worktree")
        self.assertEqual(line, 4)

    def test_absent_key_returns_none(self):
        fm = textwrap.dedent("""\
            id: T-932
            checkpoint:
              stage: done
            """).split("\n")
        self.assertIsNone(bc.nested_line_of(fm, 2, "checkpoint", "pr"))


class LineOfTopLevelOnly(unittest.TestCase):
    """Round 4 review, LOW: `line_of` used to take a `top_level_only=True`
    flag whose early-continue guard was never asserted -- deleting it
    survived. Investigating WHY turned up something the mutation-testing
    finding didn't say directly: the guard was not merely untested, it
    was PROVABLY REDUNDANT. `pattern.match(raw)` requires the match to
    start at column 0 of the raw (unstripped) line regardless of the
    flag -- `re.match(r'^status:', '  status: x')` is False -- so an
    indented line could never satisfy the pattern whether or not the
    guard ran, and no caller anywhere ever passed `top_level_only=False`.
    Fixed by deleting the (dead) parameter and its guard rather than
    padding a test around behavior that never existed; this test asserts
    the property the guard was WRITTEN for, which the simplified
    column-anchored regex still provides on its own -- the same harm
    NestedLineOfDepth exists to prevent (the PostToolUse hook hands the
    model whatever line this function returns as the place to edit)."""

    def test_a_nested_key_of_the_same_name_is_not_matched_at_top_level(self):
        fm = textwrap.dedent("""\
            id: T-933
            checkpoint:
              status: this is NOT the top-level status field
            status: todo
            """).split("\n")
        line = bc.line_of(fm, 2, "status")
        self.assertEqual(line, 5, f"got line {line}, expected 5 (the real "
                                   f"top-level status:), not the nested one")


if __name__ == "__main__":
    unittest.main(verbosity=2)
