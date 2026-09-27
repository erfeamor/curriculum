---
id: T-032
title: "Re-review board-check.py after a week of real use — synthetic rounds found 34 defects and never converged"
repo: cv-project (meta)
status: todo
owner:
branch: chore/board-check-re-review
depends_on: [T-031]
risk: normal
security_review: false   # read-only tooling in the meta repo; no adapter §5 path. A1 re-checks against the real diff.
pr:
---

## Goal

[T-031](T-031-board-frontmatter-validator.md) shipped after **three review rounds and 34 findings**, which is the pipeline's maximum. Re-review `scripts/board-check.py` once it has run against **real board edits for at least a week**, on the explicit view — ratified by the human at T-031's H2, 2026-08-23 — that live use surfaces what synthetic rounds cannot.

**Do not start this before 2026-08-30.** Elapsed time carrying real edits *is* the input; running it early re-runs round 3 with a fourth reviewer and learns nothing new.

> **The thesis was vindicated within one day — 2026-08-24.** This task was filed on the argument that *live use surfaces what synthetic rounds cannot*. It did, before the task could start: real board edits produced **five dead links and four materially wrong titles in `TASKS.md`, with `board-check.py` reporting `clean` throughout**. Three review rounds and 34 synthetic findings had not touched that class. See the link-integrity section below; it is now part of this task's scope.
>
> **A tension worth naming, since the date rule above is load-bearing:** the link-integrity check needs **no** elapsed data and could be built today, while the re-review genuinely needs the week. They are bundled here because a check belongs with the tool's review and because filing it separately was the alternative the human declined. **If it is wanted sooner, it is cleanly separable** — it shares no code path with the review and its fixtures stand alone. Do not let the 2026-08-30 date become the reason a buildable check waits.

## Why this exists — the finding rate never fell

| Round | Scope | Findings |
|---|---|---|
| 1 · `/code-review high` | whole branch | 6 |
| stage-4 QA | behaviour + hook | 2 |
| 2 · `/code-review max` | `board-check.py` | 11 |
| 3 · `/code-review max` | **the test file** (never reviewed before) | 11 + 4 from the driver |

A falling rate would have argued convergence. **This one did not fall.** What changed instead was the *character*: round 3's findings were almost entirely fallout from round 2's fix — a dual-path dispatch the driver ruled for, which orphaned the fallback's entire test coverage and introduced three false positives. That path is now deleted, so the specific cause is gone; whether the *rate* was telling us something more general is the open question this task answers.

**The honest counter-argument, recorded so nobody re-litigates it from memory:** the code is now smaller than before that fix (966 → 740 lines), the fallback whose coverage was orphaned no longer exists, and 111 tests pass including four that read real historical incidents out of git. A green suite after removing the destabilising change is not the same as a green suite that never had one.

## What to actually look at — evidence, not another cold read

1. **Every finding it produced in the wild.** Was each one real? A false positive in check 1 is what T-031 itself calls *fatal to adoption* — the tool gets switched off, and then everyone believes the board is checked when it is not. **One confirmed false positive is a bigger result than ten true ones.**
2. **Every board defect it MISSED.** Diff the sweeps: run the checks a human sweep would have caught by eye against what the tool reported. Check 1 missed **seven** distinct YAML surface forms across T-031's three rounds. There is no reason to assume the eighth does not exist. **Two misses have since arrived on their own, both in checks other than check 1** — link integrity (check 2) and `pr:` presence being status-gated (check 5, found 2026-08-27). Both have their own sections and criteria below. **Neither discharges this item:** they were found by accident, and this asks for a deliberate hunt.
3. **Did anyone turn it off, work around it, or edit the board to silence it?** That is the adoption signal, and it is not visible from the code. Look for `--no-*` flags reached for, findings "fixed" by deleting the key rather than correcting it, and whether the opt-in hook is still registered in `settings.local.json`.
4. **The `/dev-loop` driver invocation.** Enforcement point (b) lives in the gitignored adapter and does **not** propagate. Did the driver actually run it at each checkpoint write? T-031's whole motivation is that *all four* of the most recent shadowing incidents were driver edits.
5. **Mutation-test the suite again.** Round 3's method — revert each fix, confirm a test dies — found 11 survivors that three prior passes missed. It is the highest-yield technique used on this task and it should be the first one reached for, not the last.

## The eighth blind spot has already been found: LINK INTEGRITY (added 2026-08-24, on the human's instruction)

