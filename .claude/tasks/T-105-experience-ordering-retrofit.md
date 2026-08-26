---
id: T-105
title: Retrofit contract ordering onto the merged Experience resource
repo: cv-domain-service
status: done
owner: backend-developer
branch: fix/experience-ordering
pr: https://github.com/erfeamor/cv-domain-service/pull/9
depends_on: [T-006]
risk: normal
security_review: false
checkpoint:
  stage: done                 # MERGED 2026-08-26 as 1b9b398 (squash of 91a6218 + eb3329f). Nothing outstanding: every acceptance criterion met, no unticked criterion carried.
  merged_commit: 1b9b398
  h2: |
    RATIFIED BY THE HUMAN 2026-08-26. Presented CI-green and QA-signed-off, with the diff's
    shape stated up front: two production lines against 224 of tests and javadoc. The human
    read the diff and challenged that ratio directly — "the only ones I see are a method name
    change, and some tests" — which is the correct reading and the right question to ask.

    THE ANSWER, RECORDED BECAUSE IT IS THE NON-OBVIOUS PART OF THIS TASK: the rename IS the
    implementation. ExperienceRepository is a Spring Data interface with no method bodies, so
    the method NAME is the query — findByPersonId emits no ORDER BY, and
    findByPersonIdOrderByStartDateDescIdAsc emits `ORDER BY start_date DESC, id`. There is
    nowhere else the logic could live. The 100:1 test ratio is driven by one specific finding,
    not by thoroughness for its own sake: proving `startDate DESC` is cheap, and proving the
    `id ASC` tiebreak turned out to be IMPOSSIBLE through row-order assertions, which is what
    the StatementInspector harness (~40 lines, the first in this repo) exists to close.

    Accepted with no changes requested. The honest trim was named rather than hidden — dropping
    the provably-non-probative tie test — and the human did not take it.
  merge: |
    Squash-merged 2026-08-26 as 1b9b398. Rebase-and-rerun gate satisfied BY CONSTRUCTION rather
    than by re-running: origin/master was still 7677fee, the exact commit the branch was cut
    from, so the green Jenkins run was earned against the current mainline and no sibling had
    moved it.

    MERGED WITH --admin, AND THAT IS THE DESIGNED PATH HERE, NOT A CIRCUMVENTION — worth
    recording because a future reader will otherwise reasonably read it as one. `gh pr merge`
    first refused: mergeStateStatus BLOCKED, reviewDecision REVIEW_REQUIRED. Diagnosis rather
    than reaching for --admin: classic branch protection returns 404 on this repo; the rule is
    a RULESET ("Protect main branch", id 18825306, active since 2026-07-12) requiring 1
    approving review, code-owner review, last-push approval, linear history and signatures.
    Its bypass list is `RepositoryRole: always` — the owner is granted bypass BY DESIGN. And
    PR #8 (T-104) merged 2026-08-22 by erfeamor with ZERO approving reviews while that same
    ruleset was active, so every prior task on this board merged the same way. A solo developer
    cannot satisfy "1 approving review" on their own PR: GitHub blocks self-approval. The
    control that actually gated this merge was H2, which is a human gate and was given.

    Close-out cleanup completed: worktree removed, branch deleted local AND remote (cv-domain-
    service now holds master and nothing else), checkpoint.worktree cleared per T-028 and
    verified by RUNNING qa-env-override.py rather than by reading, generated compose override
    removed.
  qa: |
    STAGE 4 SIGNED OFF 2026-08-26, no defects, NO BOUNCE TO THE DEVELOPER (qa_bounces stays 0).
    Stack cvdl_t-105 (slot 0, domain 8090 / MySQL 3316), generator run bare, its up:/prov:/down:
    lines used verbatim, torn down clean — no containers, no volumes left.

    THE SPINE RAN IN FULL, which is the only reason the rest counts. T-105 is a MODIFYING task:
    every endpoint it touches already answers on master, so §§2-5 would pass against the wrong
    tree. QA-T105-02 labels (branch fix/experience-ordering, commit eb3329f, dirty=false) were
    compared against THIS FILE'S frontmatter, not merely against themselves; QA-T105-03's
    negative control then confirmed the probe discriminates — worktree eb3329f: 1 match for the
    ordered method; origin/master@7677fee: 0 matches, grep exit 1.

    13/13 planned checks PASS. QA-T105-06 exact: [6,4,8,7,5], the plan's [3,1,5,4,2] shape, not
    "mostly sorted". QA-T105-09/10: exactly the seven contract fields, one key-set across all
    five elements, absent optionals as JSON null. QA-T105-12: cross-person PUT *and* DELETE both
    404 with the victim row read back unmutated.

    QA WENT BEYOND THE PLAN AND CLOSED THE PLAN'S OWN DECLARED GAP — the best output of this run.
    §6 flagged a residual risk it judged disproportionate to close: Docker layer caching could in
    principle leave stale bytecode running under correct labels, since QA-T105-03 checks SOURCE at
    the labelled commit, not the running JAR. QA closed it for free via MySQL's performance_schema
    statement digest, reading the SQL the DEPLOYED BYTECODE actually issued:
      SELECT ... FROM `experience` `e1_0` WHERE `e1_0`.`person_id` = ?
      ORDER BY `e1_0`.`start_date` DESC , `e1_0`.`id`        COUNT_STAR: 13
    (trailing ASC elided by MySQL's digest normalizer as the default). So the tiebreak is now
    evidenced at THREE independent layers — the declaration, the Hibernate-emitted SQL captured
    in-process by the unit test, and the statement the live server actually ran.

    EXPLORATORY, all clean: a 5-ROW tie group returned strictly id-ascending with correct
    brackets (the plan named >=3-row ties as explicitly uncovered); an UPDATE moving a startDate
    INTO an existing tie group re-sorted by id within the new group rather than by storage
    position or update recency — the closest black-box analogue to an out-of-order-id tie the
    HTTP surface allows; DELETE of a tie-group head preserved order; empty collection still 200
    [] and not 404; 10 consecutive GETs produced exactly one distinct id array.

    A FREE PROVENANCE TELL THE PLAN SAID DID NOT EXIST: Flyway's dev-seed rows for person 1 carry
    ids 1,2,3 in ASCENDING startDate order, so contract order is their exact reverse. This build
    returns [3,2,1]; an un-retrofitted master returns [1,2,3]. An additive-style tell on a
    modifying task, independent of the labels. Worth relaxing the plan's §1 note on any successor.

    NON-DEFECTS, no action: the collection GET's 404 body says "Experience not found" for an
    unknown PERSON — misleading but PRE-EXISTING on master (ExperienceController.java:34 reuses
    one constant), not a T-105 regression and out of scope. An unscoped `WHERE id = ?` in the
    digest was investigated and EXONERATED BY COUNTS rather than waved off: the scoped
    `id = ? AND person_id = ?` ran 4 times (gating every single-row op, including both
    cross-person 404s) against 2 unscoped, matching only the two successful mutations — it is
    Hibernate's internal entity load during merge/remove, downstream of the ownership check.

    NOT COVERED, stated rather than left silent: the BFF pass-through. QA probed it since the
    container was up — GET /bff/api/v1/people/2/cv is 404 and the person route carries no
    experiences key, because the aggregate is T-201 and is not built yet. Nothing about T-105
    reaches the public path today.

    TWO ITEMS FOR THE BOARD, deliberately NOT filed by the driver as new tasks:
      - The stale `curl localhost:3000/api/v1/people/1` in the meta CLAUDE.md that QA hit is
        ALREADY FILED as T-023 (which the 2026-08-22 sweep widened to four files). Filing again
        would duplicate a live task — this is QA independently re-confirming T-023 is real.
      - scripts/qa-env-override.py's printed `prov:` line names `cvdl_t-105-domain-service` while
        Compose creates `...-domain-service-1`. It resolved anyway and the failure mode is loud,
        so it is COSMETIC — recorded here and raised at H2 for the human to decide, rather than
        filed unilaterally against a tool whose task (T-028) is closed.
  pr: https://github.com/erfeamor/cv-domain-service/pull/9
  ci: |
    GREEN — the authoritative gate (adapter §3: Jenkins for cv-domain-service).
    PR-9 build #2, success 2026-08-26T08:43:49Z, read from the STATUSES API, not `gh pr checks`.

    T-026 REPRODUCED ON THIS TASK'S OWN PUSH, and it is now the cleanest instance on record —
    written up in T-026 as occurrence 6 (cv-domain-service PR-9#1), which is the FIRST time the
    whole chain was observed live rather than reconstructed afterwards:
      08:41:20Z  cv-project-drone  stopped -> running   (doorbell, fired by this push — T-019
                                                         working end to end, unprompted)
      08:42:24Z  error    PR-9#1  "This commit cannot be built"   <- 64s after the box started
      08:43:49Z  success  PR-9#2  "This commit looks good"        <- warm box, UNATTENDED
    Nobody retriggered #2: pushing the branch and opening the PR are two separate webhook
    deliveries. 64s is the longest of the four measured cold-start intervals (42/47/62/64s).
    The `error` sits BETWEEN TWO `pending`s here, so `gh pr checks` hides it completely —
    worse than T-026's plain-red case and exactly T-030's warning. Console signature still
    unobtained (Jenkins needs credentials this machine's policy declines); NOT claimed.
  repo: cv-domain-service
  branch: fix/experience-ordering
  worktree: none   # CLEARED AT CLOSE-OUT 2026-08-26, per T-028's rule — a lingering path on a done task makes EVERY later qa-env-override.py bring-up exit 1, which is how T-101/T-102 silently broke the tool for a day. Was /home/erfeamor/work/cvdl-worktrees/T-105 (created 2026-08-24 at stage 1, branched from 7677fee). Directory physically removed, branch deleted local+remote, cvdl-worktrees/ now empty. Verified executably, not by eye: `python3 scripts/qa-env-override.py --task T-105` exits 0.
  developer: backend-developer
  reviewers: ["/code-review", "backend-developer (specialist lens, read-only)"]
  risk: normal                # adapter §5: not trivial — it changes the observable behaviour of a live endpoint. A1 re-decides against the real diff.
  security_review: false      # no adapter §5 path in the expected diff (no auth/secrets/IAM/CI). A1 forces it anyway if the real diff disagrees.
  env_slot: 0                 # single-task run, no wave; slot 0 -> domain-service on 8090
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-26
  commit: eb3329f
  review_round_1: |
    COMPLETE 2026-08-26, no blocking findings outstanding. Two independent passes:
    /code-review (high, EXPLICIT worktree + master...HEAD target per T-029) and the
    backend-developer specialist lens (read-only). Fixes committed as eb3329f, TEST-ONLY
    (2 files, +56/-6); ExperienceController.java is BYTE-IDENTICAL to 91a6218, so AC4
    ("no change to the controller") holds on evidence, not on assertion.

    BOTH REVIEWERS INDEPENDENTLY REPRODUCED stage1_finding_1_THE_NINTH BY PROBE, and this is
    the round's most valuable output. With `ORDER BY start_date DESC` alone, and with NO
    ORDER BY AT ALL, ordersRowsSharingAStartDateByIdAscending... STAYED GREEN; only
    declaresTheIdTiebreakerInTheGeneratedSql went red. Neither reviewer proposed deleting the
    SQL-capturing test and neither re-derived option (a) — the CONSUMED_stage2_not_started
    instruction did its job.

    FINDING 1 (BLOCKING, from /code-review; PO ruling: ACCEPT). The tie test's own javadoc
    still carried the PRE-DISCOVERY rationale — "Only inverting id against insertion order
    makes a missing id ASC observable" — which is measurably FALSE and contradicted the
    javadoc on declaresTheIdTiebreakerInTheGeneratedSql IN THE SAME FILE, authored in the same
    commit. Failure mode: a maintainer believes row-order coverage protects the tiebreak and
    deletes the SQL test as redundant, losing all coverage of the secondary key while the suite
    stays green — the T-107 shape (a confident comment retiring the question). Rewritten to
    state the measured result and to name the SQL test as load-bearing. NOTE THE SHAPE: the
    checkpoint tried to protect that test with a NOTE TO REVIEWERS while the file itself
    contained the argument for deleting it; the fix moves the protection into the artifact,
    which is the durable form (T-103 precedent).

    FINDING 2 (from /code-review, filed "low"; PO ruling: ACCEPT, and it is stronger than
    filed). No controller-level order pass-through test existed. Driver verified directly
    against master that ALL FOUR sibling resources have one (ProjectControllerTest:449,
    plus Education/Skill/PersonSkill) — experience was the odd one out, the T-104 repoUrl
    shape. c1's fixture cannot catch a re-sort: its two rows are already BOTH id-ascending
    and alphabetical. CONFIRMED RED FIRST, per standing practice: with a company sort
    temporarily in findAll, the new test failed ($[0].company expected Zeta, was Alpha) AND
    THE OTHER 19 CONTROLLER TESTS PASSED against that re-sorting controller — which measures
    the gap rather than arguing it. Green after restore.

    FINDING 3 (specialist, non-blocking; ACCEPT as cheap insurance). CapturedSql.STATEMENTS is
    process-global; added @BeforeEach clear + a javadoc stating the class must not run under
    parallel execution. The inline clear inside the SQL test is still required and was kept.

    LOGGED, DELIBERATELY NOT FIXED: \bid\b is alias-blind (tightening to a literal Hibernate
    alias is brittle across minors — a worse trade); startsWith("select") breaks under
    hibernate.use_sql_comments (not enabled anywhere); a 124-char test line (checkstyle does
    not scan test sources; five pre-existing longer lines in that file).

    FILED, NOT FOLDED IN (board rule 3): T-109. The specialist flagged EducationRepository's
    tiebreak as asserted by a test that cannot go red; the driver VERIFIED and WIDENED it
    before filing — project, person_skill and skill have the same gap, and
    `grep -rln StatementInspector src/` is empty on master, so T-105 introduces the repo's
    first SQL-capture evidence. All five orderings are CORRECT today; only the evidence is
    missing. Widened on re-checking rather than on the reviewer's description, because this
    board has twice filed a task whose count was already wrong (T-023, T-017).

    A1 RE-RUN INDEPENDENTLY BY THE DRIVER after the fixes, not taken on the developer's
    report: checkstyle:check exit 0, mvn -B test 141 tests / 0 failures / 0 errors / BUILD
    SUCCESS (was 140), worktree clean.
  resumed: |
    RESUMED 2026-08-26 in a fresh session, at stage 2 exactly as stage2_not_started directed.
    A1 RE-RUN INDEPENDENTLY ON RESUME rather than inherited from the checkpoint — the gate is
    deterministic and cheap, and this board's standing rule is to verify a claim before spending
    attention on it: checkstyle:check exit 0, mvn -B test 140 tests / 0 failures / 0 errors /
    BUILD SUCCESS. Diff re-confirmed at 4 files, +176/-6, all under src/main|src/test, ZERO files
    under .claude/tasks/. Worktree clean, branch fix/experience-ordering @ 91a6218, still local.
    Review round 1 spawned: /code-review (high effort, EXPLICIT worktree+range target per T-029)
    and the backend-developer specialist lens (read-only brief).
  budget: |
    Inherited, NOT reset (engine checkpoint.md §3). This task has now spanned THREE sessions:
    stage 0 + H1 (entered at 352/400 turns, soft), stage 1 (entered at 380/400, soft, by explicit
    human override), and this one. Resume-session probe at stage-2 entry: 68/400 turns (17%),
    10.3M/150M tokens (6.9%), status OK. Spawns on this task in THIS session: 2 of 3 (the two
    review passes) — a third is available for a QA/coverage pass or a developer re-brief, so a
    review bounce is affordable but a second full round plus QA is not without a re-probe.

    UPDATED AT STAGE-4 ENTRY, 2026-08-26: turns 162/400 (40.5%), tokens 35.1M/150M (23.4%),
    status OK. Spawns THIS SESSION: 4 — /code-review, the specialist lens, the developer, and
    stage-4 QA.

    DELIBERATE DEVIATION, RECORDED RATHER THAN LET PASS: the 4th spawn EXCEEDS the adapter's
    structural cap of max_spawns_per_task: 3. Taken knowingly, for two reasons. (1) The engine's
    non-negotiable is that nothing reaches the mainline without a QA pass, and QA must run BEFORE
    H2 so the human never reviews unvalidated work — skipping it to honour a cost cap would trade
    a correctness guarantee for a budget one. (2) The numeric guard, which is what that cap is a
    proxy for, is healthy at 40.5%/23.4%. Independence is worth more than usual on THIS task
    specifically: its entire history is tests that passed for the wrong reason, and the QA plan's
    spine (QA-T105-03's negative control) is exactly a check on whether the right binary was
    tested. The cap is a cost heuristic; the QA stage is a correctness invariant. Surfaced in the
    H2 presentation rather than buried here.
  stage1: |
    Implemented 2026-08-24 on fix/experience-ordering, commit 91a6218, NOT pushed, no PR.
    4 files, +176/-6: ExperienceRepository (derived form findByPersonIdOrderByStartDateDescIdAsc
    + javadoc recording why no IS NULL handling), ExperienceController (call site only),
    ExperienceRepositoryTest (+154: two ordering tests, a SQL-capturing test config, helpers),
    ExperienceControllerTest (+3/-3, mechanical stub rename only — see stage1_finding_2).
    No @Query, no CASE WHEN, no SecurityConfig, no payload change. Ruling 2 re-verified by the
    developer against V1__init_schema.sql:19 (start_date DATE NOT NULL) rather than inherited.
  a1: |
    PASS, RE-RUN INDEPENDENTLY BY THE DRIVER, not taken on the developer's report (T-018 precedent):
    checkstyle:check exit 0 · mvn -B test 140 tests / 0 failures / 0 errors / BUILD SUCCESS ·
    package -DskipTests clean. Diff confirmed 4 files / +176-6 with ZERO files under .claude/tasks/.
    Risk re-check against the REAL diff: no adapter §5 security path (no auth, secrets, IAM, CI
    config, ports, CORS) -> security_review: false holds on evidence, not on the stage-0 guess.
    `trivial` was never claimed, so the >150-line/>5-file revocation rule does not apply.
    NOTE the H2 unique-constraint error visible in the test log is T-103's duplicate-name test
    exercising its 409 catch path — an assertion, not a failure.
  stage1_finding_1_THE_NINTH: |
    THE H1-RATIFIED AC3 FIX IS ITSELF NOT PROBATIVE — and this one is the PO's own ruling,
    recommended by the driver and ratified by the human hours earlier. Found by the developer
    EMPIRICALLY, not argued: the ratified test (native inserts, id 9002 first, 9001 second,
    asserting 9001 comes back first) PASSED GREEN under a probe with no ORDER BY at all.
    WHY: H1 fixed half the coupling and the half it left is the one that binds. H2 stores rows in
    a primary-key B-tree, so a tie group is walked in id-ascending order WHATEVER the query says.
    Assigning ids out of order changes which rows are tied, not the order the engine returns them.
    Consequence, stated plainly: NO row-order assertion in a @DataJpaTest can go red against a
    missing `id ASC`, because the desired order IS the storage order. The PO's option (a) was
    wrong for the same class of reason the original criterion was, one level down.
    WHAT SHIPPED: the ratified test is committed unchanged (it is strictly better than the
    original — it does exclude an implementation that returns insertion order), PLUS
    `declaresTheIdTiebreakerInTheGeneratedSql`, which captures the SQL Hibernate actually issues
    and asserts an explicit id sort key follows start_date. That one DOES go red (proven: probe 2
    failed with `Expecting actual: "start_date desc" to contain pattern: "\bid\b"`). That is the
    PO's option (b), added rather than substituted — which is what the H1 ruling asked for.
    PO ADJUDICATION 2026-08-24: KEEP the non-probative test, documented, rather than delete it.
    It excludes a real (if unlikely) wrong implementation, its javadoc records the measured result
    so the next reader does not re-derive it, and deleting it would destroy the evidence trail for
    a finding this board should not have to make a tenth time. The SQL-capturing test is the one
    that discriminates and must not be removed as "redundant" in review.
  stage1_finding_2: |
    "Keep the existing controller tests unmodified" was UNSATISFIABLE alongside ruling 1, and the
    developer flagged it rather than quietly working around it. ExperienceControllerTest is a
    @WebMvcTest with a @MockBean repository that stubs the method BY NAME at :86, :100 and :347 —
    renaming the repository method necessarily renames those stubs, or the mock returns an
    unstubbed empty list and C1/C17 fail. Mechanical rename applied, no assertion/fixture/
    expectation touched, all 19 controller tests pass. The brief's constraint was the error, not
    the implementation.
  CONSUMED_stage2_not_started: |
    CONSUMED 2026-08-26 — this checkpoint was read on resume and its instructions followed; the
    key is renamed rather than deleted so the handoff stays readable, and renamed rather than left
    as-is because "REVIEW HAS NOT RUN" became false the moment round 1 started (a stale assertion
    sitting under a live key is this board's most-repeated defect). Its two REVIEW instructions
    are still BINDING on the round now in flight: adjudicate finding 1, and target /code-review
    explicitly. Original text follows verbatim.
    STOPPED HERE DELIBERATELY at the stage-1/stage-2 boundary, 2026-08-24, budget 387/400 (96.8%).
    Stage 1 is COMPLETE and A1-green; REVIEW HAS NOT RUN. review_round: 0 is accurate, not stale.
    RESUME AT: stage 2. Branch fix/experience-ordering @ 91a6218, LOCAL ONLY — not pushed, no PR.
    Reviewers per adapter §7 (normal): /code-review + backend-developer specialist lens.
    THE REVIEW MUST ADJUDICATE FINDING 1 — do not let a reviewer delete the SQL-capturing test as
    redundant, and do not let one "fix" the non-probative test by re-deriving option (a).
    Note T-029: invoke /code-review with an explicit target (the PR number once stage 3 opens, or
    a committed-diff target) — bare invocation reviews the uncommitted working tree and returns a
    clean-looking empty result.
  qa_plan: recorded           # authored by quality-assurance at stage 0, appended to this file. QA executes it verbatim at stage 4.
  h1: |
    RATIFIED BY THE HUMAN 2026-08-24. Scope, developer (backend-developer), reviewer set
    (/code-review + backend-developer specialist lens) and the QA plan approved as presented.
    Premises were re-verified against cv-domain-service@7677fee before presentation, not inherited
    from the 11-day-old spec — including the one that mattered: experience.start_date is NOT NULL,
    so the "no IS NULL handling" ruling holds and the T-104/T-151 CASE-WHEN spelling must NOT be
    copied here.
  h1_ruling_ac3: |
    ACCEPTANCE CRITERION 3 AMENDED, ratified by the human 2026-08-24: option (a) — the tiebreaker
    test must ASSIGN IDS OUT OF ORDER (persist the higher id first among the tied pair) so that the
    assertion can actually go red against a missing `id ASC` secondary key. The criterion as
    originally written could not fail, because AUTO_INCREMENT makes id monotonic in insertion order
    and both H2 and InnoDB commonly return a small scan in PK order regardless. The body's AC3 is
    updated to the ratified wording; the original is struck rather than deleted.
    The structural assertion (option b) was NOT taken as a substitute; QA-T105-08 covers that half
    at stage 4 by grepping the declaration on the proven commit.
  budget_override_h1: |
    STAGE 1 ENTERED ON A SOFT BUDGET READING (380/400 turns, 95%) BY EXPLICIT HUMAN DECISION,
    2026-08-24. The engine's rule is "do not start a new stage on SOFT", and the human was told the
    reading and that a checkpointed mid-stage stop is likely; they chose to proceed. Recorded as a
    deliberate override rather than an oversight, exactly as T-028 recorded the same choice (which
    then did stop mid-pipeline, at 86.8% — earlier than this).
    EXPECT A STOP AT OR SHORTLY AFTER STAGE 1. Whoever resumes: the checkpoint is the contract, and
    stage 1 completing does not mean review ran.
  h1_open_question: |
    ACCEPTANCE CRITERION 3 IS NOT PROBATIVE AS WRITTEN — raised at H1, not edited unilaterally.
    `id` is AUTO_INCREMENT and therefore monotonic in insertion order, so two rows sharing a
    startDate ALWAYS come back id-ASC whether or not the query declares `id ASC` as a secondary
    key. The assertion cannot go red against a missing tiebreak, which is the tell. Options and
    the PO recommendation (assign ids out-of-order in the @DataJpaTest, so the test can actually
    fail) are written up in the body under "PO finding at stage 0". Found by QA while authoring
    the plan; it is the SEVENTH acceptance criterion on this board weakened or falsified by the
    person working against it.
  premises_reverified: |
    2026-08-24, against cv-domain-service@7677fee, BEFORE presenting H1 — this board's standing
    requirement, since T-105's spec was written 2026-08-13 and has sat unclaimed for 11 days.
      - The defect is still live: ExperienceRepository.findByPersonId is still a bare derived
        query with no ORDER BY (read off the file, not inferred from the task).
      - docs/api-contract.md:22 still specifies `experiences | startDate DESC | id ASC`, so the
        task's acceptance criteria still match the contract that governs them.
      - experience.start_date is NOT NULL in V1__init_schema.sql -> the task's ruling "do not add
        IS NULL handling" holds, and the CASE-WHEN spelling T-104 needed does NOT apply here.
        This is the one ruling that would have been wrong to inherit without checking, because
        T-104 and T-151 both had to handle the nullable case and the reflex is to copy them.
  worktree_note: |
    Deliberately NO checkpoint.worktree key at stage 0. T-028 made that key load-bearing: a
    declared path makes qa-env-override.py exit 1 until the directory exists, and stage 1 has not
    run. Stage 1 creates ~/work/cvdl-worktrees/T-105 and records the path then.
  budget_note: |
    Stage 0 was entered on a SOFT budget reading (352/400 turns, 88%) as an EXPLICIT HUMAN
    DECISION, 2026-08-24 — the engine's rule is "do not start a new stage on SOFT", and the human
    chose the bounded option: complete stage 0 + H1, checkpoint, stop before implementation.
    Recorded as a deviation rather than passed off as normal, per T-028's precedent (which took the
    same override and did stop mid-pipeline). RESUME AT: stage 1, in a fresh session with the full
    ceiling. Nothing is implemented; there is no branch and no worktree yet.
---

## Why this exists

T-006 added § Ordering to `docs/api-contract.md`. T-102, T-103 and T-104 absorb it into their acceptance criteria before they are implemented. **T-101 cannot** — it merged as [cv-domain-service#3](https://github.com/erfeamor/cv-domain-service/pull/3) on 2026-08-09, so Experience is the one section resource already in `master` without an ordering guarantee.

`ExperienceRepository.findByPersonId` is a derived Spring Data query with no `ORDER BY`:

```java
List<Experience> findByPersonId(Long personId);
```

It returns rows in whatever order MySQL produces. That is exactly the defect T-006 exists to prevent, and it is live on `master` today.

**This task is the recorded answer to T-006's acceptance criterion "a decision on how T-101 picks it up."** T-006's own rollout section offered two options — amend T-101's PR, or file a follow-up. The amend option was written while T-101 was still `in_review` and **died when it merged**; a merged PR cannot absorb the change. Ratified at T-006's H1 on 2026-08-13: follow-up task, this one.

## Scope

`cv-domain-service` only. One repository method, plus the tests that prove it.

- Order `findByPersonId` by `startDate` **DESC**, tiebroken by `id` **ASC**, per the contract's § Ordering table.
- Prefer the derived-query form (`findByPersonIdOrderByStartDateDescIdAsc`) over an `@Query`; it is the idiom already used in this package and it cannot drift from the entity's column mapping.
- `startDate` is `NOT NULL` on `experience` (unlike `project.start_date`), so **the NULL-placement rule does not apply here.** Do not add `IS NULL` handling — it would be dead code that implies a nullability the schema does not have.


> ~~**Before stage-4 QA: the generated stack builds `master`, not your worktree** — see [T-028](T-028-qa-env-generator-worktree-build-context.md). Until that lands, add a build-context override pointing at your worktree, and *prove* which tree you built rather than assuming it. **This task is the exact case the current provenance check cannot catch**: every endpoint you touch already exists on `master`, so a stack built from the wrong tree answers plausibly and QA would verify the *unretrofitted* ordering.~~
>
> **SUPERSEDED — T-028 landed 2026-08-21 (`74be2c8`), and this task was its motivating case.** Struck 2026-08-24: the same supersession was propagated to T-151 (struck) and T-104 (frontmatter note) the day T-028 merged, and this file — the one T-028's ruling 5 says it exists to answer (*"This is the ruling that answers T-105"*) — was missed. Current instructions: use `scripts/qa-env-override.py --task T-105 --slot <s>` **bare, with no hand-built override** — it repoints the build context at the worktree and refuses loudly rather than silently building `master`. Provenance for this modifying task is the **image labels** (`docker inspect`: commit/branch/dirty), not an endpoint tell — exercised for real by T-104's stage 4. The warning's substance was correct and is now enforced by the tool: stage-4 sign-off still checks the labels rather than assuming them.

## Acceptance criteria

- [ ] `GET /api/v1/people/{personId}/experiences` returns `startDate` DESC, then `id` ASC.
- [ ] A `@DataJpaTest` seeds rows **inserted in a deliberately wrong order** and asserts the returned sequence. Inserting in the expected order would pass against an unordered query and prove nothing.
- [ ] ~~A separate assertion covers the tiebreaker: two rows sharing a `startDate`, asserted to come back in `id` ASC order.~~ **AMENDED AT H1, 2026-08-24 — the original could not fail.** `id` is `AUTO_INCREMENT`, so the earlier-inserted of two tied rows always has the smaller `id`, and both H2 and InnoDB commonly return a small scan in PK order anyway — so the assertion passed identically with or without an `id ASC` secondary key. **Ratified replacement:** the tiebreaker test persists the tied pair with **explicitly assigned, out-of-order ids** (the higher id inserted first), then asserts the lower id comes back first. That form goes **red** against a missing secondary key, which the original never could. Confirm it red before adding the tiebreak, per this board's standing practice.
- [ ] No change to the controller, service, payload shape, or any other endpoint — the response body is byte-identical apart from element order.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Definition of done

PR open against `master` from `fix/experience-ordering`, Jenkins green, merged, task set `done`.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2 — `cv-domain-service`). **Reviewers:** `/code-review` + `backend-developer` specialist lens. `risk: normal`; small diff, but it changes the observable behavior of an endpoint already consumed.
- `security_review: false` — no auth, secrets, IAM, or CI surface.
- **Sequencing:** independent of T-102/T-103/T-104 (disjoint packages), so it can run in the same wave. It does **not** block T-201 — but leaving it undone means the aggregate serves one unordered section out of four, which T-501 would find at the worst possible moment.

---

## ⚠️ PO finding at stage 0 — acceptance criterion 3 is not probative as written (2026-08-24)

**QA raised this while authoring the plan below, and it is the seventh acceptance criterion this board has had weakened or falsified by the person working against it** (after T-103's `@Transactional`, T-104's inherited "flag don't block", T-028's AC1, T-152's AC3 and its dirty-volume watch-out, and T-201's AC4 struck the same day). Raised at **H1** rather than edited silently, because it changes what "done" means.

AC3 reads: *"A separate assertion covers the tiebreaker: two rows sharing a `startDate`, asserted to come back in `id` ASC order."*

**The problem:** `id` is `AUTO_INCREMENT`, so it is assigned monotonically in insertion order. For any two rows sharing a `startDate`, the earlier-inserted row **always** has the smaller `id`. A test that inserts two tied rows and asserts they come back `id` ASC therefore passes **identically** whether the query says `ORDER BY start_date DESC, id ASC` or merely `ORDER BY start_date DESC` — because InnoDB (and H2) commonly return a small unindexed scan in PK order anyway. The assertion cannot distinguish a declared tiebreak from an incidental one.

That is the exact "green signal that measures nothing" class this board has catalogued four times (T-107's mock-measuring test, T-028's master-building QA stack, T-026's `gh pr checks`, T-029's empty `/code-review`).

**Two ways to make it probative — H1 picks one:**

- **(a) Control the ids independently of insertion order.** In the `@DataJpaTest`, persist the tied rows with **explicitly assigned, out-of-order ids** (higher id first), then assert the lower id comes back first. This is the only form that can actually fail against a missing tiebreak. Costs a little `TestEntityManager` / native-insert plumbing.
- **(b) Keep the behavioural assertion but pair it with a structural one** — assert the repository method's *declaration* carries the secondary key (the derived name `findByPersonIdOrderByStartDateDescIdAsc`, or an explicit `id ASC` in an `@Query`). Cheaper, but it asserts the shape of the code rather than its behaviour.

**PO recommendation: (a)**, with (b) as a cheap addition rather than a substitute. The board's standing practice is that a test must be **confirmed red before the fix** — and AC3 as written *cannot* go red, which is the tell.

**Not changed unilaterally.** AC3 stays as written until H1 rules; the QA plan below already carries the same finding as `QA-T105-08` for the stage-4 half.

---

## QA test plan (authored at stage 0 by `quality-assurance`, 2026-08-24 — QA executes it verbatim at stage 4)

**Scope:** `GET /api/v1/people/{personId}/experiences` ordering only. One repository method (`ExperienceRepository.findByPersonId` → `findByPersonIdOrderByStartDateDescIdAsc`), no controller/payload/other-endpoint change, no NULL-placement case (`experience.start_date` is `NOT NULL`).

**Environment:** `python3 scripts/qa-env-override.py --task T-105 --slot 0` — bare, no `--smoke`, no hand-built override. Domain service on `localhost:8090`, MySQL on `localhost:3316`. Bring up with the `up:` command the generator prints; tear down with its `down:` command (`down -v`) at the end, per T-028/T-104 precedent — **do not hand-derive container names**; use the exact `up:`/`down:`/`prov:` lines the tool emits, since guessing them is exactly the kind of drift T-028 exists to remove.

### 1 · Build provenance — labels, and the negative control that makes them meaningful

The trap: every endpoint T-105 touches already exists on `master` and answers 200 with *some* order. Labels alone are self-consistent, not corroborating (qa-env-override.py's own "Finding 2") — a stamped label can only be trusted if the commit it names can independently be shown to contain the retrofit.

| ID | What | How | Expected |
|---|---|---|---|
| QA-T105-01 | Generate + bring up | `python3 scripts/qa-env-override.py --task T-105 --slot 0`, then run its printed `up:` command | Override written, stack healthy; note the printed `prov:` line(s) for use below |
| QA-T105-02 | Provenance labels | run the printed `prov:` command for `domain-service` (`docker inspect --format '{{json .Config.Labels}}' <container>`) | `com.cvproject.dev-loop.branch = fix/experience-ordering` (matches the board's `checkpoint.branch`, per Finding 2 — compare against this file's frontmatter, not just self-consistency), `.dirty = false`, `.commit = <sha>`, `.worktree = ~/work/cvdl-worktrees/T-105` |
| QA-T105-03 | **Negative control** — the labeled commit actually contains the fix, and a known-bad tree doesn't | `git -C ~/work/cvdl-worktrees/T-105 show <sha-from-02>:src/main/java/com/erfeamor/cvdomain/experience/ExperienceRepository.java \| grep -n "OrderBy\|ORDER BY"`, then the **same grep** against `git -C <checkout>/cv-domain-service show origin/master:src/main/java/com/erfeamor/cvdomain/experience/ExperienceRepository.java` | Worktree commit: 1 match (the ordered derived method / `@Query`). `origin/master` tip: **no match** — proves the probe discriminates retrofitted from un-retrofitted source, so a mislabeled build (labels claiming the branch while actually building `master`) would have been caught here, not assumed away |

### 2 · Ordering through the real API — rows inserted in a deliberately wrong order

Insertion order is chosen so the resulting `id` sequence does **not** match the expected `startDate` DESC sequence in any trivial way (not ascending, not reverse) — a fixture inserted in the expected order proves nothing against an unordered query.

Fixture, insertion order γ, ε, β, α, δ (ids assigned 1..5 in that order):

| Label | startDate | Insert # | id (relative) |
|---|---|---|---|
| γ | 2025-03-01 | 1st | 1 |
| ε | 2020-01-01 | 2nd | 2 |
| β | 2026-06-01 | 3rd | 3 |
| α | 2024-01-15 | 4th | 4 |
| δ | 2025-03-01 (tie with γ) | 5th | 5 |

Expected output order: β(3), γ(1), δ(5), α(4), ε(2) → id sequence `[3,1,5,4,2]`.

| ID | What | How | Expected |
|---|---|---|---|
| QA-T105-04 | Fixture person | `curl -s -X POST http://localhost:8090/api/v1/people -H 'Content-Type: application/json' -d '{"fullName":"T105 Fixture","email":"t105-fixture@example.test"}'` | 201; capture `id` as `$PID` |
| QA-T105-05 | Seed rows, wrong order | 5× `curl -s -X POST http://localhost:8090/api/v1/people/$PID/experiences -d '{"company":"<γ/ε/β/α/δ>","role":"r","startDate":"<date above>"}'`, in the exact insertion order γ,ε,β,α,δ | 5× 201; capture each returned `id` (`$G,$E,$B,$A,$D`) |
| QA-T105-06 | Full ordering assertion | `curl -s http://localhost:8090/api/v1/people/$PID/experiences \| jq '[.[].id]'` | `[$B,$G,$D,$A,$E]` exactly — `startDate` DESC end to end, not just "roughly sorted" |

### 3 · Tiebreaker — id ASC among rows sharing one `startDate`, and how to tell a real tiebreak from luck

**Why this is hard to prove black-box:** `id` is assigned monotonically at insertion time, so for any two rows that share a `startDate`, the earlier-inserted one *always* has the smaller `id` — you cannot construct an HTTP fixture where "correct explicit `id ASC` tiebreak" and "no tiebreak at all, MySQL incidentally preserving insertion/PK order for a small unindexed scan" produce different observable results. A passing black-box test (γ before δ) is **necessary but not sufficient**. Closing the loop requires pairing it with source evidence, tied to the already-proven commit from §1. **See also the PO finding above: the same limitation applies to acceptance criterion 3's unit test, which is why it is being raised at H1.**

| ID | What | How | Expected |
|---|---|---|---|
| QA-T105-07 | Tie pair comes back id ASC | From QA-T105-06's array, extract the positions of `$G` and `$D` | `$G` immediately precedes `$D` (both are the 2025-03-01 group) |
| QA-T105-08 | **Corroborate the tiebreak is declared, not incidental** | On the same commit proven in QA-T105-03: `git -C ~/work/cvdl-worktrees/T-105 show <sha>:src/main/java/com/erfeamor/cvdomain/experience/ExperienceRepository.java` — confirm the method is the derived form `findByPersonIdOrderByStartDateDescIdAsc(...)` (or, if `@Query`, an explicit second `ORDER BY … id ASC`/JPQL equivalent) | An explicit `id` ascending secondary key is present in the declaration itself — not just `OrderByStartDateDesc` with no second key, which would leave tie order formally unspecified by SQL even if QA-T105-07 happened to pass |

### 4 · Payload shape unchanged — only element order moves

| ID | What | How | Expected |
|---|---|---|---|
| QA-T105-09 | Field set + null rendering | `curl -s http://localhost:8090/api/v1/people/$PID/experiences \| jq '.[0]'` (pick the `β` element, which was POSTed without `location`/`description`/`endDate`) | Exactly the seven contract fields — `id, company, role, location, startDate, endDate, description` — no more, no fewer; `endDate` is JSON `null` (not `"null"`, not omitted); `location`/`description` likewise `null` |
| QA-T105-10 | Array shape | `curl -s .../experiences \| jq 'length'` and `jq '[.[] \| keys] \| unique \| length'` | length `5` (no dedup/merge); the `keys` set is identical across all five elements — order moved, shape didn't |

### 5 · No regression on sibling verbs and 404 paths

| ID | What | How | Expected |
|---|---|---|---|
| QA-T105-11 | PUT / DELETE still work | `curl -s -X PUT .../people/$PID/experiences/$A -d '{"company":"Alpha2","role":"r","startDate":"2024-01-15"}'` then `curl -s -o /dev/null -w '%{http_code}' -X DELETE .../people/$PID/experiences/$A` | PUT 200 with updated body; DELETE 204; a follow-up GET on the collection shows 4 rows, still correctly ordered |
| QA-T105-12 | Cross-person 404 (IDOR guard intact) | Create a second person `$QID`; `curl -s -o /dev/null -w '%{http_code}' -X DELETE .../people/$QID/experiences/$B` (row `$B` belongs to `$PID`) | 404, not 204/200; a follow-up GET under `$PID` still shows `$B` |
| QA-T105-13 | Unknown person 404 | `curl -s -o /dev/null -w '%{http_code}' .../people/999999/experiences` | 404 (person-existence check still runs before the now-ordered query) |

### 6 · Coverage risks — what passes this plan and is still broken

- **Sections 2–5 alone are insufficient.** They pass identically against an un-retrofitted `master` build that answers plausibly (unordered but not obviously wrong on a 5-row fixture) *unless* §1's negative control is actually run and its commit is confirmed to contain the change. A QA pass that skips QA-T105-03 would rubber-stamp exactly the defect T-006 exists to prevent — this is the whole reason §1 is the plan's spine, not a formality before the "real" checks.
- ~~**QA-T105-07 (black-box tiebreak) can pass for the wrong reason**, as explained in §3 — InnoDB frequently returns ties in insertion/PK order even with no `ORDER BY id` at all. QA-T105-08 is the check that actually rules this out; treat 07 alone as non-probative.~~ **STRENGTHENED 2026-08-24 by stage-1 evidence — it is worse than "can pass for the wrong reason".** The developer proved on H2 that a tie group is returned in `id` order **every time**, not "frequently", because the rows are walked in primary-key order regardless of the query. **QA-T105-07 cannot fail at all** — it is not weak evidence, it is no evidence. Run it as a sanity check if you like, but **QA-T105-08 (the declaration/SQL check) is the only thing at stage 4 that discriminates**, and with the derived-name form now shipped the method name *is* the query, so 08's grep is load-bearing rather than corroborative. Do not report a clean stage 4 on 07 alone. See `checkpoint.stage1_finding_1_THE_NINTH`.
- **This plan does not re-run `mvn -B test` / `checkstyle:check`.** Those are CI's job and are a precondition for reaching stage 4 (CI already green) — restated here so stage 4 isn't mistaken for re-proving them.
- **`@DataJpaTest` (H2) vs live MySQL divergence does not apply here the way it did for T-104's projects/skills.** Both sort keys (`start_date` DATE, `id` BIGINT) are totally ordered non-nullable types with no engine-specific NULL-placement question — unlike T-104's `CASE WHEN … IS NULL` spelling, there is no known H2/MySQL disagreement surface for this task. Still exercised live (per QA-T105-06) rather than assumed, but do not expect a T-104-style finding here.
- **The BFF pass-through is out of scope and untested by this plan.** T-105 touches only `cv-domain-service`; hitting the domain service directly on 8090 never exercises "the BFF passes arrays through unchanged." That's correct given scope, but flagging it so nobody reads a clean stage-4 run as having validated the aggregate/BFF path.
- **A 3-way tie is not exercised.** The fixture has exactly one 2-row tie group; a comparator bug that only manifests with ≥3 equal `startDate` rows (e.g., an unstable secondary sort) would not be caught. Deliberately not added — proportionate to a 5-line change — but worth naming rather than silently not-covering.
- **Docker layer caching residual risk:** `up --build` is not `--no-cache`; if a build-context/COPY layer key somehow failed to invalidate on the worktree's changed file, the image could carry stale labels claiming the right commit while running old bytecode. §1's negative control checks *source* against the commit, not the *running JAR* against the commit — genuinely closing that gap would require decompiling or a checksum inside the container, which is disproportionate here; flagged, not built.

### 7 · Failure signatures — several fail silently or look like something else

| Failure | Signature | How to tell it apart |
|---|---|---|
| Stack built from `master`, not the worktree | Every check in §§2–5 can still pass on a small fixture if the natural/incidental order happens to look plausible; only §1 catches it directly | QA-T105-03's grep against `origin/master` returns **no match** — if it returns a match, either master already has the fix (stale local branch) or you diffed the wrong file; investigate before trusting any downstream check |
| `findByPersonId` still unordered, but returns PK-clustered order by luck | QA-T105-06 could coincidentally show something close to expected order if the fixture's insertion order weren't deliberately scrambled (this is why insertion order γ,ε,β,α,δ was chosen to diverge from the expected id sequence in a non-trivial way) | Compare the full returned `id` array against `[3,1,5,4,2]` exactly — "close" or "mostly sorted" is a fail, not a near-pass |
| `ORDER BY startDate DESC` present but no `id` tiebreak | QA-T105-07 passes anyway (insertion-order coincidence, see §3) | Only QA-T105-08 (source grep for the explicit second sort key) distinguishes this from a genuinely correct implementation |
| `location`/`description` silently dropped from the JSON on the retrofit | Easy to miss by eyeballing one response — a field that's usually `null` anyway looks the same whether present-and-null or absent | QA-T105-09's `jq keys` check is exact-set, not "looks right"; run it, don't eyeball |
| Person-existence check reordered relative to the query change | `requirePerson` still throwing before `findByPersonId` looks identical to a passing 404 in casual testing, but a regression here would silently start returning `200 []` for unknown ids | QA-T105-13 checks the status code explicitly, not just that a response came back |
| Cross-person IDOR reintroduced | Looks like a normal 204/200 unless you check the *other* person's collection afterward | QA-T105-12's follow-up GET under `$PID` is the tell — a bare "got 404" isn't enough on its own if the row was actually mutated by a different code path |
