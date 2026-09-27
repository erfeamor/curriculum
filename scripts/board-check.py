#!/usr/bin/env python3
"""
board-check — a read-only validator over the task board (.claude/tasks/).

Part of the /dev-loop pipeline (T-031). The board is hand-edited YAML
frontmatter plus a hand-edited markdown index, and every consistency property
it depends on has so far been enforced by people remembering — which the
board's own history records failing repeatedly, including on the same day the
failure was written down (see .claude/tasks/T-031-board-frontmatter-validator.md
for the twelve recorded incidents this tool exists to catch).

Eight checks, each mapped to a real incident:
  1. Duplicate keys within a frontmatter mapping (T-152, T-202, T-104/T-151).
  2. Board row <-> file agreement: one row per file, status matches (T-002,
     T-019, three recurrences).
  3. status/owner coherence (todo => no owner; in_progress/in_review/done =>
     owner present).
  4. checkpoint.worktree cleared on closed (done) tasks (T-101, T-102).
  5. pr: present on in_review/done, consistent with checkpoint.pr (T-011,
     T-009, T-019). Widened 2026-09-27 (T-032) to any status once
     checkpoint.pr already holds a real value -- the T-201/422fbeb
     incident: an open PR sat unannounced at status: in_progress, the one
     status the original status-gate never examined.
  6. depends_on resolves to a real task file.
  7. Controlled vocabularies: status, security_review, risk.
  8. Link integrity (T-032, added 2026-08-24 on the human's instruction,
     after the TASKS.md/HISTORY.md split invented five dead filenames and
     one live cross-reference that this tool reported clean throughout):
     every `[T-xxx](T-nnn-slug.md)` link in TASKS.md, HISTORY.md, README.md
     and every task file resolves to a file that exists (primary), and the
     visible id agrees with the id the target actually names (secondary --
     a different defect from a dead link). Offline and deterministic on
     purpose: no external URLs, no anchors as a navigation destination, no
     title-equality check (titles are deliberately shortened/annotated on
     board rows and left in place by the strike-don't-delete convention --
     see the task file for why a title check was ruled out).

     Round 2 review, 2026-09-27: rebuilt on markdown_it's CommonMark token
     stream rather than a hand-rolled approximation of it (fences, code
     spans, blockquotes, indented code, HTML comments and backslash-
     escapes are excluded by the PARSER now, not by regexes trying to
     re-derive CommonMark's own grammar one surface form at a time -- see
     the ruling below and the check-8 section for why). Reference-style
     links (`[x][ref]` + a `[ref]: dest` definition) are resolved by the
     parser at no extra cost, so they are IN scope now, not a documented
     limitation.

Ruling (binding, from H1 — see the task file's checkpoint.h1_rulings):
  - Check 1 never delegates to yaml.safe_load() for KEY EXTRACTION.
    safe_load() silently accepts duplicate keys and returns the LAST —
    exactly the behaviour that made all four shadowing incidents invisible.
    It uses yaml.compose() instead (the COMPOSING api -- parses into a
    node tree, duplicates intact, nothing collapsed). Narrowed on evidence
    at review round 3 (the original ruling read as "no YAML parser, ever",
    right about the hazard but wrong about the remedy) and again at round
    4: a version of this kept a hand-rolled raw-line scanner as an
    optional fallback for when PyYAML was absent, and the dual-path
    dispatch that required orphaned the scanner's entire test suite
    silently. PyYAML is now a hard requirement (matching
    qa-env-override.py's own precedent in this repo) and there is exactly
    ONE implementation of check 1. See the check-1 section below.
  - Read-only, always. Nothing here reformats, reorders or rewrites
    frontmatter; the board's strike-don't-delete convention means these files
    carry DELIBERATE contradictions that a formatter would destroy.
  - Two exemptions are binding, not oversights: T-301/T-401/T-402/T-501
    carry no risk/security_review (2026-08-17 sweep, deliberate — see below),
    and acceptance-checkbox state is never enforced (2026-08-20 sweep ruled it
    convention).
  - Does not parse the body. Prose drift is what sweeps are for.
  - Check 8 never hand-rolls CommonMark. Round 1 review (2026-09-27) found
    8 (really ~15) real defects in a regex/state-machine approximation of
    fences, code spans, blockquotes, indented code, HTML comments and
    escapes -- the identical failure shape check 1's own ruling above
    already lived through and rejected for YAML. Round 2 (same day)
    replaced it with markdown_it's real CommonMark token stream: only
    `link_open` tokens inside `inline` content count, so everything the
    regex version had to re-derive by hand is instead excluded by
    construction. markdown-it-py is now a hard requirement, PyYAML-style
    (see the import below) -- there is exactly ONE implementation of
    check 8, matching check 1's own precedent.

Usage:
    scripts/board-check.py                  # check the live board, exit 0/1
    scripts/board-check.py --tasks-dir DIR  # check a different board (tests)
    scripts/board-check.py --quiet          # print findings only, no summary

Exit codes: 0 = clean, 1 = at least one finding OR PyYAML missing at
import time (sys.exit(str) -- Python's own convention), 2 = the board
itself could not be READ once running (I/O error, not a single file) --
a false GREEN here is worse than a crash, so this deliberately does not
swallow that class of error.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

# YAML is used two ways: yaml.safe_load() for checks 2-7 (collapses
# duplicate keys to the last value -- fine there, that IS what ships), and
# yaml.compose() for check 1 (preserves every key/value pair with its own
# line, duplicates intact -- see the ruling above find_duplicate_keys).
#
# HARD REQUIREMENT, not an optional fallback (round 3 review, revised
# ruling). A prior version made PyYAML optional and hand-rolled a raw-line
# scanner for check 1 plus a minimal top-level-only reader for checks 2-7
# so this tool would run without it. That "no hard dependency" goal cost
# more than it bought: the scanner alone needed five rounds of surface-
# form-specific bug fixes (compact sequences, block-scalar chomping
# order, bare block-scalar sequence items) and was STILL blind to quoted
# keys, hyphenated keys and flow mappings even fixed; the dual-path
# dispatch this forced then orphaned the scanner's entire test suite
# (every crafted fixture exercised only the compose() path once it
# existed, silently) -- a bug born directly from having two paths to keep
# honest, not from either path's own logic. Matches this repo's own
# sibling tool: qa-env-override.py has required PyYAML outright since it
# was written, same message shape, and runs on the same machines this
# does.
try:
    import yaml
except ModuleNotFoundError:
    sys.exit("board-check: PyYAML is required (pip install pyyaml).")

# markdown_it is check 8's real CommonMark parser (round 2 review,
# 2026-09-27) -- same hard-requirement shape as PyYAML above and the same
# reasoning: a prior regex/state-machine version hand-rolled fences, code
# spans, blockquotes, indented code, HTML comments and escapes one surface
# form at a time (round 1 review, same day, found 8 real defects in it,
# several false positives), which is exactly the failure PyYAML's own
# ruling above already rejected for check 1. No optional fallback.
try:
    from markdown_it import MarkdownIt
except ImportError:
    # ImportError, not the narrower ModuleNotFoundError (round 3 review,
    # item 9): a partially-broken install (a C-extension mismatch, a
    # corrupted wheel) raises the base ImportError, not always its
    # module-not-found subclass, and this message must cover that path
    # too rather than let it fall through to a raw traceback. Confirmed
    # by actually simulating the missing-dependency path (a faked
    # `__import__` raising a bare ImportError), not assumed.
    sys.exit("board-check: markdown-it-py is required "
              "(pip install markdown-it-py, or the python3-markdown-it "
              "package on Debian/Ubuntu).")

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / ".claude" / "tasks"

# Controlled vocabularies (check 7).
STATUS_VALUES = {"todo", "in_progress", "in_review", "done", "blocked"}
RISK_VALUES = {"trivial", "low", "normal", "high"}

# 2026-08-17 sweep ruling, binding per H1: assigning risk/security_review to
# an unrefined task would "manufacture ratified-looking decisions nobody
# made". These four carry neither key, on purpose (five until T-201 was refined). Do not invent values for
# them and do not warn on their absence.
UNREFINED_EXEMPT = {"T-301", "T-401", "T-402", "T-501"}   # T-201 left 2026-09-24: refined at stage 0 on 2026-08-27, carries both keys

# Sentinel values meaning "deliberately absent", shared with
# qa-env-override.py's _NO_WORKTREE set for checkpoint.worktree (check 4).
_NONE_SENTINELS = {"none", "null", "n/a", "-", ""}

# `pr:` sentinel accepted ONLY on a `done` task (never `in_review`, where a PR
# is definitionally open) — see check 5 for the live case this covers (T-010:
# the work shipped entirely through other tasks' PRs, recorded in a comment
# the day the key was added). Kept narrow: a task can say "no PR exists and
# that is correct" the same way checkpoint.worktree already does, but cannot
# use it to dodge review while a PR really is open.
#
# `-` MUST BE QUOTED (`pr: "-"`) to reach this set at all -- a bare
# `pr: -` is a YAML SCANNER ERROR (confirmed against yaml.safe_load: "-"
# unquoted after "key:" on the same line starts a nested sequence entry,
# which is invalid there), so parse_frontmatter_dict's own YAML-error path
# reports it before check_pr_present ever runs. Kept rather than dropped,
# for parity with checkpoint.worktree's identical `-` entry in
# _NONE_SENTINELS above and because `pr: "-"` (quoted) is valid and does
# reach here — just documented rather than silently unreachable.
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
    # Column 0 ONLY -- `.rstrip()` (trailing whitespace/CR only), never
    # `.strip()`. `.strip()` also eats LEADING indentation, so an indented
    # "---" INSIDE a block scalar (a markdown horizontal rule in
    # checkpoint.review_trail or checkpoint.enforcement_propagation --
    # both hand-authored prose) was read as the closing fence. That
    # truncates the frontmatter mid-file: everything after the real "---"
    # is treated as body, so checks 1/4/5 see none of it and silently miss
    # every real defect there, while check 6 spuriously flags whatever
    # depends_on-shaped text happens to survive in the truncated tail.
    # HIGH severity: this is the flagship check going dark on exactly the
    # prose-heavy files it exists to police.
    if not raw_lines or raw_lines[0].rstrip() != "---":
        return None
    end = None
    for i in range(1, len(raw_lines)):
        if raw_lines[i].rstrip() == "---":
            end = i
            break
    if end is None:
        return None
    return raw_lines[1:end], 2, end  # frontmatter body starts at file line 2


# --------------------------------------------------------------------------
# Check 1 — duplicate keys within a frontmatter mapping, via yaml.compose().
#
# T-031's original H1 ruling forbade delegating this check to a YAML
# PARSER -- correctly: yaml.safe_load() (the LOADING api -- Composer +
# Constructor) collapses duplicate mapping keys and returns the last
# value, which is exactly the failure mode of all four incidents this
# check exists to catch (T-152's triple `worktree:`, T-202's second
# `security_review:`, T-104/T-151's `review_round` shadowing).
#
# That ruling was right about the hazard and wrong about the remedy.
# yaml.compose() runs only the Composer stage -- it returns the node
# TREE, one step before Construction ever collapses anything -- so every
# key/value pair survives with its own source line, duplicates intact.
# Re-based on evidence at review round 3, recorded in T-031's
# checkpoint.h1_rulings.
#
# This replaced a hand-rolled raw-line scanner that needed FIVE rounds of
# surface-form-specific bug fixes (compact sequences, block-scalar
# chomping order, bare block-scalar sequence items) and, even fixed, was
# still permanently blind to quoted keys (`"status":`), hyphenated keys
# (`review-round:`) and flow mappings (`{worktree: a, worktree: none}`) --
# because a hand-rolled scanner is reimplementing the YAML grammar one
# surface form at a time, and every miss was silent. yaml.compose()
# already understands the full grammar, so none of those are special
# cases here. Keeping the scanner as an optional fallback (so this tool
# would run without PyYAML) was tried and reverted at round 3: the
# dual-path dispatch it required orphaned the scanner's ENTIRE test
# suite (every crafted fixture exercised only the compose() path once it
# existed, silently) -- a bug caused by having two paths to keep honest,
# not by either path's own logic. PyYAML is now a hard requirement (see
# the import at the top of this file), matching qa-env-override.py's own
# long-standing precedent in this repo.
# --------------------------------------------------------------------------

def find_duplicate_keys(fm_lines: list[str], first_file_line: int, path: Path) -> list[Finding]:
    """Returns [] on a YAML error: "duplicate key" isn't a meaningful
    thing to report about a document that isn't valid YAML at all;
    parse_frontmatter_dict's own yaml.safe_load() call (run() calls it
    right after this) is what reports the parse-error finding for it."""
    text = "\n".join(fm_lines)
    try:
        root = yaml.compose(text, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        return []
    findings: list[Finding] = []
    _walk_compose_node(root, first_file_line, path, findings, set())
    return findings


def _walk_compose_node(node, first_file_line: int, path: Path, findings: list,
                        visited: set) -> None:
    """Recurse through a yaml.compose() node tree, reporting duplicate keys
    within each MappingNode. compose() preserves every key/value pair with
    its own line/column, duplicates intact (unlike yaml.safe_load(), which
    silently keeps only the last) -- this is what makes it safe to use for
    check 1 at all. Handles block AND flow mappings uniformly (MappingNode
    has the same `.value` shape -- a list of (key_node, value_node) pairs
    -- for both `checkpoint:\n  worktree: a` and `{worktree: a, worktree:
    none}`), and quoted/hyphenated keys uniformly with plain ones (the key
    is read from ScalarNode.value, not re-derived from a "bare identifier"
    regex the way a hand-rolled scanner would have to).

    `visited`: node ids already walked, so an ALIAS to an already-visited
    mapping (`a: &x {...}` / `b: *x`) is not walked a second time --
    compose() resolves an alias to the SAME node OBJECT as its anchor
    (confirmed empirically: `id(alias_target) == id(anchor_target)`), so
    without this a single real duplicate inside the anchored mapping
    would be reported twice, once per reference to it. Anchors/aliases
    are unused on this board today; guarded anyway since a silent double
    count is cheap to prevent and expensive to notice."""
    if node is None or id(node) in visited:
        return
    visited.add(id(node))
    if isinstance(node, yaml.MappingNode):
        seen: dict[tuple, int] = {}
        for key_node, value_node in node.value:
            if isinstance(key_node, yaml.ScalarNode):
                # Compare the RESOLVED identity (tag + raw text), not the
                # raw text alone. YAML resolves a bare `yes`/`1`/`~` to
                # bool/int/null while a QUOTED "yes"/"1"/"~" stays a
                # string -- yaml.safe_load() agrees ({'yes': ...} and
                # {True: ...} are different keys there too) -- so
                # comparing key_node.value alone invented duplicates
                # between values that were never shadowed at all. The
                # resolver already did this classification; `key_node.tag`
                # is where it is recorded.
                key_id = (key_node.tag, key_node.value)
                line = first_file_line + key_node.start_mark.line
                if key_id in seen:
                    findings.append(Finding(
                        path, line, key_node.value,
                        f"duplicate key {key_node.value!r} in the same "
                        f"mapping — first seen at line {seen[key_id]}. "
                        f"YAML keeps the LAST occurrence, so the value at "
                        f"line {seen[key_id]} is silently shadowed."))
                seen[key_id] = line
            _walk_compose_node(value_node, first_file_line, path, findings, visited)
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            _walk_compose_node(item, first_file_line, path, findings, visited)
    # ScalarNode: nothing further to recurse into.


# --------------------------------------------------------------------------
# A small, deliberately narrow frontmatter reader for checks 3-7 (never
# used for check 1 -- see above).
# --------------------------------------------------------------------------

def parse_frontmatter_dict(fm_lines: list[str], path: Path):
    """Best-effort dict of the frontmatter, for checks 2-7 only. Never used
    for check 1 (duplicate keys), which must see raw lines regardless of
    what parses the rest — see the ruling above find_duplicate_keys."""
    text = "\n".join(fm_lines)
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"
    return (data if isinstance(data, dict) else {}), None



def line_of(fm_lines: list[str], first_file_line: int, key: str) -> int | None:
    """First file line where `key:` appears at column 0 (top-level).

    Round 4 review, LOW: this used to take a `top_level_only=True` flag
    with an "opt out to match at any depth" escape hatch that no caller
    ever used AND that could never have worked -- `pattern.match(raw)`
    requires the match to start at index 0 of the RAW (unstripped) line
    regardless of the flag, so an indented line can never satisfy the
    pattern whether or not the flag's own early-continue guard runs.
    Confirmed empirically (`re.match(r'^status:', '  status: x')` is
    False) before removing it: the guard was provably redundant, not
    merely untested, so the fix is deletion, not a test asserting nothing."""
    pattern = re.compile(rf'^{re.escape(key)}:')
    for offset, raw in enumerate(fm_lines):
        if pattern.match(raw):
            return first_file_line + offset
    return None


def nested_line_of(fm_lines: list[str], first_file_line: int, parent: str, key: str) -> int | None:
    """First file line of `key:` nested DIRECTLY under a top-level
    `parent:` block -- at the immediate-child indent level ONLY, not
    anywhere deeper. The naive `indent > parent_indent` version matched a
    same-named key at ANY depth (e.g. a `pr:` two levels down inside
    checkpoint.pre_apply_gate, ahead of checkpoint's own direct `pr:`), so
    a finding could cite a line whose value is not the one it is actually
    complaining about — and the PostToolUse hook feeds that line to the
    model as the place to edit. The first non-blank line after `parent:`
    fixes the direct-child indent level for the rest of the block; well-
    formed YAML gives every direct child of one mapping the same indent,
    so this is not a guess."""
    in_parent = False
    parent_indent = None
    child_indent = None
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
        if child_indent is None:
            child_indent = indent
        if indent != child_indent:
            continue  # deeper than the direct-child level -- not ours
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
    """pr: present on in_review/done, consistent with checkpoint.pr.

    Widened 2026-09-27 (T-032), live incident at commit 422fbeb (T-201):
    status was `in_progress`, top-level `pr:` was empty, and
    `checkpoint.pr` already held a real, open PR URL. The ORIGINAL gate
    below returned early on anything but in_review/done, so the one
    status where a PR can be open and unannounced -- in_progress, before
    anyone updates status: in_review per board rule 6 -- was the one
    status never examined. board-check reported clean throughout,
    including in the same session that wrote it.

    Round 1 review, 2026-09-27, three more findings on that widening:
      #6 checkpoint.pr can ITSELF hold a sentinel ("none"/"n/a"/"-") --
         that is not a real PR either, and must stay silent at every
         status, reusing the same sentinel set as the top-level field.
         `cp_pr_is_real` below is the fix: it is what every other branch
         gates on now, not bare truthiness of cp_pr_text.
      #5 `pr: none` (the T-010 sentinel) on a `done` task is legitimate
         ONLY when checkpoint.pr is genuinely absent/sentinel too. A
         real checkpoint.pr contradicts the "no PR ever existed"
         declaration and must be reported.
      #7 the rule-6 violation is `status` not in (in_review, done) + a
         REAL checkpoint.pr, full stop -- regardless of what top-level
         pr: holds. The original widening only looked inside the
         "pr_text empty/sentinel" branch, so a top-level pr: that had
         been filled in to AGREE with checkpoint.pr (without status ever
         moving) stayed silent. `blocked` is deliberately skipped rather
         than given "should be in_review" advice, which does not fit a
         blocked task's shape (the reviewer's own second option)."""
    findings = []
    status = data.get("status")
    pr = data.get("pr")
    pr_text = str(pr).strip() if pr is not None else ""
    is_sentinel = pr_text.lower() in _PR_NONE_SENTINELS and pr_text != ""
    checkpoint = data.get("checkpoint")
    cp_pr = checkpoint.get("pr") if isinstance(checkpoint, dict) else None
    cp_pr_text = str(cp_pr).strip() if cp_pr else ""
    cp_pr_is_real = bool(cp_pr_text) and cp_pr_text.lower() not in _PR_NONE_SENTINELS

    if status not in ("in_review", "done"):
        if not cp_pr_is_real or status == "blocked":
            return findings
        message = (f"status is {status!r} but checkpoint.pr already "
                   f"holds {cp_pr_text!r} — board rule 6 requires "
                   f"status: in_review (and pr: set) the moment a PR is "
                   f"open; {status!r} is the status this check's "
                   f"original gate never examined (T-201, commit "
                   f"422fbeb).")
        findings.append(Finding(
            path, line_of(fm_lines, first_line, "pr"), "pr", message))
        return findings

    # status is in_review or done from here.
    if pr_text == "" or is_sentinel:
        if status == "done" and is_sentinel:
            if cp_pr_is_real:
                findings.append(Finding(
                    path, line_of(fm_lines, first_line, "pr"), "pr",
                    f"pr: uses the {pr_text!r} sentinel (declaring no PR "
                    f"ever existed) but checkpoint.pr holds a real PR: "
                    f"{cp_pr_text!r} — the sentinel is only valid when "
                    f"no PR ever existed, and this task has one."))
            return findings  # explicit, recognized "no PR exists" sentinel
        if is_sentinel:
            # A sentinel value is NOT empty (pr_text is truthy, e.g.
            # 'none') -- "top-level pr: is empty" was a false statement
            # about it. The defect here is the sentinel being used on the
            # wrong status, not an absent value.
            message = (f"status is {status!r} but pr: is the sentinel "
                       f"{pr_text!r} — that sentinel is only valid on a "
                       f"`done` task; {status!r} means a PR is "
                       f"definitionally open.")
        else:
            hint = (f" (checkpoint.pr holds {cp_pr_text!r} — board rule 6 "
                     f"says the top-level key is what the board and "
                     f"driver read)"
                     if cp_pr_is_real else "")
            message = f"status is {status!r} but top-level pr: is empty{hint}."
        findings.append(Finding(
            path, line_of(fm_lines, first_line, "pr"), "pr", message))
        return findings

    if cp_pr_is_real and cp_pr_text != pr_text:
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
                # Only skip a SECOND line if it actually IS the
                # `|---|---|` separator -- blindly skipping 2 swallowed
                # the very next row whenever a table's header had no
                # separator (or a malformed one), misdirecting whatever
                # finding that row would have produced at the wrong line
                # (or losing it outright).
                if (i + 1 < len(lines)
                        and re.match(r'^\|[\s:|-]+\|?$', lines[i + 1].strip())):
                    i += 2
                else:
                    i += 1
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
# Check 8 — link integrity. Primary: every `[x](T-nnn-slug.md)` link's
# target resolves to a real file. Secondary: an EXACT `[T-xxx]` link text
# whose numeric id disagrees with the id its target actually names (a
# different defect from a dead link -- the target resolves fine, but names
# the wrong task). Both offline and deterministic: no network, no anchors
# as a navigation destination, no title-equality check (see the module
# docstring and T-032's task file for why those are out of scope).
#
# Round 2 review, 2026-09-27: rebuilt on markdown_it's real CommonMark
# parser rather than a hand-rolled approximation of it. The round-1
# version tried to re-derive, in regexes and a line-based state machine,
# exactly the set of rules a CommonMark parser already enforces: fence
# open/close matching, inline code spans (including ones spanning a line
# break), blockquote nesting, indented code blocks, HTML comments, and
# backslash escapes -- and round 1's review still found 8 (really ~15)
# real defects in that approximation, several of them false positives.
# That is the identical shape check 1's OWN history already lived through
# (see the module-docstring ruling): a hand-rolled scanner needing round
# after round of surface-form-specific fixes while staying blind to
# others. The fix is the same one check 1 already took: delegate to a
# real parser. Walking `md.parse(text)`'s token stream, only `link_open`
# tokens inside an `inline` token's `.children` are links at all --
# everything the regex version had to positively exclude (fences, spans,
# blockquotes, indented code, HTML, escapes) is structurally absent from
# that stream in the first place, not filtered out by us.
#
# Line numbers come from the enclosing block token's `.map` (its 0-indexed
# [start, end) line range) rather than the exact line within it, per this
# round's instructions. This is coarser than the old per-line regex scan
# for one real case on this board: TASKS.md's lifecycle tables have no
# blank line between rows, so CommonMark (with no GFM table extension
# available in this environment -- confirmed, no mdit_py_plugins package
# installed) folds an entire table into ONE paragraph token, and every
# link in it reports the table's first line rather than its own row.
# Traded deliberately for parser-grade correctness on the things that
# were actually wrong; see the task file's round-2 section for the
# `TASKS.md`-table check confirming this doesn't create a NEW false
# positive/negative, only a less-specific line number.
#
# Reference-style links (`[x][ref]` + a `[ref]: dest` definition
# elsewhere in the same file) are resolved by markdown_it automatically,
# so they are IN SCOPE now -- confirmed empirically, not assumed. Link
# text split across a line break within one paragraph is also handled
# (it's one continuous inline token to the parser). Neither is a
# documented limitation any more.
# --------------------------------------------------------------------------

_MD = MarkdownIt("commonmark").enable("table")

# Bare filename only (no further `/`) after stripping the two prefixes this
# board actually uses; the anchor, if any, is discarded (captured OUTSIDE
# group 1) rather than validated -- board rule per T-032: anchors churn and
# are harmless, not a navigation destination this check owns. markdown_it
# has already stripped any `<angle brackets>` and split off a `"title"`
# into its own token attribute before this ever runs, so neither is dealt
# with here any more (round-1's regex version had to do both by hand).
_TASK_TARGET_RE = re.compile(r'^(?:\./|\.\./tasks/)?(T-\d+[^/#]*\.md)(?:#\S*)?$')
_EXACT_TASK_ID_RE = re.compile(r'^T-0*(\d+)$')
# An html_block whose raw content contains what looks like a markdown link
# or an HTML href pointing at a task file (round-3 finding #7) -- raw HTML
# is opaque to the parser's own link tokens, so this is the one place check
# 8 still has to look at TEXT rather than the token stream.
_HTML_BLOCK_SUSPECT_RE = re.compile(r'\]\(T-|href=["\']T-')


def _normalize_link_destination(href: str):
    """A link/image token's `href`/`src` attribute -> the bare
    `T-nnn-slug.md` filename it targets, or None if it isn't shaped like
    a task-file link at all (an anchor-only link, an external URL, a
    path elsewhere in the repo). Percent-decoded first (round-3 finding
    #3): markdown_it does not decode `%XX` escapes itself, and it
    percent-encodes even a LITERAL space inside `<angle brackets>` on
    its own, so a real accented or space-bearing filename never matches
    without this."""
    href = urllib.parse.unquote(href.strip())
    m = _TASK_TARGET_RE.match(href)
    return m.group(1) if m else None


def _mask_frontmatter(path: Path, text: str) -> str:
    """Blank the frontmatter block (both `---` fences and everything
    between) before handing `text` to the markdown parser, keeping the
    LINE COUNT identical so every line number after it still lines up.
    Reuses read_frontmatter's own fence bounds rather than re-deriving
    them. Two round-3 findings, opposite directions, both fixed by never
    parsing frontmatter as markdown at all: a broken link deliberately
    quoted inside a YAML block scalar must stay silent (finding #4 --
    it isn't body prose), and an unbalanced fence marker inside
    frontmatter prose must not bleed into the body and hide a real dead
    link there (finding #5 -- confirmed empirically that a LOW-indent
    block scalar genuinely opens a real CommonMark fence that never
    closes, swallowing everything after it to end of file)."""
    fm = read_frontmatter(path)
    if fm is None:
        return text
    _, _, end = fm  # 0-based index of the closing '---' line
    lines = text.split("\n")
    for idx in range(0, min(end, len(lines) - 1) + 1):
        lines[idx] = ""
    return "\n".join(lines)


def _iter_markdown_links(path: Path):
    """Yields (line_no, visible_text, target) for every task-file-shaped
    markdown link OR image in `path`, found by walking markdown_it's own
    CommonMark token stream (see the section comment above for why)."""
    text = _mask_frontmatter(path, path.read_text())
    for block in _MD.parse(text):
        if block.type != "inline" or not block.map:
            continue
        base_line = block.map[0] + 1  # 0-indexed block-start line -> file line
        children = block.children or []
        offset = 0  # softbreaks/hardbreaks seen so far in THIS block (finding #2)
        i = 0
        while i < len(children):
            child = children[i]
            if child.type in ("softbreak", "hardbreak"):
                offset += 1
                i += 1
                continue
            if child.type == "image":
                # A self-contained token, not an open/close pair
                # (round-3 finding #6) -- its own .content is the alt
                # text, its `src` the destination.
                target = _normalize_link_destination(child.attrs.get("src", ""))
                if target is not None:
                    yield base_line + offset, child.content, target
                i += 1
                continue
            if child.type != "link_open":
                i += 1
                continue
            link_line = base_line + offset
            target = _normalize_link_destination(child.attrs.get("href", ""))
            j = i + 1
            text_parts = []
            while j < len(children) and children[j].type != "link_close":
                ctype = children[j].type
                if ctype in ("text", "code_inline"):
                    text_parts.append(children[j].content)
                elif ctype in ("softbreak", "hardbreak"):
                    # Renders as a space (round-3 finding #8) -- and
                    # still advances the shared line-offset for
                    # whatever comes after this link in the same block.
                    text_parts.append(" ")
                    offset += 1
                # else (raw HTML, etc.): contributes nothing to the
                # visible text, per finding #8.
                j += 1
            if target is not None:
                yield link_line, "".join(text_parts), target
            i = j + 1


def _iter_html_block_warnings(path: Path):
    """Yields line_no for every html_block whose raw content contains
    what looks like a task-file link or href (round-3 finding #7): raw
    HTML is opaque to the parser's OWN link tokens, so a link inside one
    (e.g. a `<summary>` with no blank line before the next paragraph,
    which CommonMark's HTML-block rule keeps consuming) is silently
    never checked at all unless this says so."""
    text = _mask_frontmatter(path, path.read_text())
    for block in _MD.parse(text):
        if block.type == "html_block" and _HTML_BLOCK_SUSPECT_RE.search(block.content):
            yield block.map[0] + 1


def check_link_integrity(tasks_dir: Path, scan_files: list[Path],
                          task_paths: list[Path]) -> list[Finding]:
    existing = {p.name for p in task_paths}
    findings: list[Finding] = []
    for path in scan_files:
        if not path.is_file():
            continue
        for line_no in _iter_html_block_warnings(path):
            findings.append(Finding(
                path, line_no, "link-html",
                "an HTML block here contains what looks like a task-file "
                "link or href -- raw HTML is opaque to this check; use "
                "markdown link syntax if it needs to be validated."))
        for line_no, text, target in _iter_markdown_links(path):
            if target not in existing:
                findings.append(Finding(
                    path, line_no, "link",
                    f"link target {target!r} does not resolve to any file "
                    f"under {tasks_dir.name}/ (dead link)."))
                continue
            # ID/target agreement only applies when the link TEXT is
            # EXACTLY a task id (round-1 finding #4) -- descriptive prose
            # that merely mentions another task ("follow-up to T-031")
            # is not claiming to BE that task's link. Compared
            # numerically, not as strings, so T-32 and T-032 agree. The
            # target always starts with T-\d+ (guaranteed by
            # _TASK_TARGET_RE above), so target_id_m always matches.
            target_id_m = _EXACT_TASK_ID_RE.match(re.match(r'T-\d+', target).group(0))
            text_id_m = _EXACT_TASK_ID_RE.match(text.strip())
            if text_id_m and int(text_id_m.group(1)) != int(target_id_m.group(1)):
                findings.append(Finding(
                    path, line_no, "link-id",
                    f"link text names {text.strip()!r} but its target "
                    f"{target!r} names T-{target_id_m.group(1)} — the "
                    f"link resolves, but the visible id and the target "
                    f"disagree."))
    return findings


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def run(tasks_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    task_paths = sorted(p for p in tasks_dir.glob("T-*.md") if re.match(r'^T-\d+-.+\.md$', p.name))
    known_ids = {re.match(r'(T-\d+)', p.name).group(1) for p in task_paths}

    # Id collisions FIRST, and reported explicitly. Two files sharing a
    # T-nnn id used to shadow each other via plain dict assignment below
    # (task_id -> ...): whichever file was processed LAST silently won,
    # and every id-keyed check (3/4/5/6/7, plus check 2's board-row match)
    # only ever ran against the winner -- a FALSE GREEN for the loser's
    # real defects (reproduced with a stale renamed file still carrying a
    # checkpoint.worktree violation that check 4 never got a chance to
    # see). Single-pass processing below means every file's own checks
    # (1, 3, 4, 5, 6, 7) now run regardless of collisions; the collision
    # itself is reported here because check 2 (board/file agreement) has
    # no sound way to attribute one TASKS.md row to more than one file.
    id_to_paths: dict[str, list[Path]] = {}
    for p in task_paths:
        id_to_paths.setdefault(re.match(r'(T-\d+)', p.name).group(1), []).append(p)
    for tid, paths in sorted(id_to_paths.items()):
        if len(paths) > 1:
            names = ", ".join(p.name for p in paths)
            findings.append(Finding(
                paths[0], None, None,
                f"{tid} is claimed by {len(paths)} task files ({names}) — "
                f"each would silently shadow the others in every id-keyed "
                f"check. Rename or remove all but one."))

    task_files = {}   # task_id -> (path, status)  [for check 2]

    for path in task_paths:
        task_id = re.match(r'(T-\d+)', path.name).group(1)
        fm = read_frontmatter(path)
        if fm is None:
            findings.append(Finding(path, None, None,
                                     "no `---`-fenced frontmatter block found."))
            # Register the id even though frontmatter is absent: the FILE
            # exists (that is not in dispute), so check 2 must not ALSO
            # claim "no task file" on top of this finding — the mirror of
            # the fix just below for a YAML parse error.
            task_files[task_id] = (path, None)
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

        task_files[task_id] = (path, data.get("status"))

        findings.extend(check_status_owner_coherence(data, fm_lines, first_line, path))
        findings.extend(check_worktree_cleared(data, fm_lines, first_line, path))
        findings.extend(check_pr_present(data, fm_lines, first_line, path))
        findings.extend(check_depends_on(data, fm_lines, first_line, path, known_ids))
        findings.extend(check_vocabularies(data, fm_lines, first_line, path, task_id))

    findings.extend(check_board_agreement(tasks_dir, tasks_dir / "TASKS.md", task_files))

    scan_files = [tasks_dir / "TASKS.md", tasks_dir / "HISTORY.md",
                  tasks_dir / "README.md", *task_paths]
    findings.extend(check_link_integrity(tasks_dir, scan_files, task_paths))

    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="board-check",
        description="Read-only validator for .claude/tasks/ — duplicate "
                     "frontmatter keys, board/file agreement, status/owner "
                     "coherence, worktree close-out, pr: presence, "
                     "depends_on resolution, controlled vocabularies, and "
                     "link integrity.",
    )
    ap.add_argument("--tasks-dir", default=str(TASKS_DIR),
                     help=f"board directory to check (default: {TASKS_DIR})")
    ap.add_argument("--quiet", action="store_true",
                     help="print findings only, no pass/fail summary line")
    args = ap.parse_args(argv)

    tasks_dir = Path(args.tasks_dir)
    if not tasks_dir.is_dir():
        ap.error(f"--tasks-dir is not a directory: {tasks_dir}")

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