**Item 2 above asks for "every board defect it MISSED" and predicts an eighth blind spot. One arrived before this task could even start, and it is not hypothetical — it was live on the board and the validator reported `clean` the whole time.**

### What happened

During the 2026-08-24 TASKS.md/HISTORY.md split, the driver rewrote the public-path deployment table and **invented five task filenames that do not exist**:

| Link written into TASKS.md | The file that actually exists | Title the driver invented | The real title |
|---|---|---|---|
| `T-015-bff-container-registry.md` | `T-015-docs-reflect-deployed-bff.md` | "Set up image registry and CD for the BFF" | *Correct the meta docs that claim the BFF is deployed* |
| `T-403-cloudfront-caching-for-bff-aggregate.md` | `T-403-public-vanilla-deploy.md` | "CloudFront: cache the BFF's aggregate endpoint" | *Public site (vanilla): deploy + point at the deployed BFF* |
| `T-203-auto-redeploy-on-domain-changes.md` | `T-203-bff-ci-deploy-stage.md` | "Auto-redeploy the BFF's public sites" | *BFF CI: push to ECR and roll the container on master* |
| `T-404-cloudfront-gateway-to-bff-aggregate.md` | `T-404-public-react-point-at-deployed-bff.md` | "CloudFront: `/cv` aggregate route" | *Public site (React): point Vercel's `BFF_URL` at the deployed BFF* |
| `T-204-validate-path-params-before-interpolation.md` | `T-204-bff-validate-person-id-param.md` | (close enough) | *BFF: validate the person id before the upstream call* |

**`board-check.py` reported `clean` on every run**, including the run in the same session that introduced it. It was caught by a hand-written shell loop (`for f in ...; do [ -f "$f" ] || echo MISSING; done`), not by the tool.

### Why it passed — the mechanism, which is the useful part

**Check 2 matches rows to files by task ID, never by the link target or the title.** `| [T-015](T-015-bff-container-registry.md) | Set up image registry… |` satisfies it perfectly: the row's ID is `T-015`, a file with `id: T-015` exists, one row each. The **href** and the **title** are unvalidated free text.

**This is the [T-028](T-028-qa-env-generator-worktree-build-context.md) shape one level up: a check that agrees with itself.** Board-check confirmed the ID column against the frontmatter and pronounced the board consistent, while the part a human actually clicks was broken and the part a human actually reads was wrong.

### Why it is worth a check rather than a note

**The board's entire correction mechanism is inter-file links.** Every sweep, every hand-off note, every superseded marker, and the whole 2026-08-24 review — whose central fix was *"write the warning into the file the implementer actually reads"* — depends on `[T-xxx](T-xxx-slug.md)` resolving. Task files cross-reference each other heavily. **A single `git mv` breaks every inbound link silently**, and nothing on this board would notice: not the tool, not CI (there is none in this repo), and not a reader who trusts a green `board-check`.

Note also that the wrong **titles** were the more dangerous half. A dead link fails loudly when clicked; a plausible-but-wrong title is read and believed. Three of the five above materially misdescribed what the task does, and the driver's own simplification analysis in that session **was reasoned from the invented titles** and reached a correct conclusion on false evidence. That is this board's signature failure, produced by the board's own summary of itself.

### The check to build

**Primary — link resolution.** Every markdown link matching `](T-\d+[^)]*\.md)` in `TASKS.md`, `HISTORY.md`, `README.md` and every `T-NNN-*.md` resolves to a file that exists in `.claude/tasks/`. Report file, line and the dead target. Cheap, deterministic, offline.

**Secondary — ID/target agreement.** A link whose visible text names one task while its target names another (`[T-015](T-014-….md)`) is unambiguously wrong and worth failing on. Note this catches a *different* bug from the primary check: that link resolves fine.

**MANDATORY: skip inline code spans and fenced blocks — learned by prototyping, 2026-08-24.** A throwaway version of this check was run against the live board before this section was written. It returned **three** findings:

- **One real dead link**, in `T-201`'s brand-new [T-204](T-204-bff-validate-person-id-param.md) cross-reference — written *in the same session*, using one of the invented filenames from the broken table, and not noticed by the driver or `board-check`. **The check caught a live defect within minutes of being imagined**, which is the strongest available argument for building it.
- **Two false positives — both inside backticks, both in this very file**, where the incident is documented using examples like `` `| [T-015](T-015-bff-container-registry.md) | … |` ``. Those are illustrations of broken links, deliberately quoted.

