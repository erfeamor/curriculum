---
id: T-031
title: "A validator for the task board: the checks this board keeps running by hand and keeps failing"
repo: cv-project (meta)
status: done
owner: infrastructure-engineer
branch: feat/board-validator
pr: https://github.com/erfeamor/curriculum/pull/59
depends_on: []
risk: normal
security_review: false   # STAGE-0 DEFAULT, AND A1 MUST RE-DECIDE IT: the H1-ratified scope adds a settings.json HOOK, which is a command-execution path even though it is not in adapter §5's list (that list names deployed CI config -- Jenkinsfile, workflows, .drone.yml, Vercel -- not the local harness). A hook runs a script automatically on matching tool calls, so the real diff may warrant /security-review on that file alone. Flagged rather than pre-decided.
checkpoint:
  stage: done                 # merged as ae343eb 2026-08-23; H2 accepted with a follow-up
  merged: ae343eb
  h2_note: "Accepted, AND the human asked for T-032 rather than choosing between accept and block. Reasoning: shipping starts it catching real drift now, while the unconverged finding rate (6 / 2 / 11 / 15 across three rounds -- it never fell) deserves an answer only live use can give. Both driver errors on this task were surfaced for overturn at the gate: the .gitignore override (caught by a security check, reverted) and the dual-path dispatch ruling (caught by the developer, deleted)."
  repo: cv-project (meta)
  branch: feat/board-validator
  worktree: none              # meta-repo change, and NOT merely by convention: the validator reads .claude/tasks/, so running it from a worktree would validate the WORKTREE'S snapshot of the board rather than the live one. Same family of error as T-028's build-context bug, one level up.
  pr:
  developer: infrastructure-engineer
  reviewers: ["/code-review", "quality-assurance (coverage lens)"]
  risk: normal
  env_slot: n/a               # no stack; this is a pure-Python check over files
  review_round: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-23
  h1_rulings:
    - "ALL THREE ENFORCEMENT POINTS, ratified by the human against the narrower options. (a) scripts/test-all.sh, matching T-028's precedent. (b) The /dev-loop driver runs it at every checkpoint write -- an adapter change, and the pointed one: ALL FOUR of the most recent incidents were driver edits, including the two the driver made hours after sweeping for that exact bug. (c) A settings.json hook firing on edits under .claude/tasks/, so drift is caught as it is written regardless of who writes it. Rationale for taking all three: the meta repo has NO CI (verified -- .github/workflows absent), so test-all.sh alone is a MANUAL gate and would not have caught the 2026-08-23 shadowing, since nobody ran it between the edit and the sweep."
    - "FIX THE BOARD IF A CHECK FIRES TODAY. Ratified over warn-only. The validator must exit 0 on the live 53 files or it is noise from day one and ignored by the second week. Anything it surfaces on the current board is real drift and is fixed in the same PR. If a finding turns out to be substantive enough to widen the PR materially, stop and escalate rather than absorbing it silently -- board rule 3 still applies."
    - "READ-ONLY, ALWAYS. It never reformats, reorders or rewrites frontmatter. These files carry DELIBERATE contradictions under the strike-don't-delete convention; a formatter would destroy the record that makes the drift findable."
    - "TWO EXEMPTIONS ARE BINDING, not oversights. (1) Do NOT require risk/security_review on the five deliberately-unrefined tasks (T-201, T-301, T-401, T-402, T-501) -- the 2026-08-17 sweep left them off reasoning that inventing values would 'manufacture ratified-looking decisions nobody made'. (2) Do NOT enforce acceptance-checkbox state; every done task has them unticked and the 2026-08-20 sweep ruled that CONVENTION, changeable only by a README protocol change."
    - "DUPLICATE-KEY DETECTION CANNOT BE DELEGATED TO A YAML PARSER. yaml.safe_load silently accepts duplicate keys and returns the LAST -- which is the very behaviour that made all four shadowing incidents invisible. Check 1 operates on raw lines regardless of what parses the rest."
    - "NARROWED ON EVIDENCE AT REVIEW ROUND 3 (max effort, human-requested second pass on board-check.py): the ruling above is right about the hazard and wrong about the remedy. yaml.safe_load() -- the LOADING api -- collapses duplicate keys to the last value; that is the failure mode and stays correctly forbidden for check 1. yaml.compose() -- the COMPOSING api, one stage earlier, returns the node TREE before any value construction -- does NOT collapse anything; every key/value pair survives with its own source line, duplicates intact. Verified against three of the shapes the hand-rolled raw-line scanner had missed across three review rounds (compact sequences, |2- chomping order, bare '- |' sequence items, quoted keys, hyphenated keys, flow mappings) at once: an 8000-document differential fuzz against a duplicate-aware loader found zero divergences between the scanner and compose() once the bare-'- |'-item bug was fixed. Check 1 is now DISPATCHED: yaml.compose() when PyYAML is available (the common case), the original raw-line scanner kept ONLY as the no-PyYAML fallback, narrower by construction and documented as such. Both HIGH findings from round 3 (the indented '---' fence truncation, the bare block-scalar sequence item) are independent bugs, fixed in the scanner regardless of this change, since the scanner still has to be correct for the fallback role."
    - "FURTHER NARROWED AT REVIEW ROUND 4 (max effort /code-review on the TEST FILE plus the PO's own probing of the compose() path, both never reviewed before): the dual-path dispatch from round 3 was ITSELF the round-4 HIGH's root cause -- `find_duplicate_keys` went to compose() whenever PyYAML was importable (every machine that runs test-all.sh), so every crafted duplicate-key fixture exercised ONLY that path and the fallback scanner's entire test suite was silently orphaned; simultaneously reverting all three round-3 scanner bug fixes left the suite green. Resolved by DELETING the fallback scanner entirely (and the checks-2-7 minimal top-level parser alongside it) and making PyYAML a HARD REQUIREMENT (sys.exit if absent), matching qa-env-override.py's own long-standing precedent in this same repo. There is now exactly ONE implementation of check 1 -- the orphaned-coverage bug class is structurally impossible with only one path to keep honest, and the entire 'compact sequence / chomping order / bare block-scalar item' bug family the scanner needed five rounds to close does not exist for a real YAML parser. The round-4 reviewer's OWN findings (compose() comparing raw scalar text instead of resolved (tag, value), producing false positives on `yes`/`1`/`~` vs their quoted forms; an alias node walked twice, double-reporting one real duplicate) are fixed in the sole remaining implementation and would have needed fixing regardless of the dispatch decision."
  enforcement_propagation: |
    HOW ENFORCEMENT ACTUALLY SHIPS, and the decision history behind it. Read the
    second half; the first half is a mistake worth not repeating.

      (a) scripts/test-all.sh          -- COMMITTED. Propagates with the repo.
      (b) /dev-loop driver invocation  -- documented in .claude/dev-loop-adapter.md,
                                          which is deliberately gitignored (it binds a
                                          checkout to an engine installed only in
                                          ~/.claude). Does NOT propagate; per-checkout.
      (c) PostToolUse hook             -- SCRIPT committed (scripts/board-check-hook.py);
                                          REGISTRATION is opt-in, per developer, in their
                                          own .claude/settings.local.json. Instructions in
                                          .claude/tasks/README.md. Does NOT auto-activate
                                          on clone, BY DESIGN.

    WHY (c) IS OPT-IN RATHER THAN COMMITTED. A hook registration in a tracked
    .claude/settings.json executes automatically on every Edit/Write for anyone who
    clones the repo, with no prompt. That makes scripts/board-check-hook.py a
    supply-chain surface: any later PR touching it would run on every collaborator's
    machine, turning ordinary code review into the last line of defence against RCE.
    settings.json is also a general config surface (permissions, env, model), so
    tracking it invites committing an allowlist later, which would silently widen what
    runs unprompted for everyone. Against that, the benefit on a SINGLE-DEVELOPER repo
    is zero: propagation only pays off with a second contributor, which is exactly when
    the risks land. Committing the script and leaving the registration opt-in gets the
    capability without the auto-execution.

    THE DECISION HISTORY, recorded because the process error matters more than the
    outcome. The driver first ruled -- ON ITS OWN AUTHORITY, with no human
    authorization -- that .gitignore should gain a narrow `!.claude/settings.json`
    exemption so the hook would propagate, and had it committed. The human had
    ratified "all three enforcement points" at H1; that authorized BUILDING the hook,
    not overriding a documented .gitignore policy to distribute it, and the driver
    noted at the time that it was a policy change and proceeded anyway.

    A security check flagged it. On review the human chose THIS arrangement instead:
    script committed, registration opt-in. The .gitignore exemption and the tracked
    settings.json were reverted before the branch was ever pushed.

    Two things to carry forward. First: "PO ruling" in this board's vocabulary means
    THE DRIVER DECIDED. It does not mean the human approved, and the original wording
    here did not distinguish them -- on a board whose entire pathology is facts
    inherited without re-checking, that ambiguity is the defect, not a style nit.
    Where a decision is the human's, this file now says so and gives the date.
    Second: H1's "regardless of who writes it" rationale for wanting all three points
    does not survive contact with a one-writer repo. It should have been challenged at
    H1 rather than used to justify a policy override afterwards.

