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

Provenance for the two claims above, because the obvious local reference
disagrees with them (2026-08-23):

  The bundled skill at
  ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/
  skills/hook-development/SKILL.md asserts a "Settings Format (Direct)" for
  .claude/settings.json — hook events unwrapped at the top level, no `hooks`
  key, contrasted against a wrapped "Plugin hooks.json Format". That claim is
  WRONG for the installed Claude Code build. Checked against the ACTUAL
  schema, not the doc: `strings -n 6` on the installed CLI binary
  (~/.local/share/claude/versions/<ver>, a compiled executable — the extension
  .js bundles under ~/.vscode/extensions/anthropic.claude-code-*/ are not it)
  turns up the live Zod schema fragment
  `hooks:Xbe().optional().describe("Custom commands to run before/after tool
  executions")` sitting alongside sibling settings keys (`deniedMcpServers`,
  `worktree`, ...) — i.e. settings.json's schema HAS a top-level `hooks` field,
  same shape as a plugin's hooks.json. This repo's settings.json (and the
  hooks.json examples elsewhere on this machine) use the wrapped
  `{"hooks": {"PostToolUse": [...]}}` form accordingly.

  The same binary-strings search turned up a literal usage example embedded
  in the CLI's own help text: `{"PostToolUse": [{"matcher": "Edit|Write",
  "hooks": [{"type": "command", "command": "echo Done"}]}]}` — READ CAREFULLY,
  this example itself has NO OUTER "hooks" WRAPPER. Reconciled by context: the
  string is a fragment of a longer message describing the SHAPE of one
  event's array (`"PostToolUse": [...]`), not a complete settings.json
  document — it is consistent with the wrapped form once embedded under a
  top-level `"hooks"` key, not evidence for the unwrapped claim above.

  `${CLAUDE_PROJECT_DIR}` (as used in .claude/settings.json's command string)
  is confirmed real and harness-substituted, not env-var-only: the same
  strings dump shows the CLI doing a literal `.replaceAll("${CLAUDE_PROJECT_DIR}",
  ...)` on hook command strings before spawning them, and separately setting
  it as a real subprocess env var. Either form works on Linux; the
  `${...}` substitution form is used here because it is documented (same
  SKILL.md, for `${CLAUDE_PLUGIN_ROOT}`) as the portable one — PowerShell
  hosts do not expand a bare `$VAR`.

  Lesson for the next person who hits this: a bundled skill doc can be
  authoritative-sounding and wrong in a way that only shows up when the hook
  silently never fires. When a hook's shape is load-bearing, verify against
  `strings` on the installed binary (or `claude --debug`), not the doc.
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