**This is not an edge case; it is the normal shape of this board.** The strike-don't-delete convention means files routinely quote wrong links to explain why they were wrong, and a check that fires on documentation *of* a defect would make every such write-up trip the validator. Per T-031's own finding that one confirmed false positive is *fatal to adoption*, code-span handling is a correctness requirement, not a refinement.

**Explicitly NOT in scope, and each for a reason:**
- **Do not validate link *text* against the target's `title:` frontmatter.** Board rows deliberately shorten and annotate titles (`done (**A1 + stage-4 QA + review**)`), and the strike-don't-delete convention leaves superseded titles in place on purpose. A title-equality check would fire constantly on correct content — and T-031 already establishes that a validator which cries wolf gets switched off, which is worse than not having it.
- **Do not check external URLs** (GitHub PR links, the Jenkins host). That needs the network, makes the validator non-deterministic and non-offline, and would fail on a private repo or a stopped CI host. `board-check.py` is read-only and offline; keep it that way.
- **Do not check anchors** (`#section`). Markdown headings churn constantly in these files and the failure is harmless.

**Fix the board if it fires today**, per T-031's H1 ruling 2 — but note the five links above were repaired on 2026-08-24, so the expected result on the current board is **zero findings**. If it finds more, that is a live defect and a second data point for this task's verdict.

**Scope note, since this adds a check to a re-review task:** T-031's seven checks all trace to a recorded incident, and this now has one. It is an acceptance criterion below rather than loose prose deliberately — the 2026-08-24 review found three hand-offs that lived in prose and were held by no task's criteria, and the fix for that is not to create a fourth. If the re-review's verdict turns out to be *"the approach is wrong"* (AC5's third option), split this into its own task rather than building it into something being retired.

## A blind spot in CHECK 5 — `pr:` presence is gated on status, found live 2026-08-27

**Not a variant of the link-integrity item above.** That is a blind spot in check 2 (row↔file matching); this is one in check 5 (`pr:` presence). The file's earlier "eighth blind spot" numbering counts duplicate-key surface forms in check 1 and does not extend cleanly to either — **do not try to number this one**; name the check it belongs to.

### What happened

During [T-201](T-201-bff-cv-aggregate.md)'s review round, `/code-review` found that the task carried `status: in_progress` with an **empty top-level `pr:`**, while the `checkpoint:` block in the same file recorded an open PR, `stage: review` and a CI-green result. Board `README.md` rule 6 and adapter §1 both require `status: in_review` and the URL in `pr:` the moment a PR opens.

**`board-check.py` reported `clean` throughout.** This is reproducible from git, not reconstructed: at commit `422fbeb` the frontmatter reads `status: in_progress` / `pr:` (empty) with `checkpoint.pr` populated, and that tree was validated clean in the same session that wrote it.

### Why it passed — and the detail that makes it worth fixing

`check_pr_present` returns early on the status:

```python
if status not in ("in_review", "done"):
    return findings                      # board-check.py:396
```

So the one state where a task can hold an open PR *without* announcing it — `in_progress` — is the one state never examined.

**The check already has everything it needs.** Twenty lines further down (`:418`) it reads `checkpoint.pr` and builds a hint from it. The data is gathered; only the status gate stops it being used. This is not a missing capability, it is an unreachable branch.

### Why it matters more than a tidy-up

It is the **same class as the link-integrity miss, one check over: the validator agrees with itself and pronounces the board consistent while the fields a reader actually consults disagree.** A resumed driver, or any agent following the protocol, reads the canonical `status`/`pr:` fields — not the `checkpoint:` blob — concludes no PR exists, and can open a duplicate. `TASKS.md`'s PR column stays blank for a task that has one. And the board's own resume protocol is built on the premise that `status` and `checkpoint` never disagree.

Worth noting what did catch it: a review agent reading the frontmatter, not the tool. Same three-part shape this task already records twice — **the driver introduced it, the validator missed it, and something outside the validator caught it.**

### The check to build

**A task whose `checkpoint.pr` holds a real PR URL must not have an empty or sentinel top-level `pr:`, at ANY status** — and if `status` is `in_progress` while `checkpoint.pr` is set, that is itself the finding, because board rule 6 says a task with an open PR is `in_review`. Report the file, the line and both values.

