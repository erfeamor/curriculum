#!/usr/bin/env python3
"""
board-check — a read-only validator over the task board (.claude/tasks/).

Part of the /dev-loop pipeline (T-031). The board is hand-edited YAML
frontmatter plus a hand-edited markdown index, and every consistency property
it depends on has so far been enforced by people remembering — which the
board's own history records failing repeatedly, including on the same day the
failure was written down (see .claude/tasks/T-031-board-frontmatter-validator.md
for the twelve recorded incidents this tool exists to catch).

Seven checks, each mapped to a real incident:
  1. Duplicate keys within a frontmatter mapping (T-152, T-202, T-104/T-151).
  2. Board row <-> file agreement: one row per file, status matches (T-002,
     T-019, three recurrences).
  3. status/owner coherence (todo => no owner; in_progress/in_review/done =>
     owner present).
  4. checkpoint.worktree cleared on closed (done) tasks (T-101, T-102).
  5. pr: present on in_review/done, consistent with checkpoint.pr (T-011,
     T-009, T-019).
  6. depends_on resolves to a real task file.
  7. Controlled vocabularies: status, security_review, risk.

Ruling (binding, from H1 — see the task file's checkpoint.h1_rulings):
  - Check 1 operates on RAW LINES, never on a parsed YAML tree.
    `yaml.safe_load` silently accepts duplicate keys and returns the LAST —
    exactly the behaviour that made all four shadowing incidents invisible.
  - Read-only, always. Nothing here reformats, reorders or rewrites
    frontmatter; the board's strike-don't-delete convention means these files
    carry DELIBERATE contradictions that a formatter would destroy.
  - Two exemptions are binding, not oversights: T-201/T-301/T-401/T-402/T-501
    carry no risk/security_review (2026-08-17 sweep, deliberate — see below),
    and acceptance-checkbox state is never enforced (2026-08-20 sweep ruled it
    convention).
  - Does not parse the body. Prose drift is what sweeps are for.

Usage:
    scripts/board-check.py                  # check the live board, exit 0/1
    scripts/board-check.py --tasks-dir DIR  # check a different board (tests)
    scripts/board-check.py --quiet          # print findings only, no summary

Exit codes: 0 = clean, 1 = at least one finding, 2 = the board itself could
not be read (I/O error, not a single file) or a check failed at import
time — a false GREEN here is worse than a crash, so this deliberately does
not swallow that class of error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / ".claude" / "tasks"

# Controlled vocabularies (check 7).
STATUS_VALUES = {"todo", "in_progress", "in_review", "done", "blocked"}
RISK_VALUES = {"trivial", "low", "normal", "high"}

# 2026-08-17 sweep ruling, binding per H1: assigning risk/security_review to
# an unrefined task would "manufacture ratified-looking decisions nobody
# made". These five carry neither key, on purpose. Do not invent values for
# them and do not warn on their absence.
UNREFINED_EXEMPT = {"T-201", "T-301", "T-401", "T-402", "T-501"}

# Sentinel values meaning "deliberately absent", shared with
# qa-env-override.py's _NO_WORKTREE set for checkpoint.worktree (check 4).
_NONE_SENTINELS = {"none", "null", "n/a", "-", ""}

# `pr:` sentinel accepted ONLY on a `done` task (never `in_review`, where a PR
# is definitionally open) — see check 5 for the live case this covers (T-010:
# the work shipped entirely through other tasks' PRs, recorded in a comment
# the day the key was added). Kept narrow: a task can say "no PR exists and
# that is correct" the same way checkpoint.worktree already does, but cannot
# use it to dodge review while a PR really is open.
_PR_NONE_SENTINELS = {"none", "n/a", "-"}


class Finding:
    __slots__ = ("file", "line", "key", "message")

    def __init__(self, file: Path, line, key, message: str):
        self.file = file
        self.line = line
        self.key = key
        self.message = message

    def __str__(self) -> str:
        loc = f"{self.file.name}:{self.line}" if self.line else self.file.name
        key = f" [{self.key}]" if self.key else ""
        return f"{loc}{key}: {self.message}"


# --------------------------------------------------------------------------
# Frontmatter splitting — shared by every check. Returns (lines, first_line,
# last_line) where lines are the RAW frontmatter lines (no `---` fences) and
# first_line/last_line are 1-based file line numbers of the fence markers,
# so every finding can report a real file line.
# --------------------------------------------------------------------------

def read_frontmatter(path: Path):
    text = path.read_text()
    raw_lines = text.split("\n")
    if not raw_lines or raw_lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(raw_lines)):
        if raw_lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    return raw_lines[1:end], 2, end  # frontmatter body starts at file line 2


# --------------------------------------------------------------------------
# Check 1 — duplicate keys within a frontmatter mapping, on raw lines.
#
# Deliberately hand-rolled rather than delegated to any YAML parser: PyYAML's
# safe_load accepts duplicate mapping keys and returns the last one, which is
# exactly the failure mode of all four incidents this check exists to catch
# (T-152's triple `worktree:`, T-202's second `security_review:`, T-104 and
# T-151's `review_round` shadowing).
#
# Correctness constraint (verified against the live board, T-002 and T-103):
# a naive "count keys at this indent" scan produces two DISTINCT classes of
# false positive that a mapping-scope-aware scan must both avoid —
#   (a) literal YAML block-sequence items ("- key: value" siblings), where
#       the same key legitimately repeats once per list item; and
#   (b) sibling nested mappings under different parent keys that happen to
#       share a child key name at the same indent (T-002's `pre_apply_gate:`
#       / `apply:` / `post_apply:` each carry their own `evidence:`, `run:`,
#       `commit:` — three distinct rounds, not one mapping with duplicates).
# Both are handled by tracking mapping SCOPES on a stack, keyed by indent,
# and starting a fresh (empty) scope every time indentation dedents past the
# scope that owned it — rather than a flat per-indent-level counter.
# --------------------------------------------------------------------------

_KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):(\s|$)')
_DASH_RE = re.compile(r'^(-)(\s+(.*))?$')
_BLOCK_SCALAR_RE = re.compile(r':\s*[|>][+-]?\d*\s*(#.*)?$')


class _Scope:
    __slots__ = ("indent", "keys")

    def __init__(self, indent: int):
        self.indent = indent
        self.keys: dict[str, int] = {}


def find_duplicate_keys(fm_lines: list[str], first_file_line: int, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    stack: list[_Scope] = [_Scope(-1)]  # sentinel root scope, indent -1
    skip_until_indent = None  # active block-scalar: exit when indent <= this

    for offset, raw in enumerate(fm_lines):
        file_line = first_file_line + offset
        if raw.strip() == "":
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        content = raw.strip()

        if skip_until_indent is not None:
            if indent > skip_until_indent:
                continue  # still inside the block scalar's content
            skip_until_indent = None
            # fall through: this line is structural again

        if content.startswith("#"):
            continue

        # A sequence item ("- " or bare "-") starts a brand-new mapping scope
        # for that item, regardless of whether a scope already exists at this
        # indent — that is precisely what makes repeated keys across sibling
        # list items legitimate rather than duplicates.
        dm = _DASH_RE.match(content)
        if dm:
            # Pop only scopes STRICTLY deeper than this dash (a previous
            # sibling list item's own scope, or anything nested further in).
            # A "> indent" (not ">= indent") pop is load-bearing: a COMPACT
            # sequence puts its dash at the SAME column as its sibling keys
            # (`depends_on:\n- T-001\n- T-002\nstatus: done`), and the scope
            # that owns that sequence sits at that identical indent. Popping
            # on ">=" destroyed that owning scope's key registry the moment
            # the first dash was seen, so a duplicate `status:` before an
            # `- `-prefixed compact list went undetected — a silent
            # false-negative in the highest-value check. Verified against the
            # real historical T-152 (dd7bfe7), whose `h1_rulings:`-style
            # lists are all indented, not compact, so that file was never
            # exposed to this bug; a compact list anywhere in the board would
            # have been.
            while len(stack) > 1 and stack[-1].indent > indent:
                stack.pop()
            rest = dm.group(3) or ""
            if not rest:
                continue  # bare "-": nested content follows, handled below
            item_col = indent + (len(content) - len(rest))
            km = _KEY_RE.match(rest)
            if not km:
                continue  # a scalar/quoted list item — no key to track
            key = km.group(1)
            scope = _Scope(item_col)
            stack.append(scope)
            scope.keys[key] = file_line
            if _BLOCK_SCALAR_RE.search(raw):
                skip_until_indent = item_col
            continue

        km = _KEY_RE.match(content)
        if not km:
            continue  # not a recognizable "key:" line — leave it alone
        key = km.group(1)

        while len(stack) > 1 and stack[-1].indent > indent:
            stack.pop()

        if stack[-1].indent == indent:
            scope = stack[-1]
        else:
            scope = _Scope(indent)
            stack.append(scope)

        if key in scope.keys:
            findings.append(Finding(
                path, file_line, key,
                f"duplicate key {key!r} in the same mapping — first seen at "
                f"line {scope.keys[key]}. YAML keeps the LAST occurrence, so "
                f"the value at line {scope.keys[key]} is silently shadowed."))
            # Keep tracking the newest line so a THIRD occurrence (T-152's
            # shape: three `worktree:` keys) reports each shadow in turn.
            scope.keys[key] = file_line
        else:
            scope.keys[key] = file_line

        if _BLOCK_SCALAR_RE.search(raw):
            skip_until_indent = indent

    return findings


# --------------------------------------------------------------------------
# A small, deliberately narrow frontmatter reader for checks 3-7. Delegates
# to PyYAML when available (parsing everything BUT duplicate keys is not the
# load-bearing part of this tool), and falls back to a minimal top-level
# scanner if PyYAML is absent, so this tool has no hard external dependency.
# --------------------------------------------------------------------------

try:
    import yaml
    _HAVE_YAML = True
except ModuleNotFoundError:
    _HAVE_YAML = False


def parse_frontmatter_dict(fm_lines: list[str], path: Path):
    """Best-effort dict of the frontmatter, for checks 2-7 only. Never used
    for check 1 (duplicate keys), which must see raw lines regardless of
    what parses the rest — see the ruling above find_duplicate_keys."""
    text = "\n".join(fm_lines)
    if _HAVE_YAML:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            return None, f"YAML parse error: {exc}"
        return (data if isinstance(data, dict) else {}), None
    # Minimal fallback: only top-level `key: value` lines, no nesting. Good
    # enough for checks 3/5/6/7 (all top-level); check 4 needs
    # checkpoint.worktree and degrades to "not checked" without PyYAML.
    data = {}
    for line in fm_lines:
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$', line)
        if m and not line.startswith((" ", "\t")):
            key = m.group(1)
            raw_val = m.group(2).split("#", 1)[0].strip()
            data[key] = _coerce_fallback_scalar(raw_val)
    return data, None


def _coerce_fallback_scalar(raw: str):
    """PyYAML resolves an unquoted `true`/`false` scalar to a real bool;
    this fallback parser must do the same for exactly those two spellings —
    the board's own vocabulary for `security_review` — or every boolean
    field reads as the STRING 'true'/'false' and check 7's
    `isinstance(sr, bool)` fails for every task that has one. That produced
    49 false findings on the clean live board with PyYAML absent: the
    validator itself becoming the noise it exists to prevent. Deliberately
    narrow (not PyYAML's full yes/no/on/off resolver) — this board writes
    only `true`/`false`, and a wider net risks silently coercing a real
    string value (a task id, a URL) that happens to spell "on" or "off"."""
    if raw == "":
        return None
    stripped = raw.strip("'\"")
    low = stripped.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    return stripped


def line_of(fm_lines: list[str], first_file_line: int, key: str, top_level_only=True) -> int | None:
    """First file line where `key:` appears at column 0 (top-level)."""
    pattern = re.compile(rf'^{re.escape(key)}:')
    for offset, raw in enumerate(fm_lines):
        if top_level_only and (raw.startswith(" ") or raw.startswith("\t")):
            continue
        if pattern.match(raw):
            return first_file_line + offset
    return None


def nested_line_of(fm_lines: list[str], first_file_line: int, parent: str, key: str) -> int | None:
    """First file line of `key:` nested directly under a top-level `parent:`
    block (one level of indent search — good enough for checkpoint.*)."""
    in_parent = False
    parent_indent = None
    for offset, raw in enumerate(fm_lines):
        if not in_parent:
            if re.match(rf'^{re.escape(parent)}:', raw):
                in_parent = True
                parent_indent = 0
            continue
        if raw.strip() == "":
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent <= parent_indent:
            break
        if re.match(rf'^{re.escape(key)}:', raw.strip()):
            return first_file_line + offset
    return None


# --------------------------------------------------------------------------
# Checks 3, 4, 5, 6, 7 — operate on the parsed frontmatter dict.
# --------------------------------------------------------------------------

def check_status_owner_coherence(data: dict, fm_lines, first_line, path: Path) -> list[Finding]:
    findings = []
    status = data.get("status")
    owner = data.get("owner")
    if status == "todo" and owner:
        findings.append(Finding(
            path, line_of(fm_lines, first_line, "owner"), "owner",
            f"status is 'todo' but owner is set to {owner!r} — a todo task "
            f"must be unowned and free to claim."))
    elif status in ("in_progress", "in_review", "done") and not owner:
        findings.append(Finding(
            path, line_of(fm_lines, first_line, "status"), "owner",
            f"status is {status!r} but owner: is empty — {status!r} requires "
            f"an owner."))
    return findings


def check_worktree_cleared(data: dict, fm_lines, first_line, path: Path) -> list[Finding]:
    findings = []
    status = data.get("status")
    if status != "done":
        return findings
    checkpoint = data.get("checkpoint")
    if not isinstance(checkpoint, dict):
        return findings
    wt = checkpoint.get("worktree")
    if wt is None:
        return findings
    text = str(wt).strip()
    if text.lower() not in _NONE_SENTINELS:
        findings.append(Finding(
            path, nested_line_of(fm_lines, first_line, "checkpoint", "worktree"),
            "checkpoint.worktree",
            f"task is done but checkpoint.worktree still declares {text!r} — "
            f"scripts/qa-env-override.py will refuse this task (T-028's rule). "
            f"Clear it to 'none' at close-out."))
    return findings


def check_pr_present(data: dict, fm_lines, first_line, path: Path) -> list[Finding]:
    findings = []
    status = data.get("status")
    if status not in ("in_review", "done"):
        return findings
    pr = data.get("pr")
    pr_text = str(pr).strip() if pr is not None else ""
    is_sentinel = pr_text.lower() in _PR_NONE_SENTINELS and pr_text != ""
    checkpoint = data.get("checkpoint")
    cp_pr = checkpoint.get("pr") if isinstance(checkpoint, dict) else None
    cp_pr_text = str(cp_pr).strip() if cp_pr else ""

    if pr_text == "" or is_sentinel:
        if status == "done" and is_sentinel:
            return findings  # explicit, recognized "no PR exists" sentinel
        hint = (f" (checkpoint.pr holds {cp_pr_text!r} — board rule 6 says "
                 f"the top-level key is what the board and driver read)"
                 if cp_pr_text else "")
        if is_sentinel:
            hint = (f" — the {pr_text!r} sentinel is only valid on a `done` "
                     f"task; {status!r} means a PR is definitionally open.")
        findings.append(Finding(
            path, line_of(fm_lines, first_line, "pr"), "pr",
            f"status is {status!r} but top-level pr: is empty{hint}."))
        return findings

    if cp_pr_text and cp_pr_text != pr_text:
        findings.append(Finding(
            path, nested_line_of(fm_lines, first_line, "checkpoint", "pr"),
            "checkpoint.pr",
            f"checkpoint.pr ({cp_pr_text!r}) disagrees with top-level pr: "
            f"({pr_text!r})."))
    return findings


def _normalize_depends_on(raw) -> list[str]:
    """A real YAML list (`depends_on: [T-101, T-102]`) is this board's
    convention and the common case, but `depends_on:` is hand-edited — a
    bare scalar (`depends_on: T-016`) or a comma-separated string
    (`depends_on: T-016, T-018`) both parse validly under YAML as a single
    string, and check_depends_on silently no-op'd on anything that wasn't
    already a Python list, so a scalar depends_on was never validated at
    all. Handled explicitly rather than assumed away."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(d).strip() for d in raw if str(d).strip()]
    return [d.strip() for d in str(raw).split(",") if d.strip()]


def check_depends_on(data: dict, fm_lines, first_line, path: Path, known_ids: set) -> list[Finding]:
    findings = []
    deps = _normalize_depends_on(data.get("depends_on"))
    if not deps:
        return findings
    dep_line = line_of(fm_lines, first_line, "depends_on")
    for dep_id in deps:
        if dep_id not in known_ids:
            findings.append(Finding(
                path, dep_line, "depends_on",
                f"depends_on names {dep_id!r}, which has no task file."))
    return findings


def check_vocabularies(data: dict, fm_lines, first_line, path: Path, task_id: str) -> list[Finding]:
    findings = []
    status = data.get("status")
    if status not in STATUS_VALUES:
        findings.append(Finding(
            path, line_of(fm_lines, first_line, "status"), "status",
            f"status {status!r} is not one of {sorted(STATUS_VALUES)}."))

    exempt = task_id in UNREFINED_EXEMPT

    if "security_review" in data or not exempt:
        sr = data.get("security_review")
        if sr is None and not exempt:
            findings.append(Finding(
                path, line_of(fm_lines, first_line, "status"), "security_review",
                f"security_review is missing (task is not in the "
                f"deliberately-unrefined exemption {sorted(UNREFINED_EXEMPT)})."))
        elif sr is not None and not isinstance(sr, bool):
            findings.append(Finding(
                path, line_of(fm_lines, first_line, "security_review"),
                "security_review",
                f"security_review={sr!r} is not a real boolean — this board "
                f"has previously carried 'required' and duplicate booleans "
                f"as separate vocabularies for the same key."))

    if "risk" in data or not exempt:
        risk = data.get("risk")
        if risk is None and not exempt:
            findings.append(Finding(
                path, line_of(fm_lines, first_line, "status"), "risk",
                f"risk is missing (task is not in the deliberately-unrefined "
                f"exemption {sorted(UNREFINED_EXEMPT)})."))
        elif risk is not None and str(risk) not in RISK_VALUES:
            findings.append(Finding(
                path, line_of(fm_lines, first_line, "risk"), "risk",
                f"risk {risk!r} is not one of {sorted(RISK_VALUES)}."))
    return findings


# --------------------------------------------------------------------------
# Check 2 — board row <-> file agreement. Parses TASKS.md's markdown tables
# generically: a header row is recognized by carrying both an "ID" and a
# "Status" column (the board's three lifecycle tables all do; its several
# other "filed from this run"-style summary tables do not, and are correctly
# ignored — verified against the live 660-line file, which mixes both kinds).
# --------------------------------------------------------------------------

def parse_board_rows(board_path: Path):
    """{task_id: [(status, line_no), ...]} for every row found under a
    Status-bearing table header, plus a list of (line_no, raw_cells) for rows
    that matched a task-id link but did not parse cleanly (column-count
    mismatch) — reported as findings rather than silently skipped."""
    lines = board_path.read_text().split("\n")
    rows: dict[str, list] = {}
    malformed: list[tuple[int, str]] = []
    header_cols = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if "Status" in cells and "ID" in cells:
                header_cols = cells
                i += 2  # skip the `|---|---|` separator row
                continue
            if header_cols is not None:
                is_separator = bool(re.match(r'^\|[\s:|-]+\|?$', line.strip()))
                if not is_separator:
                    # The ID column, not "wherever a [T-nnn] link first
                    # appears" — this board's Title/notes cells constantly
                    # link OTHER tasks (e.g. "unblocks T-201"), so scanning
                    # every cell attributed rows to the wrong id whenever
                    # that link preceded the row's own ID cell.
                    id_col = header_cols.index("ID") if "ID" in header_cols else None
                    id_match = None
                    if id_col is not None and id_col < len(cells):
                        m = re.search(r'\[T-(\d+)\]', cells[id_col])
                        if m:
                            id_match = "T-" + m.group(1)
                    if id_match:
                        if len(cells) == len(header_cols):
                            status_cell = cells[header_cols.index("Status")]
                            sm = re.match(r'^(todo|in_progress|in_review|done|blocked)\b',
                                          status_cell)
                            status = sm.group(1) if sm else status_cell
                            rows.setdefault(id_match, []).append((status, i + 1))
                        else:
                            malformed.append((i + 1, line.strip()))
        else:
            header_cols = None
        i += 1
    return rows, malformed


def check_board_agreement(tasks_dir: Path, board_path: Path, task_files: dict) -> list[Finding]:
    findings = []
    if not board_path.is_file():
        return [Finding(board_path, None, None, "TASKS.md not found — cannot check board/file agreement.")]

    rows, malformed = parse_board_rows(board_path)
    for line_no, raw in malformed:
        findings.append(Finding(
            board_path, line_no, None,
            f"table row names a task but its column count does not match "
            f"its table's header — cannot verify its Status cell: {raw!r}"))

    file_ids = set(task_files)
    board_ids = set(rows)

    for missing in sorted(file_ids - board_ids):
        findings.append(Finding(
            task_files[missing][0], None, None,
            f"{missing} has a task file but no row in any Status-bearing "
            f"TASKS.md table."))
    for orphan in sorted(board_ids - file_ids):
        for _, line_no in rows[orphan]:
            findings.append(Finding(
                board_path, line_no, None,
                f"TASKS.md row names {orphan}, which has no task file."))

    for tid in sorted(file_ids & board_ids):
        occurrences = rows[tid]
        if len(occurrences) > 1:
            at = ", ".join(f"line {ln}" for _, ln in occurrences)
            findings.append(Finding(
                board_path, occurrences[0][1], None,
                f"{tid} has {len(occurrences)} rows in TASKS.md ({at}) — "
                f"expected exactly one."))
            continue
        board_status, line_no = occurrences[0]
        file_path, file_status = task_files[tid]
        if file_status is None:
            continue  # frontmatter failed to parse; already reported above
        if board_status != file_status:
            findings.append(Finding(
                board_path, line_no, None,
                f"{tid}'s board row reads status {board_status!r} but its "
                f"file ({file_path.name}) says {file_status!r}."))
    return findings


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def run(tasks_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    task_paths = sorted(p for p in tasks_dir.glob("T-*.md") if re.match(r'^T-\d+-.+\.md$', p.name))

    parsed = {}       # task_id -> (path, data, fm_lines, first_line)
    task_files = {}   # task_id -> (path, status)  [for check 2]
    known_ids = {re.match(r'(T-\d+)', p.name).group(1) for p in task_paths}

    for path in task_paths:
        task_id = re.match(r'(T-\d+)', path.name).group(1)
        fm = read_frontmatter(path)
        if fm is None:
            findings.append(Finding(path, None, None,
                                     "no `---`-fenced frontmatter block found."))
            continue
        fm_lines, first_line, _ = fm

        findings.extend(find_duplicate_keys(fm_lines, first_line, path))

        data, err = parse_frontmatter_dict(fm_lines, path)
        if err:
            findings.append(Finding(path, first_line, None, err))
            # Still register the id: it HAS a task file (that's not in
            # dispute — only its YAML failed to parse), so check 2 must not
            # ALSO report "no task file" or "orphan board row" for it. The
            # status is genuinely unknown here, not merely absent — status=
            # None is the signal check_board_agreement uses to skip the
            # (meaningless) status comparison rather than raise a second,
            # misdirected finding on top of the real one just appended.
            task_files[task_id] = (path, None)
            continue

        parsed[task_id] = (path, data, fm_lines, first_line)
        task_files[task_id] = (path, data.get("status"))

    for task_id, (path, data, fm_lines, first_line) in parsed.items():
        findings.extend(check_status_owner_coherence(data, fm_lines, first_line, path))
        if _HAVE_YAML:
            findings.extend(check_worktree_cleared(data, fm_lines, first_line, path))
        findings.extend(check_pr_present(data, fm_lines, first_line, path))
        findings.extend(check_depends_on(data, fm_lines, first_line, path, known_ids))
        findings.extend(check_vocabularies(data, fm_lines, first_line, path, task_id))

    findings.extend(check_board_agreement(tasks_dir, tasks_dir / "TASKS.md", task_files))

    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="board-check",
        description="Read-only validator for .claude/tasks/ — duplicate "
                     "frontmatter keys, board/file agreement, status/owner "
                     "coherence, worktree close-out, pr: presence, "
                     "depends_on resolution, and controlled vocabularies.",
    )
    ap.add_argument("--tasks-dir", default=str(TASKS_DIR),
                     help=f"board directory to check (default: {TASKS_DIR})")
    ap.add_argument("--quiet", action="store_true",
                     help="print findings only, no pass/fail summary line")
    args = ap.parse_args(argv)

    tasks_dir = Path(args.tasks_dir)
    if not tasks_dir.is_dir():
        ap.error(f"--tasks-dir is not a directory: {tasks_dir}")

    if not _HAVE_YAML:
        print("board-check: WARNING — PyYAML not installed; check 4 "
              "(checkpoint.worktree) is skipped entirely, and any check "
              "that reads a NESTED frontmatter value (e.g. checkpoint.pr "
              "consistency in check 5) degrades to top-level-only. "
              "Top-level checks (3, 6, 7, and the top-level half of 5) "
              "still run at full accuracy — true/false coercion for "
              "security_review is handled by the fallback parser too.",
              file=sys.stderr)

    try:
        findings = run(tasks_dir)
    except (OSError, UnicodeDecodeError) as exc:
        # The docstring's exit-code contract promises 2 here — a board that
        # cannot be READ at all (permissions, encoding, a vanished file
        # between glob() and read_text()) is not "drift"; folding it into
        # the findings list at exit 1 is a false GREEN's cousin: test-all.sh
        # reads it as an ordinary failing check, and the PostToolUse hook
        # would present a raw traceback to the model captioned "found
        # frontmatter drift introduced by this edit" — actively misleading.
        # Caught narrowly (not bare Exception) so an actual bug in this
        # tool still surfaces as the traceback it should be, not a quiet 2.
        print(f"board-check: could not read the board "
              f"({exc.__class__.__name__}: {exc}) — this is a read failure, "
              f"not content drift; nothing was checked.", file=sys.stderr)
        return 2

    for f in sorted(findings, key=lambda f: (f.file.name, f.line or 0)):
        print(str(f))

    if not args.quiet:
        if findings:
            print(f"\nboard-check: {len(findings)} finding(s).", file=sys.stderr)
        else:
            print("board-check: clean.", file=sys.stderr)

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