---

## Goal

`.claude/tasks/` frontmatter is hand-edited YAML with **nothing checking it**. Every consistency property this board depends on is enforced by people remembering, and the record shows that failing repeatedly — including on the same day the failure was written down.

Build `scripts/board-check.py`, wire it into `scripts/test-all.sh`, and make the checks below executable.

## Why now — the evidence, not the argument

Twelve recorded violations, every one found by a human or agent re-reading rather than by anything downstream noticing:

| Date | What broke | Cost |
|---|---|---|
| 2026-08-13 | [T-002](T-002-jenkins-on-drone-host.md)'s board line read `in_review` while its file said `done` | **Five infra tasks read as un-claimable for four days** |
| 2026-08-17 | [T-011](T-011-budget-credit-alarm.md) `pr:` unfilled; [T-009](T-009-user-data-size-ceiling.md) missing the `pr:` key; [T-101](T-101-experience-resource.md) checkpoint `stage: pr` on a done task | drift |
| 2026-08-17 | `security_review` written as `required` in five files and `true` in others — two vocabularies for one boolean | ambiguity at the gate that reads it |
| 2026-08-20 | [T-019](T-019-ci-host-on-demand.md) merged but boarded `in_review` — **third recurrence** of the T-002 class | drift |
| 2026-08-20 | T-019's top-level `pr:` empty while `checkpoint.pr` held the URL | same bug as T-011, one task later |
| 2026-08-20 | `security_review` missing entirely from T-003, T-007, T-151 | gate reads nothing |
| 2026-08-22 | **[T-152](T-152-mysql-84-parity-cv-database.md): three `worktree:` keys in one mapping and a second, empty `pr:`.** YAML takes the last, so a close-out that *did* clear the worktree was **inert**, and the merged PR URL was shadowed by a blank | the generator refused on a closed task; the file read correct at the line the close-out edited |
| 2026-08-22 | [T-202](T-202-bff-public-routing-and-auth.md): a second `security_review:` holding `done` — a **third vocabulary**, and last, so it won | drift |
| 2026-08-22 | [T-101](T-101-experience-resource.md)/[T-102](T-102-education-resource.md): `checkpoint.worktree` never cleared at close-out | `qa-env-override.py` refused on both |
| **2026-08-23** | **[T-104](T-104-project-resource.md)/[T-151](T-151-dev-seeds-cv-sections.md): `review_round: 0` shadowing `review_round: 1`** — introduced **by the driver, hours after it swept for this exact bug**, with the write-up a few sections above in the same board file | both files read *"no review has happened"* for tasks whose review converged with findings applied |

