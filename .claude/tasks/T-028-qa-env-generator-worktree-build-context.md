---
id: T-028
title: "The QA stack builds master, not the worktree under test"
repo: cv-project (meta)
status: done
owner: infrastructure-engineer
branch: fix/qa-env-worktree-build-context
pr: https://github.com/erfeamor/curriculum/pull/49
depends_on: []
risk: normal          # small diff, but it fails in the direction of a FALSE PASS
security_review: false   # no adapter §5 security path — local tooling only
checkpoint:
  stage: done
  merged: "2026-08-21 as 74be2c8 (squash, PR #49). Five commits, scripts/ only. H2 accepted. 33 tests wired into scripts/test-all.sh."
  stage1: |
    Implemented 2026-08-21 on fix/qa-env-worktree-build-context, commit 1a2629a.
    scripts/qa-env-override.py ONLY (+217/-4); the uncommitted .claude/tasks/ board
    edits were left untouched as instructed, verified by the driver.
    G1-G6 all pass. Driver independently re-ran G3 (exit 0, loud "no service
    repointed: task repo 'cv-infra' is not built by...") and G4 (exit 1, refuses to
    fall back). I1 ACCEPTANCE TEST PASSED WITH ITS NEGATIVE CONTROL:
      worktree stack  -> "headline":"T-028-WORKTREE-PROBE Full-Stack Engineer"
      control stack   -> "headline":"Full-Stack Engineer"
    Same compose, same generator; the build context alone decides which code answers.
    That pair is the proof -- the positive alone would not have been.
    I2 labels present on the repointed image and ABSENT on the control, so absence is
    itself a signal. Stacks torn down, volumes/networks/images/worktrees all verified
    gone by both the developer and the driver.
  stage1_developer_amendments: |
    Five deviations from the PO-authored provisional plan, all argued and all accepted
    by the PO -- this is why the plan was marked provisional:
      1. G2-vs-ruling-3 CONFLICT, resolved in the ruling's favour: the generated YAML
         is byte-identical to before (proved by diff), but stdout gains one
         "no service repointed" line. A silent no-worktree run is HOW THIS DEFECT
         SURVIVED. QA to ratify the amended wording.
      2. Added a `dirty` label beyond task/branch/SHA. I1 itself is the argument: the
         probe worktree was dirty, so the SHA alone described an image that never
         existed. A SHA that silently lies is the same failure class as a path that
         silently lies.
      3. Added --worktree-root instead of hard-coding $HOME/work.
      4. branch "HEAD" -> "(detached)"; HEAD-as-a-branch-label is misinformation.
      5. A non-git or origin-less --worktree is a HARD ERROR, not a fallback.
    It also flagged that this task's OWN acceptance criterion ("verified by a bring-up
    whose service reports code only present on the branch") encodes the ADDITIVE tell
    that T-103 got lucky with, and contradicts the modifying-task criterion directly
    below it. That is the third acceptance criterion this week found to be wrong by the
    person implementing against it (after T-103's @Transactional one). Reword at review.
  stage1_not_done: |
    Scope item 4 (cross-reference from the adapter's §6) was DECLINED by the developer
    on the grounds that .claude/dev-loop-adapter.md is gitignored LOCAL CONFIG and an
    agent should not edit a human's config on instruction. The PO agrees. It stays
    open and belongs to the human; the generator's printed build:/prov: lines are
    self-documenting in the meantime.
  budget_stop: |
    STOPPED HERE DELIBERATELY at 86.8% of ceiling_turns (SOFT, approaching HARD).
    Stage 1 is COMPLETE and verified; stage 2 (review) is NOT started -- the engine's
    rule is that a stage which has barely started stops where it is, and a review round
    that runs out mid-flight is an abandoned round, not a thorough one.
    RESUME AT: stage 2. Branch fix/qa-env-worktree-build-context, commit 1a2629a,
    local only, NOT pushed and NO PR. Reviewers: /code-review + QA ratification of the
    provisional plan (the ratification is itself a gate, see budget_note).
  h1: "APPROVED by the human 2026-08-21 with 'approve and push on' — six rulings and the PO-authored provisional test plan accepted as written, no scope change. The human was told the budget read SOFT (325/400, 81.2%) and that pushing on risks a mid-stage stop; they chose to proceed. Recorded because the budget guidance says do not start a stage on SOFT, and this start was a deliberate human override of that rule, not an oversight."
  repo: cv-project (meta)
  branch: fix/qa-env-worktree-build-context
  worktree: none      # meta-repo tooling change; no worktree needed and using one would be self-referential
  developer: infrastructure-engineer
  reviewers: [code-review, quality-assurance]
  risk: normal
  security_review: false
  review_round: 3
  qa_bounces: 1
  stage4: |
    2026-08-21, live Docker + real git worktrees, branch @ 0b512f3. All five items
    PASS; ONE low-medium defect bounced (below).
      1. I1 IN THE BARE FORM -- QA's own ratification gap, now closed by execution.
         Worktree at the LITERAL conventional path, invoked --task/--slot with NO
         --worktree flag: the modifying change was served
         ("T-028-I1-BARE Full-Stack Engineer") and the negative control returned
         master's value with ZERO dev-loop labels. The path every real pipeline
         invocation uses is now proven, not just the explicit-flag path G1 covered.
      2. I2b: response T-028-I1-BARE -> -V2 AND labels commit 1327bf6/dirty=true ->
         f0e40c8/dirty=false. Both moved together; no stale layer.
      3. BIND MOUNT (T-151's shape), evidence captured WHILE UP:
           worktree .Mounts Source = .../T-028-BIND-PROBE/sql
           control  .Mounts Source = .../curriculum/cv-database/sql
         Behavioural confirmation: SELECT on cv.skill returned 'T-028-BIND-PROBE'
         vs master's 'Terraform', with Flyway logs proving the seed callback ran in
         both (not skipped).
      4. Three board states on the LIVE board: T-102 (declares a path, directory
         absent) -> exit 1; T-103 (worktree: none) -> exit 0 silent; unknown task ->
         exit 0.
      5. Guard probes: branch mismatch against the main checkout -> exit 1, refused;
         with --no-branch-check -> proceeds but still prints the MAIN CHECKOUT
         warning, exactly as the round-1 correction designed.
    NO CASE FOUND where the tool reports success while the stack runs the wrong
    code -- the only failure class that matters here.
  stage4_contrast_test: |
    The driver asked QA to disprove a specific self-consistency risk: T-103 now exits
    0 where it exited 1 an hour earlier, after the driver cleared its
    checkpoint.worktree. That is indistinguishable from the check having silently
    stopped working. QA ran the identical invocation against a SCRATCH COPY of T-103's
    board file with the old worktree path restored, same missing-directory condition
    -> exit 1, same message as T-102. Same code, same task id, same missing worktree;
    only the board content differs and the exit code follows it.
    THE CHECK WORKS; THE BOARD CHANGED. Recorded because "the signal agrees with
    itself" is this task's entire subject, and the driver's own board edit was the
    most likely place for it to recur.
  stage4_defect_bounced: |
    LOW-MEDIUM, bounced 2026-08-21 (attempt 1 of 2). WorktreeError raised by
    rewrite_mount_source (:245) reaches the user as a RAW PYTHON TRACEBACK, because
    match_mount_services is called at :625, outside the try/except at :587-591 which
    only wraps resolve_worktree/repo_identity.
    NOT a false pass: exit 1, no override written, no stack comes up on an empty
    directory. It is a consistency defect against the tool's own bar -- the
    WorktreeError docstring and ruling 3 both demand loud AND ACTIONABLE, and a
    traceback is loud but not actionable. The unasked guard doesn't get to speak in
    its own voice.
    None of the 32 tests covered this path, which is why it reached stage 4. The new
    test must assert the MESSAGE SHAPE (stderr starts "qa-env-override: ", does not
    contain "Traceback"), because asserting exit 1 alone passes against the defect.
  standing_limitation_for_the_board: |
    MOUNT PROVENANCE IS STRUCTURALLY WEAKER THAN BUILD-LABEL PROVENANCE, and QA's
    stage-4 verdict is that the board should carry this permanently rather than let
    it read as uniformly fixed.
    Build labels are an image property and survive teardown. A bind mount leaves no
    such trace: the only evidence is docker inspect .Mounts, which exists ONLY while
    the stack is up and cannot be reconstructed afterwards. It therefore depends on
    QA remembering to capture during the run rather than on the tool guaranteeing
    later checkability.
    QA'S RULE, adopted: for any bind-mount-only task (cv-database, cv-observability)
    sign-off requires BOTH the .Mounts capture AND an independent BEHAVIOURAL check
    (the actual seeded row). The pairing is the proof; the mount inspection alone is
    not. Applies to T-151 first.
  review_round_3: |
    2026-08-21, commit 0b512f3. The board's checkpoint.worktree now makes a repoint
    MANDATORY, which is what actually closes F5 -- --require-worktree alone was
    unreachable from the pipeline's real command line (--task --slot, adapter
    gitignored). 32 tests, run by the driver (1.672s, OK). Three states verified
    against the LIVE board, not fixtures:
      declared path + nothing repointed -> exit 1, naming the board file, the
        declared path and the consequence. Demonstrated on T-103, a genuinely
        failing real case.
      worktree: none (T-014/T-018/T-019/T-028) -> exit 0, silent. A real
        configuration, not an omission.
      no board entry at all -> exit 0.
    Coverage deliberately includes the states that must NOT fail: `none` with a
    trailing comment (every live one has one), a board entry with branch: but no
    checkpoint key, checkpoint present without worktree, checkpoint as a scalar,
    and no board file.
  po_rulings_on_round_3: |
    1. SILENCE over a warning for the no-board-entry case: ACCEPTED, and the
       developer's argument is better than my instruction. I allowed "warn at most";
       it chose silence because a warning firing on a correct, common invocation
       (every ad-hoc probe run) is how people learn to skim warnings -- which would
       directly degrade the finding-1 mount-exposure warnings, the ones that MUST be
       read. Ruling: silence stands. A warning channel is only worth having while it
       is still worth reading.
    2. DECLARED path vs RESOLVED path is NOT compared (checkpoint.worktree: /A plus
       --worktree /B passes, because a repoint happened). Accepted as a deliberate
       gap: comparing invites false failures (~ expansion, relative forms, a worktree
       legitimately moved mid-task) and the branch check already catches the case
       that hurts -- /B being on the wrong branch.
    3. BOARD HYGIENE IS NOW LOAD-BEARING. A closed task that still declares
       checkpoint.worktree makes every later bring-up for it exit 1. That is the
       right default -- loud and overridable with --no-worktree-check -- but it means
       "clear checkpoint.worktree at close-out" stopped being tidiness and became a
       convention with a tool depending on it. T-103's entry cleared accordingly; the
       convention is recorded in the board sync.
  review_round_2: |
    2026-08-21. All six findings addressed; 3 commits (1a2629a, 7399277, 67e7286),
    scripts/ only, board edits untouched -- verified by the driver.
    F1: took the FULL bind-mount fix rather than the minimum wording change.
      rewrite_mount_source/match_mount_services walk volumes: in both forms and
      rebase only the host side; named volumes, unrelated mounts, container paths
      and :ro pass through. ${VAR} sources are NOT guessed -- skipped and reported
      as an exposure. Proven end to end on T-151's exact failure shape: a
      cv-database worktree with a renamed seed produced "T-028-DB-PROBE" from the
      worktree while the control produced master's "Terraform".
      UNASKED GUARD, and the best thing in the round: a rewritten mount source that
      does not exist in the worktree is now FATAL, because Docker creates a missing
      bind source as an empty root-owned directory -- a repointed-but-empty
      /flyway/sql would come up healthy with no migrations. Same false pass, one
      layer down, found by the developer looking rather than by review.
    F2: took BOTH mechanisms -- --expect-branch as override, the board's frontmatter
      branch: as the DEFAULT, --no-branch-check to opt out. Its argument is the
      thesis of the whole task: the flag alone reproduces the hole, because the
      adapter's documented invocation passes no flags and the adapter is gitignored.
    F3: closed, WITH A CORRECTION TO THE FINDING (see stage1_correction below).
    F4: note emitted into the file header in all three branches. Kills plan row G2
      by design; row struck rather than reconciled.
    F5: --require-worktree added -- but see round 3, the flag alone is unreachable
      from the pipeline's real command line.
    F6: scripts/test_qa_env_override.py, 24 tests, RUN BY THE DRIVER not just
      reported (0.951s, OK), wired into scripts/test-all.sh. Includes named
      regressions for finding 1 (cv-database->flyway, cv-observability->grafana)
      and an assertion against the LIVE compose file, so a service rename or a
      context move fails a test -- which is what stops this silent defect returning.
    I1/I2/I2b/I3 all re-run because the resolution path changed. I2b holds: across
      a rebuild in the same project the response changed AND the label changed
      (dirty false->true). Note the mechanism -- a commit-only label would have been
      byte-identical across a build serving different code, which is exactly the
      job QA ratified the `dirty` label for.
  stage1_correction: |
    FINDING 3 WAS PARTLY MISATTRIBUTED, corrected by the developer and accepted.
    `git rev-parse --show-toplevel` catches --worktree "" and a SUBDIRECTORY, but it
    does NOT catch --worktree ~/work/curriculum/cv-domain-service, because the main
    product checkout IS a valid work-tree root. Only finding 2's branch check catches
    that, plus a non-fatal MAIN CHECKOUT warning the developer added that fires even
    under --no-branch-check.
    Recorded prominently because an inherited belief that a guard covers a case it
    does not is precisely how T-101's client-supplied-id hole survived three weeks in
    master behind a green test.
  accepted_gaps_recorded_for_qa: |
    - MOUNT PROVENANCE IS NOT LABEL-PROVABLE. Build labels are an image property; a
      bind mount leaves no such trace, so its provenance is
      docker inspect --format '{{json .Mounts}}' <proj>-<svc>-1, checkable ONLY WHILE
      THE STACK IS UP. A cv-database task's provenance evidence is therefore
      structurally weaker than a Java task's and QA must capture it DURING the run,
      not after. No fix inside this tool.
    - A --task/--worktree mismatch is visible in the labels but only guarded by the
      branch check. QA checked and rejected a "branch contains task id" heuristic --
      correctly: this task's own branch contains no "T-028".
  review_round_1: |
    Two reviewers, 2026-08-21. THE HEADLINE IS THAT THIS TASK'S OWN MODEL WAS
    INCOMPLETE -- a PO ruling error, found by review, on a repo the task names.
    /code-review (high): 3 medium + 4 low/medium.
      F1 BLOCKING: "zero matches is legitimate" (DoR ruling 3) is FALSE for
        bind-mounted repos. flyway bind-mounts ./cv-database/sql and grafana
        ./cv-observability/grafana/provisioning FROM THE MAIN CHECKOUT, and neither
        is a build context, so match_build_services can never see them. T-151 --
        cross-linked in this task's own acceptance criteria -- would seed from
        master's SQL while the generator printed "no service repointed", which
        READS AS REASSURANCE. The exact silent false pass T-028 exists to kill,
        surviving the fix, with comforting output.
      F2 BLOCKING: the resolved branch is recorded but never checked. A worktree
        sitting on master resolves, repoints, stamps branch: master, and QA's
        docker inspect provenance check SUCCEEDS. Ruling 5's check is
        self-consistent, not corroborating.
      F3 BLOCKING: the --worktree guard is is_dir() only. --worktree "" resolves to
        CWD; and git -C <subdir> walks UP, so the main product checkout passes the
        guard and gets labelled as the tree under test.
      F4: the ruling-3 note is persisted only in the repointed case, so the artifact
        cannot distinguish "considered and found nothing" from "predates the fix".
      F5: add --require-worktree; the adapter's documented invocation passes no
        worktree flag, so the only guard is an unenforced directory convention.
      F6: 217 lines, no automated tests, against this workspace's TDD rule. Worse
        than usual because the defect is SILENT -- a later compose edit reintroduces
        it with nothing failing.
      F7: the board row said "H1 pending" while the file recorded H1 approved.
        Same drift class as the sweep three commits earlier. Fixed by the driver.
    quality-assurance (plan ratification -- it was ratifying a PO-WRITTEN plan,
    which is itself the deviation recorded in budget_note): RATIFIED WITH THREE
    AMENDMENTS, ready for stage 3 conditional on recording them.
      - No row covered CONVENTIONAL-PATH-PRESENT, the branch the real pipeline
        actually uses (G1 = explicit flag, G2 = conventional absent). Driver ran it
        by hand: resolves correctly. Missing test, not missing behaviour.
      - New I2b: rebuild-after-mutation, asserting the labels CHANGE. Nothing proved
        a cached layer isn't serving old code under a fresh label.
      - G2 wording split: generated YAML byte-identical, stdout gains one line.
      - It AGREED this task's AC1 is wrong (see below) and proposed replacement text.
      - It raised F2 independently and recommended accepting it as a gap, having
        checked and rejected "branch name contains task id" as a heuristic --
        correctly, since THIS task's branch contains no "T-028". It was right about
        the heuristic and wrong about the conclusion: an EXACT check exists, because
        every board item declares its branch in frontmatter.
  env_slot: 0
  budget_note: |
    Refined at 81.2% of ceiling_turns (SOFT). Stage 0 was done by the PO INLINE and
    the test plan below is PO-AUTHORED, which is a deliberate deviation from the
    engine's "spawn QA to write the plan it will later run". Recorded as a deviation
    rather than passed off as normal: at SOFT the choice was a PO-written plan or no
    start at all. QA MUST ratify or amend this plan before stage 4 executes it, and
    the ratification is itself a gate -- a plan authored by the person who wants the
    task to pass is exactly the arrangement the split exists to prevent.
  updated: 2026-08-21
---

## The defect

`docker-compose.dev.yml:50` builds the domain service from a **fixed relative path**:

```yaml
  domain-service:
    build: ./cv-domain-service
```

`./cv-domain-service` is the **main checkout**, which sits on `master`. But the dev-loop runs every task on a **git worktree** under `~/work/cvdl-worktrees/<task-id>`. So the documented stage-4 bring-up — the exact command the adapter's §6 prints — builds `master` and exercises **none of the code under test**.

`scripts/qa-env-override.py` does not close this. It isolates `COMPOSE_PROJECT_NAME`, host ports and named volumes, which is what it was written for; the build context was simply never part of its model.

## Why this is `normal` and not `trivial`

**It fails toward a false pass.** Two outcomes, and only one is loud:

- The endpoints under test don't exist on `master` → everything 404s → QA reports a false failure and someone burns a bounce-back round chasing it.
- The task **modifies** behaviour that already exists on `master` (a fix, a retrofit, an ordering change) → the stack answers plausibly on every endpoint, the old behaviour passes the old assertions, and **QA signs off on a binary that does not contain the change**. Nothing in the run looks wrong.

The second is the dangerous one and it is the shape of most non-greenfield tasks. [T-105](T-105-experience-ordering-retrofit.md) is precisely it: an ordering retrofit whose endpoints all exist on `master` today and whose stage-4 QA would happily verify the *unretrofitted* order.

## How it was caught, and how nearly it wasn't

T-103's stage-4 run, 2026-08-21. The driver noticed `build: ./cv-domain-service` while preparing the bring-up and added a third compose file by hand:

```yaml
# docker-compose.override.cvdl_t-103.build.yml
services:
  domain-service:
    build: /home/erfeamor/work/cvdl-worktrees/T-103
```

QA then **proved its own provenance** rather than assuming it: `GET /api/v1/skills` answered `200` on bring-up, and that endpoint does not exist on `master` at all, so its presence is positive evidence the right tree was built. That check only works for a **new** resource — T-103 was greenfield and got lucky. A modifying task has no such tell, which is the argument for fixing the generator rather than repeating the manual workaround.

## Scope

1. **Teach `scripts/qa-env-override.py` the build context.** It already takes `--task`; give it the worktree path (derive from the task id, or accept `--worktree`, and fall back to the main checkout when the task is not on a worktree). Emit the `build:` override into the file it already generates — one file, not two.
2. It must handle **any** buildable service, not just `domain-service` — `cv-bff-node` has the identical exposure and the JS/TS tasks (T-201, T-203, T-204) will hit it.
3. **Print a provenance check** alongside the up/down/smoke commands it already prints: something QA can run to prove which tree it built. A commit SHA exposed by the service, or at minimum an instruction to verify rather than assume.
4. Cross-reference from the adapter's §6. **Note the adapter file is gitignored**, so §6 itself cannot be fixed by a PR in this repo — this task's own body is the durable record, and the adapter should be edited locally to point here.

## Definition of Ready — scope decisions (PO-ratified at refinement, 2026-08-21)

1. **Resolve the worktree from git, do not guess it from the task id.** `~/work/cvdl-worktrees/<task-id>` is a convention, not a guarantee — T-019, T-014 and T-018 all declare `worktree: none` because cv-infra's local Terraform backend forbids one. Accept an explicit `--worktree PATH`; when omitted, look for the conventional path and fall back to the main checkout **only if it does not exist**. Never invent a path that isn't on disk.

2. **Match worktree → compose service by repo name read from git, not from a hard-coded table.** `git -C <worktree> remote get-url origin` yields `cv-domain-service`; the compose service's build-context basename (`./cv-domain-service`) is the same string. Repoint the service whose basename matches. A hard-coded `{"domain-service": "cv-domain-service"}` map is rejected — it is one more thing to drift, and this task exists *because* a hard-coded relative path drifted from reality.

3. **Only the matched service is repointed, and zero matches is legitimate.** A task changes one repo (the engine guarantees it at stage 0), so exactly zero or one service is repointed. A `cv-database`, `cv-infra` or docs task has no buildable service under test. **Print which, loudly** — "repointed `domain-service` → …" or "no service repointed (task repo is not built by this compose file)" — because a silent zero is indistinguishable from the bug being fixed.

4. **The build override goes in the file the generator already writes.** One file, not the two T-103 needed by hand. Emitting a second file preserves the failure mode: the bring-up command grows a third `-f` that someone will eventually omit.

5. **Provenance is a build LABEL, not an endpoint.** The service must not grow a `/version` endpoint — that is scope creep into a product repo and a contract change. Emit `build.labels` carrying task id, branch and short SHA; provenance is then `docker inspect` against the built image and works for **every** service, including modifying tasks with no distinguishing endpoint. **This is the ruling that answers T-105.**

6. **The generated file stays gitignored.** It is a build artifact; the durable record is this task and the generator's own printed output.

## Test plan (PO-AUTHORED at refinement — see `checkpoint.budget_note`; QA must ratify or amend before stage 4)

**This plan was not written by QA.** It was written by the PO at SOFT budget, a deliberate deviation from the engine's rule that QA authors the plan it later runs. Treat every row as a proposal until QA signs it — a plan written by the party who wants the task to pass is precisely what the split exists to prevent.

### Generator-level

| # | Case | Detects |
|---|---|---|
| G1 | `--worktree` given, matching service exists | override carries `build:` = worktree path **and** the port remapping is still present — the regression risk is fixing builds while silently breaking isolation |
| ~~G2~~ | ~~`--worktree` omitted, conventional path absent | no `build:` key; output byte-identical to today~~ | **ROW STRUCK 2026-08-21.** Finding 4 overrode it deliberately: the ruling-3 note is now emitted into the file header in **all three** branches, so a reader of a stored override can tell "considered, nothing to repoint" from "predates the fix". The YAML **body** identity was verified by `diff` at round 1 and is recorded there. Reconciling this row would have meant re-hiding the information finding 4 exists to surface. |
| G3 | worktree repo not built by this compose file (e.g. `cv-infra`) | exits 0, emits no `build:`, and **says so on stdout** (ruling 3) |
| G4 | `--worktree` path does not exist | fails loudly, non-zero — never silently falls back, which would recreate this very bug |
| G5 | two buildable services, worktree is `cv-bff-node` | only `bff` repointed; `domain-service` untouched |
| G6 | `--json` | reports resolved build context + labels, so stage 4 can assert provenance mechanically |

### Integration — the case that matters

| # | Case | Detects |
|---|---|---|
| **I1** | Bring the stack up from a worktree carrying a **trivial, visible change to an EXISTING endpoint**, and assert the response shows it | **the false pass this task exists to fix.** An additive check (new endpoint 404s) does not exercise it — T-103 passed that way by luck |
| I2 | `docker inspect` the built image for task/branch/SHA labels | ruling 5's provenance actually works |
| I3 | same bring-up with no worktree | main checkout still builds; single-task non-wave runs not broken |

**I1 is the acceptance test.** If only I1 runs, the task is meaningfully verified. If everything *except* I1 runs, it is not verified at all.

## Acceptance criteria

- [ ] ~~`qa-env-override.py --task <id> --slot <s>` produces a stack that builds **the worktree**, verified by a bring-up whose service reports code only present on the branch.~~ **WRONG — struck 2026-08-21, agreed by both reviewers.** *"code only present on the branch"* encodes the **additive** tell that T-103 passed by luck, and it contradicts the very next criterion, which demands the **modifying** case. Replacement: `--task <id> --slot <s>` in the **bare form** (no `--worktree` — the real pipeline invocation) produces a stack that builds the worktree under test, proven two ways: (a) `docker inspect` shows the provenance labels; (b) a bring-up against a worktree carrying a **modifying** change to an existing endpoint returns the modified value while the identical bring-up with no worktree returns master's. **This is the third acceptance criterion this week found wrong by the person implementing against it** — after T-103's `@Transactional` one and T-104's inherited "flag, don't block". The specifications, not the implementations, are this board's weak link.
- [ ] Works for a **modifying** task, not just an additive one — prove it on a change to an existing endpoint, since that is the case the current tell cannot catch.
- [ ] Falls back cleanly to the main checkout when no worktree exists (single-task, non-wave runs).
- [ ] Covers every buildable compose service, `bff` included.
- [ ] The generator prints a provenance check.
- [ ] [T-104](T-104-project-resource.md), [T-151](T-151-dev-seeds-cv-sections.md) and [T-105](T-105-experience-ordering-retrofit.md) cross-linked, as the next tasks exposed.

## Definition of done

PR against `master` in the meta repo from `fix/qa-env-worktree-build-context`, with the manual `*.build.yml` workaround retired.

## Provenance

Found 2026-08-21 during T-103's stage 4 and worked around by hand for that run. Filed rather than left in the checkpoint because the workaround lives in a **gitignored** generated file that vanishes with the next cleanup — exactly the hand-off-that-lands-nowhere this board keeps having to re-file.