**Explicitly NOT in scope:**
- **Do not require `pr:` on a task with no `checkpoint.pr`.** A `todo` or `in_progress` task that genuinely has no PR is the normal case and must stay silent — firing there would be the cries-wolf failure T-031 calls fatal to adoption.
- **Do not widen the existing `done`-only `pr:` sentinel rule.** `pr: "none"` on a `done` task is deliberate (the T-010 case) and already handled.

### Acceptance criteria (added to the list below)

- [x] **A task with `checkpoint.pr` set and an empty or sentinel top-level `pr:` is reported, at any status** — with `in_progress` + a set `checkpoint.pr` called out as a board-rule-6 violation in its own right.
- [x] **A fixture reproduces the 2026-08-27 incident specifically** — `status: in_progress`, empty `pr:`, `checkpoint.pr` holding a URL — and is **confirmed red before the check exists**, per this board's standing practice. The real instance is recoverable from `git show 422fbeb:.claude/tasks/T-201-bff-cv-aggregate.md` rather than needing to be invented.
- [x] **A task with no `checkpoint.pr` and no `pr:` produces no finding at any status**, with a fixture — this is the false-positive guard, and it is the half that decides whether the check survives contact with the board.


## One passenger, added 2026-08-24 on the human's instruction

**[T-019](T-019-ci-host-on-demand.md)'s billing-week criterion should be read in this session.** It is the last thing standing between T-019 and a fully-ticked acceptance list, and it needs one Cost Explorer read. Its billing week (automation applied 2026-08-19) completes **2026-08-26** — before this session's earliest start on 08-30 — with real builds through the automation on 2026-08-20/21/22. *(A first draft of this note claimed the week had "already" elapsed on 08-24; it had not — corrected the same day, see T-019.)* This session is meta-repo, read-only and applies nothing, which is exactly the shape that can carry it.

**The check:** the measured daily rate across a window containing those build days is at or near **$0.6837/day**; a higher sustained rate means the reaper is not stopping the box after builds. Record it against [T-020](T-020-cost-model-correction.md)'s model — **not** T-010's, which is superseded — and tick the criterion on T-019.

**This is a passenger, not a dependency.** It does not gate this task's own verdict and must not shape it. If it turns up something interesting, file it; do not absorb it (board rule 3).

## Acceptance criteria

- [x] At least **7 days** of real board edits have elapsed since `ae343eb` (2026-08-23). *(35 days, as of this session 2026-09-27; 37 board-touching commits in that window.)*
- [x] Every finding the tool produced in that window is classified **true / false positive**, with the false positives reproduced. *(Zero false positives found — see Re-review section below. Nothing to reproduce; every finding in every sample was a true positive.)*
- [x] A deliberate attempt to find an **eighth duplicate-key** blind spot is made and its result recorded either way — "none found" is a valid and useful outcome, but only if it was actually looked for. **(Distinct from the link-integrity criteria below: that is a blind spot in a different check. Finding one does not discharge the hunt for the other.)** *(Six forms tried, `scripts/test_board_check.py::EighthDuplicateKeyBlindSpotHunt` — none found.)*
- [x] The mutation check is re-run and every mutant dies. *(23 mutations across new+existing checks; 1 survivor found and closed — see table below.)*
- [x] **Link integrity is checked** — every `](T-NNN-*.md)` target in `TASKS.md`, `HISTORY.md`, `README.md` and every task file resolves to a file that exists. Offline, deterministic; no external URLs, no anchors.
- [x] **ID/target agreement is checked** — a link whose visible text names one task and whose target names another fails. This is a *different* defect from a dead link and needs its own fixture; the link in question resolves.
- [x] **Regression fixtures reproduce the 2026-08-24 incident specifically** — a row linking `T-015` to a non-existent `T-015-bff-container-registry.md`, and a row linking `[T-015]` to an existing `T-014-*.md`. Both must be confirmed **red before the check exists**, per this board's standing practice and T-031's own precedent of reproducing the four real shadowing incidents.
- [x] **Links inside inline code spans and fenced blocks are skipped**, with a fixture proving it — this file quotes broken links on purpose to document them, and a prototype produced **two false positives here** before this rule was added. T-031 calls one confirmed false positive fatal to adoption.
- [x] **The new check does not fire on the current board** — the five real dead links and the one in T-201 were repaired on 2026-08-24, so the expected result is zero. Anything it finds is live drift: fix it in the same PR (T-031 H1 ruling 2) and record it as a second data point for the verdict. *(Confirmed zero on the current board — no live drift to fix in this branch. See Re-review section for a SECOND incident the check independently confirmed against git history: 4 more dead links, 2026-09-25, `9767706`.)*
- [x] **No title-equality check was added**, and the reason is recorded. Board rows deliberately shorten and annotate titles, and strike-don't-delete leaves superseded ones in place — a title check would fire on correct content, and a validator that cries wolf gets switched off. *(Recorded in `check_link_integrity`'s own section comment in `scripts/board-check.py` and reaffirmed in the Re-review section below.)*
- [x] A written verdict: **converged**, **needs another round**, or **the approach is wrong**. The third is a real option and must not be excluded by sunk cost. *(Converged — see Re-review section.)*