**The last row is the argument.** The control was "be careful", it was written down in detail, and it failed within hours **for the person who wrote it**. That is not a discipline problem to be solved with more discipline.

Note the shape the failures share: **none was caught by something that depended on the value.** A shadowed `review_round` would tell a resumed session no review had happened; a shadowed `pr:` would send it looking for a PR that exists. Nothing complains. The board's own convention of striking rather than deleting is what makes these findable *afterwards* — it is not a check.

## The checks — each one maps to a row above

1. **Duplicate keys within a frontmatter mapping.** The single highest-value check: four incidents, and the one class that silently inverts a value rather than leaving it absent. Must handle nested mappings (`checkpoint:`) and must **not** false-positive on sequence items — `T-002` and `T-103` have repeated keys inside `-` list entries that are legitimately distinct mappings. A naive indent-based counter flags both; verified.
2. **Board row ↔ file agreement.** Every `T-NNN-*.md` has exactly one row in `TASKS.md` and vice versa, and the row's status equals the file's `status:`. This is the T-002 class, three recurrences.
3. **status/owner coherence.** `todo` must have no `owner:`; `in_progress`/`in_review`/`done` must have one.
4. **`checkpoint.worktree` cleared on closed tasks.** A `done` task declaring a filesystem path makes `qa-env-override.py` exit 1 for that task. The convention exists ([T-028](T-028-qa-env-generator-worktree-build-context.md)) and was violated twice.
5. **`pr:` present on `in_review`/`done`**, and consistent with `checkpoint.pr` when both exist. Covers T-011, T-009, T-019.
6. **`depends_on` resolves** — every id names a file that exists.
7. **Controlled vocabularies**: `status` in the lifecycle set; `security_review` a real boolean; `risk` in `trivial|low|normal|high`.

