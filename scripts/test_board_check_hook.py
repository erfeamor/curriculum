#!/usr/bin/env python3
"""Tests for scripts/board-check-hook.py.

Run:  python3 -m unittest discover -s scripts -p 'test_*.py'
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "board-check-hook.py"
BOARD_CHECK = Path(__file__).resolve().parent / "board-check.py"
REPO_ROOT = Path(__file__).resolve().parent.parent

TABLE_HEADER = "| ID | Title | Repo | Status | Owner | Depends on | PR |"
TABLE_SEP = "|----|-------|------|--------|-------|------------|----|"


def run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=str(REPO_ROOT), timeout=20)


class ExitCodeTwoIsNotDrift(unittest.TestCase):
    """Review round 3, MEDIUM #5: the hook treated board-check's exit 2
    (a READ failure -- permissions, encoding, a file vanishing between
    glob() and read_text()) the same as exit 1 (real findings), so the
    model-visible message said "board-check found frontmatter drift
    introduced by this edit" about a file it never actually managed to
    check at all."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / ".claude" / "tasks").mkdir(parents=True)
        (self.root / "scripts" / "board-check.py").write_text(
            BOARD_CHECK.read_text())
        task = self.root / ".claude" / "tasks" / "T-998-x.md"
        task.write_text(textwrap.dedent("""\
            ---
            id: T-998
            status: todo
            ---
            body
            """))
        (self.root / ".claude" / "tasks" / "TASKS.md").write_text(
            "\n".join([TABLE_HEADER, TABLE_SEP,
                       "| [T-998](T-998-x.md) | x | repo | todo | | | |"]) + "\n")
        self._task_path = task

    def test_unreadable_file_is_reported_as_a_read_failure_not_drift(self):
        if os.name != "posix":
            self.skipTest("chmod-based unreadable-file test is POSIX-only")
        self._task_path.chmod(0o000)
        self.addCleanup(lambda: self._task_path.chmod(0o644))
        if os.access(self._task_path, os.R_OK):
            self.skipTest("running as a user that ignores file permissions (e.g. root)")

        payload = {"tool_name": "Edit",
                   "tool_input": {"file_path": str(self._task_path)}}
        result = run_hook(payload)
        self.assertEqual(result.returncode, 0)  # the hook itself never fails the turn
        out = json.loads(result.stdout)
        context = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("could not run", context)
        self.assertIn("NOT a claim that this edit introduced drift", context)
        self.assertNotIn("found frontmatter drift introduced by this edit", context)


if __name__ == "__main__":
    unittest.main(verbosity=2)
