#!/usr/bin/env python3
"""
PostToolUse hook: run scripts/board-check.py after an Edit/Write that touches
`.claude/tasks/`, so frontmatter drift is caught in the same turn it is
written rather than at the next manual `test-all.sh` run.

Part of T-031's H1-ratified third enforcement point (checkpoint.h1_rulings
item (c)) — the meta repo has no CI, so scripts/test-all.sh is a MANUAL gate
here; all four of the most recent duplicate-key incidents were driver edits
that nobody happened to run it after.

Cost discipline (the reason this exists as a tiny standalone script rather
than inline shell in settings.json): this fires on EVERY Edit/Write in the
session, so the common case — a file outside .claude/tasks/ — must return
before doing any work at all. Only a touched .claude/tasks/*.md path pays
for a board-check run.

Wired as a PostToolUse hook because Edit/Write have already landed by the
time any hook can see them; there is nothing to block here, only to report.
Uses CC's modern hookSpecificOutput.additionalContext protocol (not the
legacy stderr+exit(2) shape), so a clean run is genuinely silent — no stdout,
no stderr, no JSON — matching the "cheap and non-blocking-on-success"
requirement literally.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MARKER = "/.claude/tasks/"


def main() -> int:
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0  # never break the session over a malformed hook payload

    tool_input = input_data.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if MARKER not in file_path.replace("\\", "/"):
        return 0  # the overwhelming common case — stay silent and cheap

    repo_root_str, _, _ = file_path.replace("\\", "/").partition(MARKER)
    repo_root = Path(repo_root_str)
    board_check = repo_root / "scripts" / "board-check.py"
    if not board_check.is_file():
        return 0  # unexpected layout — say nothing rather than guess

    try:
        proc = subprocess.run(
            [sys.executable, str(board_check), "--quiet"],
            cwd=str(repo_root), capture_output=True, text=True, timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError):
        return 0  # a hung/broken check must not hang or break the turn

    if proc.returncode == 0:
        return 0  # clean — genuinely silent, no output at all

    findings = proc.stdout.strip() or proc.stderr.strip()
    context = (
        "board-check found frontmatter drift introduced by this edit "
        "(scripts/board-check.py, T-031):\n"
        f"{findings}\n"
        "Fix the frontmatter directly (never reformat unrelated content) "
        "before treating this task's checkpoint write as done."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