## Re-review — 2026-09-27

**Phase A (build).** `a2bdb9c` adds check 8 (link integrity: resolution + ID/target agreement, both offline, code-span/fence-aware) and widens check 5 (`pr:` presence) to any status once `checkpoint.pr` already holds a real value. Every RED-FIRST case named in the binding test plan (dead link, ID/target mismatch, scan coverage across all four surfaces, the `422fbeb`/T-201 regression, the `in_progress` widening) was confirmed failing before the corresponding check existed. `python3 scripts/board-check.py` on this branch's board produces **zero link findings** — the five dead links + T-204 cross-reference from 2026-08-24 stay fixed; there is no live drift in this repo state, so nothing needed fixing in the same PR. 125 tests green at the end of phase A.

**Phase B (re-review).**

### 1. Mutation re-run (item 13)

Script: `/tmp/.../scratchpad/mutate.py` (scratchpad only, not shipped) — reverts one guard at a time across both pre-existing checks (1–7) and the two new/widened ones (5, 8), runs the full suite, restores the file exactly, records KILLED/SURVIVOR.

| # | Mutation | Result |
|---|---|---|
| m01 | check 1: drop `.tag` from the duplicate-key identity | KILLED |
| m02 | check 1: invert the `seen` membership test | KILLED |
| m03 | check 1: remove the `visited`-node de-dup guard | KILLED |
| m04 | `read_frontmatter`: OPENING fence `.rstrip()` → `.strip()` | **SURVIVOR → fixed** |
| m05 | `read_frontmatter`: CLOSING fence `.rstrip()` → `.strip()` | KILLED |
| m06 | check 3: `todo and owner` → `todo or owner` | KILLED |
| m07 | check 3: invert the `elif` owner-required branch | KILLED |
| m08 | check 4: `status != "done"` → `== "done"` | KILLED |
| m09 | check 4: invert the worktree-sentinel test | KILLED |
| m10 | check 5: revert the widened status gate | KILLED |
| m11 | check 5: `pr_text == "" or is_sentinel` → `and` | KILLED |
| m12 | check 5: remove the `done`+sentinel early return | KILLED |
| m13 | check 5: invert the `checkpoint.pr` disagreement test | KILLED |
| m14 | check 6: invert `dep_id not in known_ids` | KILLED |
| m15 | check 7: invert `status not in STATUS_VALUES` | KILLED |
| m16 | check 7: invert the `UNREFINED_EXEMPT` membership test | KILLED |
| m17 | check 2: invert the board/file status-agreement test | KILLED |
| m18 | check 2: invert the malformed-row column-count test | KILLED |
| m19 | check 8: invert the dead-link existence test | KILLED |
| m20 | check 8: invert the ID/target-agreement test | KILLED |
| m21 | check 8: disable the fence toggle | KILLED |
| m22 | check 8: disable the code-span strip | KILLED |
| m23 | `run()`: id-collision `len(paths) > 1` → `>= 1` | KILLED |

**23 mutations, 22 killed on the first pass, 1 survivor (m04).** m04 was not a functional defect — `.rstrip()` genuinely ships in the code — it was a coverage gap: nothing exercised an indented **opening** fence, the mirror image of round 3's real closing-fence bug. Closed with a direct `read_frontmatter()` regression test (commit `8391b09`, test-only, no `board-check.py` change). Re-ran after the fix: **23/23 killed, 0 survivors.**

### 2. In-the-wild findings, classified (item 14)

Searched `git log -p ae343eb..HEAD -- .claude/tasks/ scripts/` for every mention of `board-check`, `false positive`, `--no-`, "silenced" (37 board-touching commits in the window). Every finding found is a **true positive**; none is a false positive:

