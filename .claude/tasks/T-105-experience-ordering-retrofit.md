---
id: T-105
title: Retrofit contract ordering onto the merged Experience resource
repo: cv-domain-service
status: in_progress
owner: backend-developer
branch: fix/experience-ordering
pr:
depends_on: [T-006]
risk: normal
security_review: false
checkpoint:
  stage: 1                    # H1 ratified 2026-08-24; implementation in flight. NOT reviewed, no PR.
  repo: cv-domain-service
  branch: fix/experience-ordering
  worktree: /home/erfeamor/work/cvdl-worktrees/T-105   # created 2026-08-24 at stage 1, branched from 7677fee. CLEAR THIS AT CLOSE-OUT — T-028 makes a lingering path on a done task an exit-1 for qa-env-override.py.
  developer: backend-developer
  reviewers: ["/code-review", "backend-developer (specialist lens, read-only)"]
  risk: normal                # adapter §5: not trivial — it changes the observable behaviour of a live endpoint. A1 re-decides against the real diff.
  security_review: false      # no adapter §5 path in the expected diff (no auth/secrets/IAM/CI). A1 forces it anyway if the real diff disagrees.
  env_slot: 0                 # single-task run, no wave; slot 0 -> domain-service on 8090
  review_round: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-24
  commit: 91a6218
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
  stage2_not_started: |
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
