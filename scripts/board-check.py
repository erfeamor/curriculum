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
  - Check 1 never delegates to yaml.safe_load() for KEY EXTRACTION.
    safe_load() silently accepts duplicate keys and returns the LAST —
    exactly the behaviour that made all four shadowing incidents invisible.
    Narrowed on evidence at review round 3: the original ruling read as
    "no YAML parser, ever" and that was right about the hazard (the
    LOADING api collapses duplicates) but wrong about the remedy. Check 1
    now uses yaml.compose() (the COMPOSING api -- parses into a node tree,
    duplicates intact, nothing collapsed) whenever PyYAML is available; the
    hand-rolled raw-line scanner is kept as the fallback for when it is
    not. See the check-1 section below for the full reasoning.
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

# YAML is used two ways: yaml.safe_load() for checks 2-7 (collapses
# duplicate keys to the last value -- fine there, that IS what ships), and
# yaml.compose() for check 1 (preserves every key/value pair with its own
# line, duplicates intact -- see the ruling above find_duplicate_keys).
# Both are optional: this tool has no hard external dependency, and falls
# back to a hand-rolled raw-line scanner for check 1 and a minimal
# top-level-only reader for checks 2-7 when PyYAML is absent.
try:
    import yaml
    _HAVE_YAML = True
except ModuleNotFoundError:
    _HAVE_YAML = False

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
# Check 1 — duplicate keys within a frontmatter mapping.
#
# Two implementations, in priority order:
#
#   1. yaml.compose() (this file's PRIMARY path when PyYAML is available).
#      T-031's original H1 ruling forbade delegating this check to a YAML
#      PARSER -- correctly: yaml.safe_load() collapses duplicate mapping
#      keys and returns the last value, which is exactly the failure mode
#      of all four incidents this check exists to catch (T-152's triple
#      `worktree:`, T-202's second `security_review:`, T-104/T-151's
#      `review_round` shadowing). That ruling was right about the hazard
#      and wrong about the remedy: yaml.compose() returns the node TREE
#      (the Composer stage, before Construction), which preserves EVERY
#      key/value pair with its own source line, duplicates intact -- it
#      does not collapse anything. Re-based on evidence (round 3 review),
#      recorded in T-031's checkpoint.h1_rulings.
#
#      This closes an entire CLASS of gap the hand-rolled scanner below
#      kept hitting one surface form at a time across three review
#      rounds -- compact sequences, `|2-` chomping order, bare `- |`
#      sequence items, quoted keys (`"status":`), hyphenated keys
#      (`review-round:`), flow mappings (`{worktree: a, worktree: none}`)
#      -- because compose() already understands the full YAML grammar;
#      nothing here is re-implementing it one shape at a time anymore.
#
#   2. _find_duplicate_keys_scan() (the FALLBACK, used only when PyYAML is
#      absent). Raw-line, indent-tracking scanner -- narrower than (1) by
#      construction (see its own docstring for exactly which shapes it
#      does not understand), kept only so this tool has no hard external
#      dependency. An 8000-document differential fuzz against a
#      duplicate-aware loader found zero divergences between this
#      scanner and (1) once the bare-`- |`-item bug above was fixed, so
#      it remains trustworthy for the fallback role.
# --------------------------------------------------------------------------

_KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):(\s|$)')
_DASH_RE = re.compile(r'^(-)(\s+(.*))?$')
# YAML permits the block-scalar chomping/indentation indicators in
# EITHER order (`|2-` and `|-2` are both legal, likewise `>2+`/`>+2`) --
# confirmed against yaml.safe_load, not assumed. The original
# sign-then-digit-only pattern missed the digit-then-sign form, so a
# `|2-` block scalar was never recognized as one and its prose content
# was walked as structure, producing a FALSE duplicate-key finding on
# whatever key names happened to appear twice in that prose. Dormant on
# the live board today (nothing uses an indentation indicator), but the
# realistic trigger is close: the deeply-nested prose-with-colons block
# scalars (checkpoint.review_trail, checkpoint.enforcement_propagation)
# are exactly where someone reaches for one.
_BLOCK_SCALAR_RE = re.compile(r':\s*[|>][+-]?[0-9]?[+-]?\s*(#.*)?$')
# Same indicator, no leading ":" -- a sequence item whose value IS a
# block scalar ("- |") rather than a "key: value" pair.
_BARE_BLOCK_SCALAR_RE = re.compile(r'^[|>][+-]?[0-9]?[+-]?\s*(#.*)?$')