- **`b03664d` (2026-08-26).** *"The opt-in `board-check` hook earned its keep three times in one session, catching a task file with no board row, and twice catching a file/board status disagreement... including the `checkpoint.worktree` clear at close-out."* Three true positives: check 2 (missing board row), check 2 (status disagreement) ×2, one of which is check 4's worktree-clear rule. Same session also confirms the hook is registered and used (see adoption, below).
- **`422fbeb` (2026-08-27), T-201.** The already-documented `pr:`-gating miss this task exists to fix. Confirmed live (not reconstructed): `git show 422fbeb:.claude/tasks/T-201-bff-cv-aggregate.md` — `status: in_progress`, empty `pr:`, `checkpoint.pr` set. The OLD tool reported clean (a false *negative*, not a false positive — it produced no finding at all). The widened check now reports it, and current live T-201 (`done`, `pr:` set) is silent. Fixture: `PrPresence422fbebRegression`.
- **`218b9dc` (2026-08-24), the "fifth sweep."** Already documented in this file's own provenance: five invented filenames + the T-201→T-204 cross-reference, caught by a hand shell loop, not the tool — another false negative of the pre-check-8 tool, now closed by check 8.
- **`9767706` (2026-09-26), a SECOND, previously undocumented instance of the same class**, found in this session by running check 8 against `9767706`'s parent (`4b77edb`, 2026-09-25): **4 more real dead links**, all `T-013-bff-public-edge-path.md` (T-013's file was since renamed to `T-013-contract-bff-public-routing.md`; 3 references in `T-210-bff-domain-types-null-not-absent.md`, 1 in `T-405-public-react-null-optionals.md`). Commit message confirms: *"4 dead links to T-013 fixed (T-210, T-405)."* board-check (pre-check-8) reported clean throughout this incident too — a second real-world confirmation that link rot recurs and check 8 catches it, not a synthetic worry.
- **No confirmed false positive anywhere in the window.** No `--no-*` flag exists on this tool's CLI at all (only `--tasks-dir`/`--quiet`), so there is no escape hatch to even reach for. No commit deletes a flagged key to silence a finding rather than correcting it — every fix found (T-201's `pr:`, T-210/T-405's links, T-409's missing `pr:` key) sets the field to a *correct* value, never removes it.

### 3. Eighth duplicate-key blind-spot hunt (item 15)

`scripts/test_board_check.py::EighthDuplicateKeyBlindSpotHunt`, six forms, one fixture each:

| Form | Result |
|---|---|
| Tabs vs spaces (indentation) | YAML forbids tabs in block indentation; `compose()` raises, `find_duplicate_keys` returns `[]` by design, but `parse_frontmatter_dict`'s own `yaml.safe_load` ALSO raises — a loud parse-error finding, never a silent clean. Not a blind spot. |
| Quoted vs bare keys | Already caught (pre-existing coverage, re-confirmed). |
| Anchors/aliases used AS a key (`*k` resolving to `status`, colliding with a literal `status:`) | Caught — `compose()` resolves the alias's tag/value through to the key identity check. Not a blind spot. |
| Merge keys (`<<: *a` / `<<: *b` twice in one mapping) | Caught — both `<<:` occurrences share the merge tag, so the identity check flags the literal duplicate marker itself. Not a blind spot. |
| Flow-mapping duplicates | Already caught (pre-existing coverage, re-confirmed). |
| Comment-adjacent keys (trailing `# status: ...` comment; comment-only line matching a key) | No effect — comments are stripped before `compose()` ever sees the text; empirically confirmed both shapes parse to only the real keys. Not a blind spot. |

**Result: none found, having actually tried all six.** Tabs-vs-spaces is the only form that changes behaviour at all, and it changes it to a correct loud error, not a silent clean.

### 4. Adoption signals (item 16)