## What it must NOT do — this is where a validator turns into noise

- **Do not require `risk`/`security_review` on unrefined tasks.** The 2026-08-17 sweep *deliberately* left them off T-201, T-301, T-401, T-402 and T-501, reasoning that assigning them is a stage-0 refinement output and *"inventing values here would manufacture ratified-looking decisions nobody made."* A validator that demands them would push exactly that. Warn at most; do not fail.
- **Do not enforce acceptance-checkbox state.** Every `done` task on this board has its boxes unticked. The 2026-08-20 sweep looked at this and ruled it **convention, not drift**, and said making them load-bearing would be a protocol change to [README.md](README.md) rather than a board edit. Out of scope here.
- **Do not reformat, reorder or rewrite frontmatter.** Read-only. The strike-don't-delete convention means these files carry deliberate contradictions; a formatter would destroy the record.
- **Do not parse the body.** Prose drift is what sweeps are for.

## Decide at H1

1. **Where does it run, given the meta repo has NO CI?** `ls .github/workflows` → absent (recorded 2026-08-22 during T-016). So `test-all.sh` is a *manual* gate here, unlike every product repo. Candidates, not mutually exclusive: (a) `scripts/test-all.sh`, matching T-028's precedent; (b) a `PreToolUse`/`Stop` hook in `settings.json` so an edit to `.claude/tasks/` is checked as it happens; (c) the `/dev-loop` driver calls it at every checkpoint write, which is the moment the value is actually created. **(c) is where the last four incidents were born** — all four were driver edits.
2. **Fail or warn, per check.** It must exit 0 on the board **as it stands today**, or it is noise on day one and will be ignored by the second week. Run it against the current 53 files before choosing thresholds.
3. **Is a YAML library available, or does it hand-roll?** The existing `qa-env-override.py` parses frontmatter without PyYAML. Note that **`yaml.safe_load` silently accepts duplicate keys and returns the last** — so check 1 cannot be delegated to a parser and must operate on the raw lines either way.

## Acceptance criteria

- [ ] `python3 scripts/board-check.py` exits **0** on the board as it stands, and non-zero with a precise, actionable message when a check fails.
- [ ] Each of the seven checks has a test proving it **fails on a crafted bad fixture and passes on a good one** — confirmed red first, per this board's standing practice.
- [ ] **Regression fixtures reproduce the four real incidents**: T-152's triple `worktree:`, T-202's second `security_review:`, T-104's `review_round` shadowing, and a T-002-style board/file status mismatch. A validator that would not have caught the bugs that motivated it is not done.
- [ ] No false positive on sequence-item repeats (T-002, T-103) — assert explicitly against those two real files.
- [ ] Does not require `risk`/`security_review` on the five deliberately-unrefined tasks.
- [ ] Wired into `scripts/test-all.sh` alongside the T-028 generator tests.
- [ ] Output names the file, the key and the line for every finding.

## Definition of done

PR open from `feat/board-validator`, tests green via `./scripts/test-all.sh`, validator exits 0 on the live board, task updated. **Note there is no CI gate in this repo** — A1 and QA carry the whole weight, as recorded for every meta-repo task.

## Provenance

Filed 2026-08-23 from a housekeeping sweep that found the T-104/T-151 shadowing — the fourth instance of a bug the driver had itself swept for the previous day. Proposed at the end of that sweep and filed on the human's instruction.