class _Scope:
    __slots__ = ("indent", "keys")

    def __init__(self, indent: int):
        self.indent = indent
        self.keys: dict[str, int] = {}


def _find_duplicate_keys_scan(fm_lines: list[str], first_file_line: int, path: Path) -> list[Finding]:
    """The FALLBACK path (no PyYAML): a raw-line, indent-tracking scanner.

    Correctness constraint (verified against the live board, T-002 and
    T-103): a naive "count keys at this indent" scan produces two DISTINCT
    classes of false positive that a mapping-scope-aware scan must both
    avoid --
      (a) literal YAML block-sequence items ("- key: value" siblings),
          where the same key legitimately repeats once per list item; and
      (b) sibling nested mappings under different parent keys that happen
          to share a child key name at the same indent (T-002's
          `pre_apply_gate:` / `apply:` / `post_apply:` each carry their
          own `evidence:`, `run:`, `commit:` -- three distinct rounds, not
          one mapping with duplicates).
    Both are handled by tracking mapping SCOPES on a stack, keyed by
    indent, and starting a fresh (empty) scope every time indentation
    dedents past the scope that owned it -- rather than a flat
    per-indent-level counter.

    Known to be NARROWER than yaml.compose() (the primary path, used
    instead of this whenever PyYAML is available): quoted keys
    (`"status":`), hyphenated keys (`review-round:`) and flow mappings
    (`{worktree: a, worktree: none}`) are not recognized as keys at all by
    `_KEY_RE`, so a duplicate expressed in any of those forms is invisible
    here. This is an accepted, documented gap in the fallback, not a
    silent one -- see the check-1 header comment above."""
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
            if _BARE_BLOCK_SCALAR_RE.match(rest):
                # "- |" / "- >" / "- |-" etc: the sequence item's VALUE is
                # ITSELF a block scalar, not a "key: value" pair -- there is
                # no ":" anywhere on this line, so _BLOCK_SCALAR_RE (which
                # requires one) never fires here. Missing this meant a bare
                # block-scalar list item's prose was walked as structure,
                # producing a phantom duplicate on whatever key names
                # happened to repeat inside it (reproduced with an
                # h1_rulings: item written as "- |" containing two
                # "ruling:" lines). The content is indented deeper than the
                # dash itself, same threshold a keyed block scalar uses.
                skip_until_indent = indent
                continue
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


def find_duplicate_keys(fm_lines: list[str], first_file_line: int, path: Path) -> list[Finding]:
    """Dispatcher: yaml.compose() when PyYAML is available (understands the
    full YAML grammar -- see the check-1 header comment), the hand-rolled
    _find_duplicate_keys_scan() otherwise."""
    if _HAVE_YAML:
        result = _find_duplicate_keys_compose(fm_lines, first_file_line, path)
        if result is not None:
            return result
        # yaml.compose() raised: the document isn't valid YAML at all, so
        # "duplicate key" isn't a meaningful thing to report about it --
        # parse_frontmatter_dict's own yaml.safe_load call (run() calls it
        # right after this) is what reports the parse-error finding for
        # this file. Nothing further for check 1 to add.
        return []
    return _find_duplicate_keys_scan(fm_lines, first_file_line, path)