- **Hook registration**: `.claude/settings.json` (gitignored, per T-031 H2's ruling — script committed, registration opt-in, never distributed) is present and correctly configured in the working checkout, registering `board-check-hook.py` on `PostToolUse` for `Edit|Write|MultiEdit`.
- **Actual use, not just registration**: `b03664d` records the hook firing and catching three real defects in one session (above).
- **No `--no-*` reached for**: the CLI has no such flag to reach for (`--tasks-dir`, `--quiet` only).
- **No key deleted to silence a finding**: every real incident found in the window was closed by *correcting* the flagged field, never by removing it (T-201's `pr:`, T-210/T-405's links, T-409's missing `pr:` key — see item 14).

### 5. Driver invocation sampling (item 17)

Ran the **contemporaneous** `scripts/board-check.py` (as it existed at each commit, via `git archive`) against that commit's own `.claude/tasks/` tree, for 3 checkpoint-write commits:

| Commit | Date | Result |
|---|---|---|
| `7618ec0` ("checkpoint T-026 at stage 4") | 2026-08-26 | clean — genuinely clean at that time (T-201 was still in that version's `UNREFINED_EXEMPT`, correctly). |
| `422fbeb` ("T-201 at review round 1") | 2026-08-27 | clean — but **wrongly** clean: this is the exact `pr:`-gating incident, reported clean only because that version's check 5 never examined `in_progress`. |
| `533cfa1` ("T-207 ... PARKED at review") | 2026-08-27 | clean — genuinely clean. |

The driver's board-check invocation ran and matched the historical record at all three; one of the three is the known miss, now fixed.

### 6. False-positive sweep (item 18)

10 board snapshots via `git archive` + **today's** `board-check.py` (to test the checks this task adds/widens against real historical data), 5 checkpoint-write-style + 5 merge/close-style, spanning 2026-08-26 to 2026-09-27: `7618ec0`, `8825d96`, `422fbeb`, `533cfa1`, `a78e953` (checkpoint-write); `725ec8b`, `c7c7c79`, `c54d324`, `9767706`, `52aaeb4` (merge/close).

Filtered to this task's own checks (`key` in `link`, `link-id`, `pr`): **1 finding across all 10 snapshots — `422fbeb`'s `pr` finding, a confirmed true positive** (item 14). The other 9 snapshots: zero. **False-positive rate: 0/10 snapshots, 0 false positives.**

(4 of the 10 snapshots also show `risk`/`security_review`-missing findings on T-201 from **check 7**, pre-dating this task — these are an artifact of replaying *today's* `UNREFINED_EXEMPT` set, which no longer includes T-201, against board state from *before* T-201's 2026-08-27 refinement, when the contemporaneous script legitimately exempted it (`git show 7618ec0:scripts/board-check.py` confirms `T-201` was in that version's set). Not a tool defect, not in this task's scope, and not counted in the rate above — flagged here only so the number isn't misread.)

### 7. Verdict — **converged**

Reasoning: round 3's mutation pass found 11 real survivors; this re-run of the same method against a larger surface (7 pre-existing checks plus the 2 new/widened ones, 23 targeted mutations) found exactly **1**, and it was a test-coverage gap, not a functional defect. The tool has run against 35 days and 37 commits of real, unscripted board editing and produced **zero confirmed false positives** — the failure mode T-031 calls fatal to adoption never happened. The two blind spots that *were* found live (link integrity, `pr:` status-gating) each mapped cleanly onto exactly this project's existing structure — one narrow check, one incident, fixtures reproducing the real commit — with no architectural strain, and a *second*, independent real-world dead-link incident (`9767706`) confirms the new check's value against data it was never tuned to. The eighth-blind-spot hunt (six deliberately chosen forms) found nothing, and the one form that behaves differently (tabs) fails loudly rather than silently. The adoption signal is positive: the hook is registered, actually used, and every real incident found was fixed forward, never silenced. Weighed against "the approach is wrong" deliberately, not by default: nothing here suggests the incident-per-check structure is straining — the opposite, it kept absorbing new incidents (T-032 itself is the third round of that) without needing to change shape. **Converged** is the answer this evidence supports, not the one sunk cost would prefer.

PR open from `chore/board-check-re-review` with the verdict recorded on this task, or — if nothing is found — this task closed with the evidence that nothing was found. **Note there is no CI in this repo**; A1 and QA carry the whole weight.

## Provenance

**Link-integrity scope added 2026-08-24 on the human's instruction**, after the board split introduced five dead links and four wrong titles that `board-check.py` passed as clean. Worth recording precisely, because the shape matters more than the incident: **the driver introduced the defect, the validator missed it, and a hand-written shell loop caught it** — the same three-part pattern as the T-104/T-151 shadowing that motivated [T-031](T-031-board-frontmatter-validator.md) in the first place, one check-class over.

Filed 2026-08-23 at T-031's H2 gate. The human accepted the merge **and** asked for this, rather than choosing between accepting and blocking — the reasoning being that shipping it starts it catching real drift immediately, while the unconverged finding rate still deserves an answer that only live use can give.