def _find_duplicate_keys_compose(fm_lines: list[str], first_file_line: int, path: Path):
    """The PRIMARY path (PyYAML available): walk yaml.compose()'s node
    tree. Returns None (not []) on a YAML error, so the caller can tell
    "valid YAML, no duplicates" apart from "not valid YAML at all"."""
    text = "\n".join(fm_lines)
    try:
        root = yaml.compose(text, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        return None
    findings: list[Finding] = []
    _walk_compose_node(root, first_file_line, path, findings)
    return findings


def _walk_compose_node(node, first_file_line: int, path: Path, findings: list) -> None:
    """Recurse through a yaml.compose() node tree, reporting duplicate keys
    within each MappingNode. compose() preserves every key/value pair with
    its own line/column, duplicates intact (unlike yaml.safe_load(), which
    silently keeps only the last) -- this is what makes it safe to use for
    check 1 at all. Handles block AND flow mappings uniformly (MappingNode
    has the same `.value` shape -- a list of (key_node, value_node) pairs
    -- for both `checkpoint:\n  worktree: a` and `{worktree: a, worktree:
    none}`), and quoted/hyphenated keys uniformly with plain ones (the key
    is read from ScalarNode.value, not re-derived from a "bare identifier"
    regex the way the fallback scanner's _KEY_RE has to)."""
    if node is None:
        return
    if isinstance(node, yaml.MappingNode):
        seen: dict[str, int] = {}
        for key_node, value_node in node.value:
            key_str = key_node.value if isinstance(key_node, yaml.ScalarNode) else None
            line = first_file_line + key_node.start_mark.line
            if key_str is not None:
                if key_str in seen:
                    findings.append(Finding(
                        path, line, key_str,
                        f"duplicate key {key_str!r} in the same mapping — "
                        f"first seen at line {seen[key_str]}. YAML keeps "
                        f"the LAST occurrence, so the value at line "
                        f"{seen[key_str]} is silently shadowed."))
                seen[key_str] = line
            _walk_compose_node(value_node, first_file_line, path, findings)
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            _walk_compose_node(item, first_file_line, path, findings)
    # ScalarNode (and AliasNode, unused on this board): nothing to recurse into.


# --------------------------------------------------------------------------
# A small, deliberately narrow frontmatter reader for checks 3-7. Delegates
# to PyYAML when available (parsing everything BUT duplicate keys is not the
# load-bearing part of this tool), and falls back to a minimal top-level
# scanner if PyYAML is absent, so this tool has no hard external dependency.
# --------------------------------------------------------------------------

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
    # Minimal fallback: only top-level `key: value` lines, no nesting.
    # Handles both this board's real vocabularies at top level: scalars
    # (coerced true/false -> bool) and flow sequences (`depends_on: []`,
    # `depends_on: [T-013, T-202]` -> a real Python list, not left as the
    # bracketed STRING that used to comma-split into '[]' / '[T-013' /
    # 'T-202]' and fail check 6 on nearly every file). checkpoint.worktree
    # (check 4) and checkpoint.pr (half of check 5) are nested and still
    # degrade to "not checked" without PyYAML — see the check-4 gate in
    # run() and the warning printed at startup.
    data = {}
    for line in fm_lines:
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$', line)
        if m and not line.startswith((" ", "\t")):
            key = m.group(1)
            raw_val = _strip_fallback_comment(m.group(2)).strip()
            data[key] = _coerce_fallback_value(raw_val)
    return data, None


def _strip_fallback_comment(value: str) -> str:
    """Truncate a raw `key: value` tail at the first '#' that starts a
    comment -- quote-aware. The old `value.split("#", 1)[0]` truncated
    blindly, so `pr: "#53"` (`#nn` is TASKS.md's own spelling for a PR
    number, e.g. its T-401 row) read as empty rather than the string
    '#53'."""
    in_quote = None
    for i, ch in enumerate(value):
        if in_quote:
            if ch == in_quote:
                in_quote = None
            continue
        if ch in ("'", '"'):
            in_quote = ch
            continue
        if ch == "#":
            return value[:i]
    return value


_FLOW_LIST_RE = re.compile(r'^\[(.*)\]$')


def _coerce_fallback_value(raw: str):
    """Top-level value coercion for the no-PyYAML fallback: a flow sequence
    (`[...]`) becomes a real list (comma-split, each item stripped of
    surrounding whitespace/quotes — this board never nests a comma inside a
    quoted depends_on item, so this is not a general YAML flow parser and
    does not try to be one); anything else is a scalar, handled by
    _coerce_fallback_scalar."""
    m = _FLOW_LIST_RE.match(raw)
    if m:
        inner = m.group(1).strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",")]
    return _coerce_fallback_scalar(raw)


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
                     if cp_pr_text else "")
            message = f"status is {status!r} but top-level pr: is empty{hint}."
        findings.append(Finding(
            path, line_of(fm_lines, first_line, "pr"), "pr", message))
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
        print("board-check: WARNING — PyYAML not installed. This warning "
              "has been wrong about its own blast radius twice before "
              "(security_review boolean coercion, then depends_on flow "
              "sequences), so it now names checks by number rather than "
              "promising a blanket 'top-level is fine': checks 3 and 7 read "
              "only top-level scalars and are unaffected. Check 6 "
              "(depends_on) is handled for this board's real usage — flow "
              "sequences (`[T-013, T-202]`) and bare/comma-separated "
              "scalars — but the fallback is NOT a general YAML flow "
              "parser (no quoted-comma handling, no nesting). Check 4 "
              "(checkpoint.worktree) is skipped entirely — it is nested "
              "and the fallback reads no nested keys at all. Check 5 "
              "(pr:) runs its top-level half; the checkpoint.pr "
              "consistency half is skipped for the same nested-key reason.",
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
