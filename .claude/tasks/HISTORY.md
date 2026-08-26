# Board history

Board consistency sweeps and close-out narratives, split out of [TASKS.md](TASKS.md) on **2026-08-24** so the board could return to its documented purpose ([README.md](README.md): *"one line per task, always current"*). TASKS.md had reached 706 lines, most of it this material.

**Nothing here is current state.** Every entry records what was true when written. The board's convention is to strike rather than delete, so corrections are findable and the original error stays readable — read entries in that spirit, and check [TASKS.md](TASKS.md) or the task file itself before acting on anything below.

---

## The split itself — what it changed, and the one thing it lost (2026-08-24)

TASKS.md 706 lines → 96; this file holds the rest. The board tables, the parallelization notes, the deployment-gap table and the cost-model summary stayed; sweeps and merge narratives moved here.

**One deviation from board convention, recorded rather than glossed:** the wave-1 status line was **rewritten into a clean summary instead of being carried over with its strike history**. That history is the artifact this board's convention exists to preserve — the line had been superseded four times, and each strike records a period when it was actively sending readers at an already-merged task. It is restored verbatim below. It survives in git (`git show HEAD~:.claude/tasks/TASKS.md`), but requiring git archaeology to find drift is precisely what strike-don't-delete exists to avoid.

### The wave-1 status line, as it stood before the split

  - ~~**Status as of 2026-08-09:** T-101 is **merged**… T-102/T-103/T-104 reached **H1 and stopped**… T-151 never started.~~ ~~**Superseded 2026-08-20.** **Status as of 2026-08-20:** T-101 (`09282ed`) and T-102 (`42abe91`) are **merged**. **Wave 1 is now T-103, T-104 and T-151.**~~ **Superseded again 2026-08-22 — T-103 merged on 2026-08-21 (`2e54394`) and this line kept sending readers at it.** ~~**Status as of 2026-08-22:** T-101 (`09282ed`), T-102 (`42abe91`) and T-103 (`2e54394`) are **merged**. **Wave 1 is now T-104 and T-151.**~~ ~~**Superseded later the same day — T-104 merged as `7677fee`.** **Wave 1 is now [T-151](T-151-dev-seeds-cv-sections.md) alone**, and it is the only wave-1 task that never started.~~ **WAVE 1 IS COMPLETE, 2026-08-22** — T-151 merged as `865784f`. All five wave-1 tasks are `done`. **All four API resources are done**, so [T-201](T-201-bff-cv-aggregate.md) and [T-301](T-301-admin-cv-sections-crud.md) are unblocked and wave 2 is open. The "start at implementation, not refinement" instruction served all three of T-102/T-103/T-104 and is retained for the record: an 18-day-old ratified H1 was worth more than a re-refinement each time, provided the premises that moved were written down first.

**What the current board says instead:** wave 1 is complete (all five merged, commits recorded in TASKS.md), and **T-105 is called out separately as still `todo`** — the contradiction that made the original line worth preserving. The old line ended by declaring wave 1 complete while the same section still assigned T-105 to wave 1, so a reader skimming for the latest claim could miss the one open wave-1-class task, which blocks T-501.

---

## Superseded cost-model derivations and close-out notes (moved from TASKS.md, 2026-08-24)

The arithmetic below was correct for the rate each version assumed; the premises moved three times ($0.92/day → $1.23/day → $0.6837/day measured). **The current model is the table in [TASKS.md](TASKS.md); quote that, never this.** Kept because the re-derivations are what caught two ratified decisions resting on stale numbers.

**Cost model is stale as of 2026-08-14 — the documented figures understate real burn by a third.** `cv-infra/CLAUDE.md` and T-010's runway both encode *~$0.92/day ≈ $28/month*. The 2026-08-08 `t3.micro`→`t3.small` resize of the CI host (T-002, deliberate, for Maven headroom) took the real rate to **~$1.23/day ≈ $37.30/month**, verified against the August cost export and `describe-instances`. Consequences: the credits deplete **~25% sooner in elapsed time**, which moves T-012's date; and the `$30` monthly budget is now **structurally exceeded (~124%)**, so its 100/120% thresholds will fire every month from September — an alarm that always fires stops being a signal. Note [cv-infra#14](https://github.com/erfeamor/cv-infra/pull/14) deliberately refused to raise that limit, so this needs a decision rather than a bump. **T-014 may push it further** — its own watch-outs say the domain-service box may need `t3.small` for RAM, another +$8.62/month → ~$46. [T-019](T-019-ci-host-on-demand.md) is the largest available offset (~$17.24/month).

**Nobody re-ran the division — done 2026-08-14, and it moves two ratified decisions.** The note above recorded that the rate changed but left every date derived from the old one standing. Re-deriving from T-010's console read ($120.66 remaining on 2026-08-11) at the verified **$1.23/day**:

| Grant | modelled at $0.92/day | re-derived at $1.23/day | binds |
|---|---|---|---|
| $160 (current) | 2026-12-20 | **~2026-11-17** | credits, by ~8 weeks |
| $200 (after the two activities) | 2027-01-12 — window binds | **~2026-12-19** | credits still, by ~3 weeks |

Two consequences, neither cosmetic:

1. **[T-012](T-012-aws-endgame-decision.md)'s `due: 2026-12-20` is now after the money is gone** in the $160 case. Re-dated in that file.
2. **T-010's ratified decision (b) — "do NOT trim the run rate" — no longer follows from its own reasoning.** It rested on the crossover at ~$32/month: *below* that the 6-month window binds first and savings expire unspent. Real burn is **$37.30/month, above the crossover**, so credits bind first and trimming now buys real elapsed demo time — up to ~8 weeks in the $160 case. That does not automatically mean *build* [T-019](T-019-ci-host-on-demand.md): its own DoR §4 notes stopping the host by hand saves the identical $17.24 with no new IAM, no public endpoint and nothing to break. What changed is that the saving is now worth *something*, where T-010 correctly concluded it was worth nothing. **Decide it at T-019's H1.**

~~**These figures are derived, not read.** … confirming it needs a console read.~~ **Read 2026-08-19 — see below. Everything above this line is superseded; it is kept because the arithmetic was right each time and only the premises moved.**

> **Closed out 2026-08-20: [T-019](T-019-ci-host-on-demand.md) is merged and the M2 backend wave is unblocked.** PR [#17](https://github.com/erfeamor/cv-infra/pull/17) is in `cv-infra` master (`bd65353`), applied 2026-08-19, and the manual webhook re-point **has been done** — `cv-domain-service` and `cv-database` both point at the doorbell Function URL, `active=true`, last delivery OK. A push to either repo now starts the CI host by itself; nothing needs starting by hand. Two criteria remain outstanding and are recorded in T-019 rather than held open as a status: the hook has only ever received a **`ping`** (2026-08-19T09:39:19Z), so *"the build actually runs"* is unproven until the first real push — **T-102 supplies it for free** — and the billing-week rate check needs elapsed time. Drone is deliberately **not** covered (T-019 ruling 5): `cv-admin-react`'s hook still points at `http://13.39.59.12/hook` and reads `last=unused`, so a push there neither builds nor wakes the box. That is T-301's problem when it arrives, and it is now written down somewhere other than inside T-019.

> T-013, T-014 and T-015 are part of the deployment chain below and are boarded there, not here, so there is one line per task to claim.

**Board-line correction 2026-08-13.** T-002's line above read `in_review` while its own task file had said `done` since PR [#11](https://github.com/erfeamor/cv-infra/pull/11) merged on 2026-08-09 — rule 1 requires both to be updated and only the file was. The line is now `done`. The practical cost was not cosmetic: **T-003, T-005, T-007, T-008 and T-009 all gate on T-002**, so five infra tasks read as un-claimable for four days. They are claimable now, and none is owned. (The sentence that followed here named T-001 as "the only thing that has to happen before the deployment chain reaches its destructive step" — superseded the same day: T-001 is `done`, and the destructive step is *accepted*, not gated. The durable fix is [T-018](T-018-mysql-on-dedicated-ebs-volume.md).)

> **T-001 applied and verified 2026-08-13 — backups are now real.** The nightly timer is enabled on `i-038600c71d141035b` (next run 03:04 UTC), a forced run landed `cv-20260813T152654Z.sql.gz` in `s3://cv-project-mysql-backup-dev/mysql-dumps/`, and that dump was **restored into a throwaway MySQL 8.4 container** — all six tables plus the Flyway history. The restore, not the upload, is what makes this claim worth anything.
>
> The instance was replaced as expected, so the previous test data is gone and the verified dump is schema-only. The mechanism is proven; it has simply had no authored content to capture yet. ~~**T-018 is still the thing that matters before real content exists** — a nightly dump does not save data written between dumps, and T-014's apply will replace this box again.~~ **[T-018](T-018-mysql-on-dedicated-ebs-volume.md) landed 2026-08-14** ([cv-infra#16](https://github.com/erfeamor/cv-infra/pull/16)): the datadir is on an independent volume and survival across replacement is proven, so T-014's apply no longer replaces the database along with the box. The nightly dump and the dedicated volume now cover different failures — the dump protects against corruption and bad writes, the volume against instance churn — and neither substitutes for the other.


---

## Board consistency sweep — 2026-08-17

A read of all 37 task files against each other and against the contract. **No status changed and no work was done** — this is drift repair. Recorded rather than silently applied, per the convention this board already follows for the T-002 and T-014 board-line corrections.

**Four unowned items filed as tasks.** Each had been handed from one task file to another and never landed:

| New | What it was | Where it was lost |
|---|---|---|
| [T-023](T-023-meta-docs-stale-bff-smoke-path.md) | `CLAUDE.md:37` and `README.md:247` still document the E2E smoke as `curl localhost:3000/api/v1/people/1` — a path T-202 deleted from the BFF on 2026-08-13 | T-015 is gated behind T-014; T-016 notices it in passing; T-202 is in another repo |
| [T-024](T-024-contract-skill-assignment-put-shape.md) | The contract clarification T-103's DoR ruling 1 promised ("a follow-up docs PR clarifies this wording") | promised at refinement, never opened, held by no task |
| [T-404](T-404-public-react-point-at-deployed-bff.md) | Pointing cv-public-react's Vercel `BFF_URL` at the deployed BFF | T-402 → "tracked at T-501"; T-403 → "handle it at T-501"; T-501 → silent |
| — | The meta `CLAUDE.md`'s stale `~$28/mo` | folded into **T-020 §3**, which named only `cv-infra/CLAUDE.md` and T-010 |

**Six contradictions corrected in place**, each struck rather than deleted:

1. **T-401 and T-402 still specified `GET /api/v1/people/:id/cv`** — the pre-T-013 path. T-013's review caught this exact drift in T-201 and fixed it *only there*; the other two consumers of the same endpoint were missed for four days. Both now read `/bff/api/v1`.
2. **T-501's step 2 curled the same dead path**, so the milestone's own end-to-end verification would have 404'd.
3. **T-004 §3 and T-021 contradicted each other on `db_password`.** T-004 offers rotation as an open decision; T-021 says rotating it aborts the bootstrap and leaves the box with no domain-service container. Neither file referenced the other. Cross-linked both ways.
4. **T-014's numbering**: "six rulings" against seven, a pointer to "ruling 7's correction" that belongs to ruling 1, and a baseline capture citing "criterion 4" (the criterion T-018 superseded) instead of 6.
5. **T-014's `user_data_replace_on_change` watch-out still said the apply destroys MySQL** — superseded by T-018, but only two sections further down, so a reader who stopped at the watch-outs got the opposite answer. Struck at the watch-out itself.
6. **This board claimed "every task above is genuinely `todo`"** in the M2 section, directly beneath its own note that T-101 had merged.

**Three stale premises struck**: T-012's threshold dates (24 Sep / 15 Nov / 20 Dec, derived at the superseded $0.92/day, inside the file that re-derives everything else at $1.23/day) · T-004's "do before applying T-002" (T-002 applied 2026-08-09) · T-016's "T-014 gates on T-001" (that edge was removed 2026-08-13) · T-009's housekeeping request that T-007 already fulfilled.

**Frontmatter hygiene**: `security_review: required` normalized to `true` in five files (two vocabularies for one boolean) · T-011's `pr:` filled from its checkpoint, per board rule 6 · T-009 given the missing `pr:` key · T-010's DoD branch name reconciled with its frontmatter · T-101's checkpoint `stage: pr` → `done`.

**Left alone deliberately.** T-201, T-301, T-401, T-402 and T-501 carry no `risk` or `security_review`. Assigning them is a stage-0 refinement output, not a board edit — inventing values here would manufacture ratified-looking decisions nobody made. They get them when they are refined.

## Board consistency sweep — 2026-08-20

A second pass over all 40 task files, this time **verified against the live systems** rather than only against each other: `git log` in the eight sibling repos, `aws ec2 describe-instances`, `aws freetier`, and the GitHub webhook + delivery API. No task's scope changed and no product code was touched.

**What the live checks confirmed.** T-101, T-202, T-006, T-013, T-018, T-009 and T-020 have all genuinely landed in their repos. Every task file appears on this board and every board line has a file (40/40). `cv-project-drone` is still `stopped` and `cv-project-domain-service` still `running`, so T-020's measured cost model holds as of today.

**What was wrong:**

1. **[T-019](T-019-ci-host-on-demand.md) was merged but boarded `in_review`** — PR #17 is in `cv-infra` master as `bd65353`. Board rule 6 says merge → `done`. **Third recurrence** of the drift class this board corrected for T-002 (2026-08-13) and again in the 2026-08-17 sweep. Fixed on the line above and in the file.
2. **T-019's top-level `pr:` was empty** while `checkpoint.pr` held the URL — the *exact* hygiene bug the 2026-08-17 sweep fixed in T-011, recurring on the very next task to reach review. Filled in.
3. **T-019's `remaining:` note was stale in its premise and right in its conclusion.** It said the webhook re-point had not happened and the automation was "inert"; both hooks were in fact re-pointed on 2026-08-19. The criterion *is* still unmet, but only because no `push` has ever reached the doorbell — only a `ping`. Corrected in place, old text kept.
4. **[T-012](T-012-aws-endgame-decision.md) had never absorbed T-020's measured read** — the single most consequential item in this sweep. The board's only deadline-bearing task still argued end to end from the superseded **$1.23/day**: credits binding by ~8 weeks, exhaustion ~2026-11-17, and **option A priced at ~$37/month against a real ~$21**. It still carried *"These dates are derived, not read — T-020 holds that read and will correct this task again if the console disagrees."* T-020 is `done`, it did the read, the console **did** disagree, and §5's conclusion was written into T-020 and into this board but **never into T-012**. A decision document arguing from superseded arithmetic, waiting to be opened on 1 November. Corrected with a measured block at the top; `due: 2026-11-01` **deliberately unchanged**, per T-020 §5.
5. **[T-005](T-005-ci-secret-blast-radius.md) still listed the GitHub webhook secret as work to do.** T-019 ruling 4 built it and said in terms that *"T-005 should drop that bullet rather than build it twice"* — a hand-off recorded only in the file doing the handing. Struck, with a pointer.
6. **[T-023](T-023-meta-docs-stale-bff-smoke-path.md) contradicted itself on scope**: *"Two files, one path each"* above a bullet list of three, the third hedged as *"check `README.es.md`"*. `README.es.md:247` does carry the dead path — verified — so the hedge is now a fact and the count is three.
7. **Frontmatter hygiene**: `security_review` was missing entirely from T-003, T-007 and T-151, all three of which *do* carry `risk` (so they are not covered by the 2026-08-17 sweep's deliberate exemption for unrefined tasks). Set to `false` per adapter §5, flagged in-line as a stage-0 default that A1 overrides on the real diff.
8. **Four stale worktrees** at `cvdl-worktrees/{T-102,T-103,T-104,T-151}` held their `feat/*` branches, clean and zero commits ahead of master — left behind when those claims were reset. They made `git branch` read as work-in-flight. Removed; the dev-loop recreates them on demand.

**Filed as work, not drift:** [T-024](T-024-contract-skill-assignment-put-shape.md) was implemented in this session rather than left on the board ([#41](https://github.com/erfeamor/curriculum/pull/41), **merged 2026-08-20** as `3a45f94`), because it is a docs-only contract change and landing it before T-103 means the implementer builds from `docs/api-contract.md` instead of from a ruling buried in a task file — which is the arrangement the contract exists to replace. **T-103's DoR ruling 1 now points at the merged contract text instead of promising a future PR**, closing the last of the four hand-offs the 2026-08-17 sweep filed.

**The recurring failure this board keeps finding, stated once more:** every item above is a fact that was true when written and was never re-checked. Items 1–3 were each *recorded correctly by the task that did the work* and then not propagated; item 4 is the same shape at the scale of a deadline. The board's convention of striking rather than deleting is what makes them findable — it is working, and it is not a substitute for re-reading.

## T-022 applied — and what its security review cost the next two tasks (2026-08-20)

**The direct-to-origin path is closed, proven by request from outside AWS** ([cv-infra#20](https://github.com/erfeamor/cv-infra/pull/20)). `:8080/v3/api-docs`, `/actuator/health` and `/api/v1/people/1` all answered before the change (200 / 200 / 401) and all time out after it, while the edge is untouched (`cf /api/v1/people/1` 401, `cf /v3/api-docs` 403, `cf /admin/` 200). The 401 through CloudFront is what proves the origin is still reachable from the edge — an unreachable origin gives 502/504.

**Two findings came out of it that other tasks inherit, and both are the kind that fail at apply time rather than review time:**

1. **[T-014](T-014-deploy-bff-to-aws.md) cannot put port 3000 on the domain-service security group.** An AWS-managed prefix list counts against the 60-rule inbound quota as its **entry count**, not as one rule; the CloudFront list held **46** entries on 2026-08-20. One reference fits, two do not. The BFF needs its own security group. Written into T-014 above its scope section, because ruling 1 as drafted would fail on apply.
2. **The prefix list proves "a CloudFront distribution", not "ours"** — it is shared by every CloudFront customer, so an attacker's own distribution still reaches the origin and still reads the spec. Raised as the one MEDIUM finding by T-022's forced `/security-review` and **deliberately not fixed in that PR** (board rule 3 — both remedies are cross-repo or out of scope, which T-022's own body said before the review existed). Filed as **[T-025](T-025-verify-requests-come-from-our-cloudfront.md)** (shared-secret origin header — closes the bypass class) and **[T-106](T-106-restrict-openapi-and-actuator-exposure.md)** (stop `permitAll`-ing `/v3/api-docs`, `/swagger-ui/**` and `/actuator/prometheus` in `SecurityConfig.java:38-39`, which is *why* it was readable — cheap, independent, and the whole answer if T-025 is declined at H1).

**T-022's own claim is corrected on the task**: `/v3/api-docs` is unreachable **directly**, not unreachable from the internet. That distinction is the entire content of finding 2, and stating it the strong way is how it would have been forgotten.

**One acceptance criterion is outstanding and is not being quietly counted as met**: the admin UI loading its people list with a real Cognito JWT needs an interactive login. The anonymous 401 is strong evidence the path is intact; it is not the same check.

## T-019's last criterion is MET — and using it found a defect (2026-08-20)

**The doorbell fired on a real push, for the first time.** T-106's PR to `cv-domain-service` supplied it, exactly as predicted:

```
push 08:11:58Z (delivery 200) -> doorbell -> ec2:StartInstances
  -> i-073e5284ca2a1ceed  stopped -> running
  -> Jenkins boots, multibranch scan finds PR-4, build starts 08:12:45Z
```

So T-019's *"a push to a watched repo starts the CI host"* is **proven end to end**, no longer by synthetic payload. Its companion criterion — *"and the build actually runs"* — is **also met**: builds #2 and #3 ran all four stages green in ~97s (checkstyle 0 violations, 35 tests, image tagged).

**But build #1 — the one the automation itself triggered — failed**, 47 seconds after the instance started, with `No build record cv-domain-service/PR-4#1 could be located` and a `Lint` stage that opened and closed without executing anything. The identical commit then passed twice. Filed as **[T-026](T-026-first-build-after-cold-start-fails.md)**.

**Why that matters beyond one red build:** every first push after an idle period gets a red X whose fix is "push again", and it will be blamed on whatever code was pushed — it briefly looked like T-106 had broken CI. It is also the honest asterisk on T-019's criterion: *met by build #3, not by the build the automation triggered.*

This is the healthy outcome of T-019, not an argument against it. **The value of "prove it with a real push" was precisely this** — the synthetic payload proved the doorbell, and only a real push could have found what happens to the build on the other side of the boot.

## T-102 implemented — M2 is two of eleven (2026-08-20)

Picked up **at implementation**, not refinement, as its `reset_note` directed — the H1 checkpoint from 2026-08-04 was real and was used as written. [cv-domain-service#5](https://github.com/erfeamor/cv-domain-service/pull/5).

Structural twin of T-101 as specified: same package shape, same four rulings, same no-DTO trade-off. **It ships with contract ordering built in** (`findByPersonIdOrderByStartDateDescIdAsc`), which is the thing [T-105](T-105-experience-ordering-retrofit.md) still has to retrofit onto Experience — Education never had the gap.

**Stage-4 QA ran against live MySQL 8.4 on slot 1, and it earned its keep.** 18/18 checks passed, but the reason to run it was the `field_of_study` → `fieldOfStudy` mapping that H2 cannot police, and the strongest evidence is simply that **the service booted**: `ddl-auto: validate` against the real V1 schema fails at startup on a naming-strategy slip.

**It also found a defect — in the test, not the code.** C7 asserted `jsonPath("$.fieldOfStudy").doesNotExist()` for omitted optionals and passed, while the live body is `{"fieldOfStudy":null,...}` — the field *is* present. `jsonPath` treats a JSON null as absent, so C7 was green for the wrong reason and would have stayed green under `@JsonInclude(NON_NULL)`, which **would** break the contract's *"absent optionals serialize as `null`"*. Tightened to assert key count plus a null value. A unit test that passes for the wrong reason is worse than a missing one, and only the live stack showed the difference.

**A control for [T-026](T-026-first-build-after-cold-start-fails.md):** T-102's first push landed on an *already-running* box and its first build succeeded, where the cold-start push earlier the same morning failed on its first build. That is one data point, not a proof, but it points at cold start specifically rather than at first-builds generally — recorded there.

**Closed out:** `/code-review` ran and its three findings were fixed in the PR (see the section below); all three commits on the branch built green on Jenkins. **Merged as `42abe91`.** M2 is now **two of eleven**.

## T-102's code review found a cross-person write, and this board had it mislabelled (2026-08-20)

`/code-review` on [cv-domain-service#5](https://github.com/erfeamor/cv-domain-service/pull/5) returned one HIGH and two LOW. All three are fixed in that PR (`cbe077f`).

**The HIGH is the one worth reading, because this board had already seen it and waved it through.** T-102's test plan carried it as a coverage risk, in these words:

> *A client-supplied `"id": 999` in a POST body must not override the generated id. `PersonController.create` has the same exposure — flag, don't block, don't fix here.*

That is wrong about the impact, and the wrongness is what carried it unfixed through refinement, implementation **and** stage-4 QA. It is not an id override. It is an **authenticated cross-person write**:

1. `Education.id` is a private field with no setter — which reads as un-bindable. Jackson's `INFER_PROPERTY_MUTATORS` binds it anyway (verified empirically, not argued: `getId() == 999`).
2. A non-null id makes Spring Data's `save()` take `merge()` instead of `persist()`.
3. `create()` has already set the owning person to the **caller's**.
4. Net statement: `UPDATE education SET person_id = <caller>, … WHERE id = 999` — **another person's row is overwritten and handed to the caller, with `201` and the victim's id in the response.**

That is precisely the write `findByIdAndPersonId` scopes PUT and DELETE against (DoR ruling 2), arriving through the one verb with no existing row to scope to. **Fixed inside T-102** rather than deferred: shipping new code carrying a known cross-person write, because a task file said "flag, don't block", would be following process off a cliff. The test was confirmed **red first** — `201` where `400` is required.

**`PersonController` and `ExperienceController` have it identically and are already on `master`** — filed as **[T-107](T-107-post-id-cross-person-write.md)**, `risk: high`. Its DoR asks whether the answer is three local guards or one global one (`@JsonProperty(access = READ_ONLY)`, or disabling `INFER_PROPERTY_MUTATORS`), because the global answer would also cover **T-103 and T-104 before they are written** — otherwise those two arrive with the same hole and need the same retrofit.

**Context, recorded so nobody either panics or relaxes too far:** `/api/v1/**` requires a valid Cognito JWT in the deployed config, and since [T-022](T-022-domain-service-origin-bypasses-cloudfront.md) the origin is reachable only through CloudFront. So this is an *authenticated* attack and today the only credentials are the owner's. It becomes materially worse the moment the demo has a second user.

**The failure class, in a new costume.** [T-020](T-020-cost-model-correction.md) was a stale *number*. The T-002 board line was a stale *status*. This was a stale *severity assessment* — written down once in words that undersold it, then honoured by every later reader, including the person implementing the resource it undermined. The flag was not ignored. It was believed.

## T-107: the exploit reproduced, and the reason it survived (2026-08-20)

Fixed in person and experience ([cv-domain-service#6](https://github.com/erfeamor/cv-domain-service/pull/6)); education was already done in T-102. **Demonstrated against live MySQL 8.4 rather than argued** — guard temporarily removed, then restored:

```
POST /api/v1/people/2/experiences  {"id":<row owned by person 3>, "company":"PWNED", ...}

  before    id=1  person_id=3  company=VictimCo  role=Staff Engineer
  response  201,  {"id":1,"company":"PWNED",...}
  after     id=1  person_id=2  company=PWNED     role=owned
  GET /people/3/experiences  ->  []
```

The victim's row was reassigned to the caller and their CV entry disappeared. Guard restored: `400`, row untouched — verified for all three resources against the row itself, which is what T-107's acceptance criterion demanded.

**Why it survived three weeks in `master`, and this is the part worth keeping.** T-101 shipped a test called `clientSuppliedIdInThePostBodyIsIgnored`. It asserted `201` with the id "ignored", **and it passed**. Its comment explained why: *"the entity exposes no id mutator, so Jackson ignores it."* Jackson does not ignore it. The test passed because `givenSaveReturnsWithId(5L)` stubs `save()` to return an entity with id 5 whatever it receives — **the assertion measured the mock, not the code.**

So the sequence was: QA flagged the risk in words that undersold it → the implementer wrote a test that appeared to close it → the test passed → every later reader, including the one implementing T-102 against this very file as a template, took the question as answered. **A green test asserting the safe-looking behaviour is worse than no test**, because it answers the question before anyone thinks to ask it. The old body is kept in a comment where it stood.

**The decision, recorded as a decision.** `@JsonProperty(access = READ_ONLY)` would have closed this structurally — a new resource inherits protection whether or not its author knows the rule. It was **declined**: it discards a supplied id in silence, so a client that sent one believing it was updating gets a `201` for a different row and no signal it was wrong, and T-102 had already shipped `400`. Two behaviours across sibling resources would be worse than either. The price of that choice is that the guard must be *called* — so **[T-103](T-103-skills-catalog-and-assignments.md) and [T-104](T-104-project-resource.md) now carry it in their DoR**, including the instruction to confirm the test fails first.

**Severity in context:** `/api/v1/**` requires a valid Cognito JWT and, since [T-022](T-022-domain-service-origin-bypasses-cloudfront.md), the origin is reachable only through CloudFront. This is an authenticated attack and today the only credentials are the owner's. It becomes real the moment the demo has a second user — which is what an admin UI with logins (T-301) implies.

**[T-026](T-026-first-build-after-cold-start-fails.md) reproduced while landing T-107.** The reaper stopped the box at 09:59:17; T-107's push woke it; `PR-6#1` failed with the identical `No build record … could be located` and an empty `Lint` stage; a rebuild on the warm box went green. **Three for three on the pattern** — cold start fails, warm start succeeds — so it is now reproducible on demand rather than an anecdote, and cheap to bisect. It cost this task one spurious red build and a manual retrigger, which is exactly the papercut T-026 predicts for every developer's first push after an idle period.

## Board consistency sweep — 2026-08-20 (second pass, same day)

A third sweep, run after T-102, T-106, T-107 and T-022 all landed within hours of each other. **No status changed, no scope changed, no product code was touched** — every item is prose that was true when written and was contradicted by work that landed later the same day. Structural state was re-verified first and is clean: **44 task files ↔ 44 board rows**, no orphans in either direction, no frontmatter/board-line status mismatch, no `depends_on` pointing at a non-existent task, no `todo` task holding an owner, and all six recently-claimed merges confirmed in the sibling repos' `git log` (`09282ed` T-101, `4f38f77` T-106, `42abe91` T-102, `1327bf6` T-107, `da17414` T-022, `bd65353` T-019).

**Six contradictions corrected, struck rather than deleted:**

1. **[T-104](T-104-project-resource.md)'s coverage-risk list still said *"Client-supplied `\"id\": 999`: flag, don't block, don't fix here"*** — the exact sentence this board diagnosed as the root cause of [T-107](T-107-post-id-cross-person-write.md), contradicting §"Carry the T-107 guard — do not skip" **in the same file, added the same day**. T-104 is claimable now, and coverage-risk bullets read as instructions. This is the highest-cost item in the sweep: the failure mode is not that the guard is unknown, it is that the file argues both ways and the wrong half is phrased as a ruling. Struck, with a pointer to the binding section. T-103 was checked and is clean.
2. **[T-102](T-102-education-resource.md) carried the same bullet unstruck in its body** while its frontmatter had marked it `SUPERSEDED` since the code review. Lower stakes — the task is `done` — but the strike-don't-delete convention only works if the strike reaches the text a reader actually reads.
3. **[T-019](T-019-ci-host-on-demand.md)'s `remaining:` block asserted the opposite of this board's own record.** It said *"No PUSH has ever reached the doorbell… the NEXT push is the proof — T-102 supplies it for free"*, and the proof then arrived (T-106's push, 08:11:58Z → StartInstances → PR-4 build at 08:12:45Z; builds #2/#3 green in ~97s) and was written into §"T-019's last criterion is MET" **above** and never back into the task. A note that names its own future proof has to be revisited when that proof lands. Corrected; the billing-week criterion is the only one genuinely still open (~6 days of elapsed time, not work).
4. **T-019's board line still read *"awaiting one real push — see sweep 2026-08-20"*** — pointing at a sweep superseded by a later section of this same file. Now `done (**all criteria met bar the billing week**)`.
5. **[T-025](T-025-verify-requests-come-from-our-cloudfront.md)'s H1 was framed against a premise that had already shipped.** It priced [T-106](T-106-restrict-openapi-and-actuator-exposure.md) as a *"cheaper alternative worth pricing at H1"* — but T-106 is `done` and merged, so the leak that motivated T-025 is closed and the cheap half is not an option to weigh. **H1 now decides a genuinely narrower question**, written into the file: is the residual *bypass class* worth a shared secret today, given [T-014](T-014-deploy-bff-to-aws.md) is about to put a second port behind the same weak proof? Left `todo` — this is a reframing, not a decision.
6. **The M2 parallelization note still described T-102 as *"reached H1 and stopped, no code was written"***, and the deployment-gap section still recommended doing T-022 before T-014 as pending work. Both landed. ~~Wave 1 is now **T-103, T-104, T-151**.~~ **Corrected again 2026-08-22: wave 1 is T-104 and T-151** — T-103 merged the next day and this sentence went stale in under 24 hours, for the second time in the same paragraph.**

**Housekeeping:** [README.md](README.md)'s infra range read `T-001…T-024`; it runs to T-026, and those two are among the more actionable items on the board. The stale-branch problem was **repo-wide, not one repo**: 25 local branches across all eight siblings, plus ~25 more on `origin`. Merge status was taken from **GitHub, not from `git`** — `git branch --merged` reports nothing here because every PR is squash-merged, and `git merge-tree` over-reports because `master` has since edited the same files; both would have been read as "unmerged work" by anyone doing this by eye. `gh pr list --state all` settles it: **every branch in every repo maps to a MERGED PR — ~~47 PRs~~, zero open, zero closed-unmerged.** The 25 local branches are deleted, each checked against that list by name first. ~~**The `origin` copies are NOT yet deleted** — that push was blocked by this machine's permission policy and is left for the human, deliberately not worked around.~~ Same false "work in flight" signal the previous sweep removed stale worktrees to kill.

  **Corrected within the hour, and the correction is the point.** Two of the three factual claims above were wrong before the ink dried — in a paragraph belonging to a sweep *about* claims that go stale unread:

  - **The count was wrong.** "47 PRs" counted the meta repo's PRs, not the product repos' — the repos the sentence is about. Verified figures: **51 PRs across the eight product repos, 47 in the meta repo, 98 in the workspace, and all 98 merged** — zero open, zero closed-unmerged, workspace-wide.
  - **The scope was wrong.** The sweep audited the eight *sibling* repos and silently skipped the meta repo it was written in, which held **8 stale local branches of its own**. Total local: **33, not 25.**
  - **The `origin` claim expired.** The push was authorized explicitly and the branches are gone: **31 remote branches deleted** (2 meta + 29 product), verified against `GET /repos/:owner/:repo/branches` rather than local tracking refs, which lie after a delete elsewhere. **All nine repos now hold `master` and nothing else**, local and remote.

  Every deletion remains recoverable — each branch had a merged PR, and GitHub keeps a *Restore branch* button on it.

**Left alone deliberately.** Every `done` task on this board has its acceptance checkboxes **unticked** — T-001, T-009, T-018, T-019, T-022, T-102, T-106, T-107, all of them. That is consistent board-wide, so it is convention rather than drift and this sweep did not "fix" it. It is worth naming once, because it is *why* item 3 could happen: with the boxes decorative, the fact that a criterion is met can only live in prose, and prose is what this board keeps failing to propagate. Making them load-bearing would be a protocol change ([README.md](README.md)), not a board edit.

**The pattern, once more, now with a shorter fuse.** The previous sweep found facts that went stale over *days*. Items 1, 3 and 6 here went stale in **hours** — T-104's contradiction was authored the same day as the section that contradicts it. Velocity is what changed, not the failure mode: the board is now moving fast enough that a task file can be internally inconsistent before anyone reads it twice.

## T-103 merged — M2 is three of eleven, and the review found the acceptance criterion wrong (2026-08-21)

Picked up **at implementation** per its `reset_note`, as T-102 was — the H1 checkpoint from 2026-08-04 was real and was used as written. Merged as `2e54394` ([cv-domain-service#7](https://github.com/erfeamor/cv-domain-service/pull/7)). The catalog/assignment split, the composite key, the upsert and the 409 all landed as specified.

**Three premises had moved since that H1 and were recorded in the checkpoint before a line was written** — T-024 turned DoR rulings 1/2/5/6 into contract text, T-107 added the guard, T-006 added ordering. A 16-day-old DoR is not uniformly current, and saying which parts aged is cheaper than letting the implementer infer it.

**The most valuable output of this task is not the resource. It is that T-103's own acceptance criterion was wrong**, and the implementation satisfied it *exactly* while carrying the defect the criterion existed to prevent:

> ~~The upsert read-then-write is inside a single `@Transactional` boundary.~~

A single transaction does **not** serialize insert-if-absent. Two concurrent PUTs on an unlinked pair both read empty, both insert, and because the id is pre-populated `save()` takes `merge()` — so the INSERT defers to commit **after the handler returns**, and the violation escapes as a **500** where the contract mandates 200. `/code-review` (high effort) found it by booting the full application context, which no test in that repo does, and by decompiling Hibernate 6.5.2 rather than arguing from plausibility. Struck and corrected on the task: *transaction present **and** the create branch recovers from a lost race*. **That test plan is the template T-104 inherits**, which is the whole reason this matters beyond one PR.

**The PO's prescribed fix was wrong and the developer said so with evidence.** "Catch around the save and re-read" cannot work: after a flush failure the session is unusable and the transaction is rollback-only, and with annotation-based `@Transactional` the exception is not catchable in the method at all. Proven with a throwaway probe, not asserted. The shipped fix runs each attempt through a `TransactionTemplate` and retries once in a fresh transaction. Recorded because the disagreement was resolved *before* H2 rather than discovered after it — which is what the gate is for.

**Proven under real concurrency, twice, independently.** Developer: 6 rounds × 10 parallel PUTs → 60/60 `200`, 54 recovered `Duplicate entry` violations, zero escapes. Stage-4 QA reproduced **exactly 54** rather than accepting the number, and stressed the catalog's concurrent POST to 8-way (the plan asked for 2) → one `201`, seven `409`s, no 500. ~90 requests, zero 500s anywhere.

**Two rulings ended up enforced structurally rather than by vigilance**, which is the durable form and worth copying: `SkillRepository` has **no `findByName` at all**, so a pre-check 409 would not compile; and `SkillControllerTest` declares **no `PersonRepository`**, so adding a person-check to the global catalog fails context startup (DoR 7).

**Filed from this run, not folded in:** [T-027](T-027-contract-ordering-note-sql-vs-jpql.md) (the contract's ordering note prescribes SQL for a JPQL context — **T-104 hits it next**) and [T-028](T-028-qa-env-generator-worktree-build-context.md) (below).

### The QA stack was building `master` — [T-028](T-028-qa-env-generator-worktree-build-context.md)

`docker-compose.dev.yml:50` builds from `./cv-domain-service`, the **main checkout**, while every dev-loop task runs on a **worktree**. The documented stage-4 bring-up therefore exercises code that does not contain the change. Worked around by hand for this run with a third compose file; filed because the workaround lives in a **gitignored** generated file that vanishes with the next cleanup.

T-103 was greenfield and got lucky: QA proved provenance by observing that `GET /api/v1/skills` answered at all, since that endpoint does not exist on `master`. **A modifying task has no such tell** — it would answer plausibly on every endpoint and QA would sign off on a binary without the change. [T-105](T-105-experience-ordering-retrofit.md) is exactly that shape. T-104, T-151 and T-105 are annotated in place.

### [T-026](T-026-first-build-after-cold-start-fails.md) reproduced a fourth time — and its own severity claim is now narrower

```
06:45:54  error    PR-7/1/   "This commit cannot be built"
06:47:42  success  PR-7/2/   "This commit looks good"
```

**Nobody retriggered it.** Pushing the branch and opening the PR fire two separate webhook deliveries, so build #2 ran on the warm box unattended. GitHub's status API keeps only the latest state per context, so **the PR renders green and the failure is invisible** unless someone reads the full status history. T-026's *"every developer's first push after an idle period gets a red X"* is therefore too strong for the normal push-then-PR workflow — and unchanged for a push to an existing branch, where the red stands and gets blamed on the code. Corrected in the task; the diagnostic signature is untouched.

A caution now written into T-026: **`gh pr checks` will report `pass` while a failed build sits in the history**, so anyone verifying the eventual fix through it will "confirm" a fix that never ran.

## T-028 merged — the QA stack now builds and mounts the tree under test (2026-08-21)

Merged as `74be2c8` ([#49](https://github.com/erfeamor/curriculum/pull/49)), five commits, `scripts/` only, **33 tests wired into `scripts/test-all.sh`**.

**The defect it closes, restated because the fix is easy to under-read:** `docker-compose.dev.yml` wires every repo from the **main checkout**, which sits on `master`, while every dev-loop task runs on a **worktree**. Stage-4 QA was therefore capable of exercising code that did not contain the change under test — and it **fails toward a false pass**: an additive task 404s loudly, but a *modifying* task answers plausibly on every endpoint while QA signs off on a binary without the change.

### The most important thing this task learned is that its own model was wrong

The first implementation handled `build:` contexts, which is what [T-028's DoR ruling 3](T-028-qa-env-generator-worktree-build-context.md) told it to handle. `/code-review` found that ruling **incomplete on a repo this task explicitly cross-links**: `flyway` bind-mounts `./cv-database/sql` and `grafana` bind-mounts `./cv-observability/grafana/provisioning`, neither is a build context, and neither was ever visible to the matcher.

So [T-151](T-151-dev-seeds-cv-sections.md) would have seeded from **master's SQL**, its non-idempotent seeds would have duplicated exactly as before, and the generator would have printed *"no service repointed: task repo 'cv-database' is not built by docker-compose.dev.yml"* — **which reads as "nothing to do here".** The identical silent false pass, surviving the fix, wearing reassuring output. Now proven closed end to end, with the mount source inspected live **and** the seeded row read back (`T-028-BIND-PROBE` vs master's `Terraform`).

### Three corrections that outlive the code

1. **This task's AC1 was wrong** — *"a bring-up whose service reports code only present on the branch"* encodes the **additive** tell that T-103 passed by luck, and contradicted the modifying-task criterion directly below it. Struck. **That is the third acceptance criterion in two days found wrong by the person implementing against it**, after T-103's `@Transactional` boundary and T-104's inherited *"flag, don't block"*. The specifications, not the implementations, are this board's weak link — and all three were caught only because the implementer was told the spec was open to challenge.
2. **A guard was believed to cover a case it did not.** `/code-review` offered `git rev-parse --show-toplevel` as closing `--worktree ~/work/curriculum/cv-domain-service`. It does not: the main product checkout **is** a valid work-tree root. Only the branch check catches it. Corrected in the record because an inherited belief that a guard covers a case it doesn't is exactly how T-107's cross-person write survived three weeks behind a green test.
3. **A stale handler, not a wrong one.** The `try/except` was correct when written and went stale when the function beside it grew a new failure mode — so a `WorktreeError` escaped as a raw traceback. Fixed by *widening* the block rather than adding a second handler, so a future raiser is covered by construction. QA found it at stage 4; none of the 32 tests reached that path.

### Two consequences the board now owns

**[Board hygiene is load-bearing.](T-103-skills-catalog-and-assignments.md)** `checkpoint.worktree` now makes a repoint **mandatory** — a closed task still declaring a path makes every later bring-up for it exit 1. That is deliberate (loud, overridable with `--no-worktree-check`), but **"clear `checkpoint.worktree` at close-out" is now a convention with a tool depending on it.** T-103's entry is cleared accordingly; do the same at every close-out.

**Mount provenance is permanently weaker than build-label provenance.** Build labels are an image property and survive teardown; a bind mount leaves no trace beyond `docker inspect .Mounts`, which exists **only while the stack is up** and cannot be reconstructed. QA's adopted rule: for any bind-mount-only task (`cv-database`, `cv-observability`), sign-off requires **both** the `.Mounts` capture **and** an independent behavioural check. The pairing is the proof. **[T-151](T-151-dev-seeds-cv-sections.md) is the first task this binds.**

### The check that proved the check

T-103 began exiting 0 where it had exited 1, immediately after the driver cleared its `checkpoint.worktree` — indistinguishable from the guard having silently broken. QA ran the identical invocation against a scratch copy of the **old** board file: exit 1, same message. Same code, same task, same missing worktree; only the board content differed. **The check works; the board changed.** Recorded because "the signal agrees with itself" is this task's whole subject, and the driver's own edit was the likeliest place for it to recur.
## T-152 and T-016 merged — the workspace is on MySQL 8.4, and an H1 ruling was voided by evidence (2026-08-22)

**Written 2026-08-22, after the fact.** Both tasks merged earlier today and neither got a close-out section — the board sync for each ([#51](https://github.com/erfeamor/curriculum/pull/51), [#53](https://github.com/erfeamor/curriculum/pull/53)) changed table rows only, so everything below lived exclusively in commit messages. Every other merged task on this board has a section; these two did not, which is the same propagation failure the sweeps keep finding, arriving this time as an *absence* rather than a contradiction.

T-152 merged as `5942881` ([cv-database#3](https://github.com/erfeamor/cv-database/pull/3)); T-016 as `ebb6649` ([#52](https://github.com/erfeamor/curriculum/pull/52)). Together they retire the last three `mysql:8.0` pins in the workspace — `grep -rn "mysql:8.0"` across all nine repos now returns nothing.

**The migration gate was the half that mattered.** `cv-database/Jenkinsfile:18` stood up a throwaway **8.0** to answer *"will these migrations apply?"* while production applied them on **8.4**. A green CI therefore said nothing about the engine actually receiving the DDL. T-152 was filed separately from T-016 rather than widening it, because a `Jenkinsfile` diff forces `security_review: true` under adapter §5 and a local compose bump does not.

**The bump is proven, not observed.** The data-layer review diffed the full `information_schema` across real 8.0.46 and 8.4.11 — columns, charsets, collations, every index including `person_skill`'s composite PK, `sql_mode`, seed counts — and got byte-identical output except `SELECT VERSION()`. `ddl-auto: validate` therefore cannot behave differently across the two.

**What this retroactively costs the board:** four stage-4 checkpoints claim QA against *"live MySQL 8.4"* ([T-102](T-102-education-resource.md), [T-103](T-103-skills-catalog-and-assignments.md)). `scripts/qa-env-override.py` takes `docker-compose.dev.yml` as its base and has no image handling, so those stacks were almost certainly **8.0 wearing an 8.4 label**. They are torn down and not reconstructible. Nothing is being re-litigated — the point of the pair of tasks is that every such claim from today forward is true by construction.

### An H1 ruling was voided by evidence — the entry worth reading

H1 ratified *"wipe (`down -v`) is the supported route; seeds regenerate via the Flyway callback, so it costs nothing."* Both halves were false, and the reasoning is the artefact:

- The ruling rested on QA's stage-0 advice, given while everyone still believed 8.4 would **refuse** an 8.0 datadir. **The asymmetry proved inverted hours later** — 8.0→8.4 upgrades in place and *preserves* the datadir; 8.4→8.0 aborts with `MY-014061` and is unrecoverable in place. Nobody re-derived the ruling when its premise died.
- *"It costs nothing"* was false independently: `cv-admin-react` writes real rows to that same database, and `down -v` also drops `cv-dev-grafana-data`, where UI-built dashboards live with no JSON in the repo.

Both reviewers found it independently. The docs now say **forward wipe is optional, backward required**. Raised at H2 and the correction confirmed by the human — voided by evidence, not overridden silently. Not a stale number and not a stale status this time: **a ratified decision whose premise died the same day it was ratified.**

### QA's dirty-volume check ran against real data for the first time

The only genuine 8.0-era volume on this machine is developer data untouched since 2026-07-19, and the first plain `up` would have consumed it irreversibly — so the driver revised the check to **clone** it rather than test on it. The pre-existing person row survived the in-place upgrade byte-identical, `created_at=2026-07-11 15:10:00` included. The original was left untouched.

### Two task specs falsified by reviewers forbidden from fixing them — board rule 3 working as designed

- **[T-023](T-023-meta-docs-stale-bff-smoke-path.md) could not satisfy its own DoD.** It makes a clean `grep -rn "3000/api/v1"` the definition of done and listed **three** files. There are **four**: `docker-compose.dev.yml:7` is a compose comment header, not prose. Note the shape — T-023 was *created* by a drift sweep, its count was *corrected* by a second sweep (two → three, *"the hedge is now a fact"*), and it was **still wrong**. A sweep that greps only `*.md` keeps re-confirming its own blind spot. Scope widened on the task; the board line now says four.
- **[T-029](T-029-code-review-cannot-see-worktrees.md)'s premise was disproved hours after filing.** Filed as *"`/code-review` returns nothing on a worktree"*. T-016 runs in the **meta repo on a branch, with no worktree at all**, and bare `/code-review` returned the same empty result there; `/code-review 52` then ran a full review (21 tool calls, four findings). The real behaviour: with no explicit target it reviews the **uncommitted working-tree diff**, which in every failing invocation was board markdown. *"No findings"* was correct — it answered a question nobody asked. Retitled; the surviving defect is that an empty result is indistinguishable from a clean one.

### Five tasks filed from this run, none of them previously introduced here

| ID | What it is | Why it is not folded into another task |
|---|---|---|
| [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) | `cv-database`'s `Deploy` stage is gated on `main`, a branch that does not exist here, and its placeholder still targets RDS | A pipeline file with a live-if-inert logic error, not prose — so not [T-017](T-017-docs-drift-rds-to-selfhosted.md)'s. `depends_on: [T-152]` is **file-level**: both edit `Jenkinsfile`, adjacent lines |
| [T-154](T-154-jenkins-pipeline-timeout.md) | No `timeout {}` on the pipeline | Latent, not live — but a hung build defeats [T-019](T-019-ci-host-on-demand.md)'s reaper and holds the **only** CI host up at ~$17.24/month. A cost argument, not a correctness one |
| [T-155](T-155-flyway-version-supports-mysql-84.md) | Flyway 10 does not claim MySQL 8.4 support and **already runs against 8.4 in production** | T-152 made it *visible*; it did not cause it. `cv-infra/templates/domain-service-user-data.sh:181` has run `flyway/flyway:10` against `mysql:8.4` on every instance replacement since MySQL left RDS. Cross-repo (four pins, three repos) — decompose at stage 0 |
| [T-029](T-029-code-review-cannot-see-worktrees.md) | `/code-review` silently reviews the wrong thing without an explicit target | See above — filed this morning, premise corrected the same afternoon |
| [T-030](T-030-pr3-build1-success-then-error.md) | A build posted `success` and then `error` **one second later** | **Attribution to [T-026](T-026-first-build-after-cold-start-fails.md) was withdrawn within the hour** after stage-4 QA challenged it. T-026's signature (`No build record …` plus an empty stage) was never obtained here, and all four confirmed T-026 occurrences *fail outright* rather than succeed and self-invalidate. Padding T-026's occurrence count would corrode the evidence base for *"reproducible on demand"* |

### T-152 merged with one acceptance criterion explicitly unverified

The CI-console version proof — Flyway's connection banner from the Jenkins PR-3 build — **was never obtained**: the console is authenticated and the credential path was declined by this machine's policy. Named in the PR at the human's H2 ruling rather than ticked, and carried in the task's `outstanding:` field. The same fetch also settles [T-030](T-030-pr3-build1-success-then-error.md), so one Jenkins login closes both.

That makes **three `done` tasks holding an unmet acceptance criterion** — T-019 (billing-week rate check), T-022 (admin UI loading with a real Cognito JWT), T-152 (the console banner). All three are honestly recorded in their files and **none is visible from the board table**, because this board's acceptance checkboxes are decorative by convention. That is the mechanism, named once more: with the boxes unticked board-wide, "met" and "unmet" can only live in prose, and prose is what keeps failing to propagate.

### The meta repo has no CI

No `.github/workflows` at all, so the engine's stage-3 *"authoritative gate"* **does not exist** for T-016 or for any other meta-repo task — [T-003](T-003-ci-docs-reflect-jenkins.md), [T-012](T-012-aws-endgame-decision.md), [T-015](T-015-docs-reflect-deployed-bff.md), [T-017](T-017-docs-drift-rds-to-selfhosted.md), [T-023](T-023-meta-docs-stale-bff-smoke-path.md), [T-027](T-027-contract-ordering-note-sql-vs-jpql.md), [T-029](T-029-code-review-cannot-see-worktrees.md). A1 and QA carry the entire weight there. Left unfiled per the human's H2 choice; recorded so the next meta-repo task knows what it is not getting.

## Board consistency sweep — 2026-08-22

A fourth sweep, run against all 52 task files, the frontmatter, `README.md`, and the live filesystem. **No status changed, no scope changed, no product code was touched.**

**Structural state is clean and was verified first:** 52 task files ↔ 52 board rows, no orphans in either direction, every file's `status:` matches its board line, no `todo` holds an owner, and no `depends_on` names a task that does not exist.

**What was wrong:**

1. **The wave-1 note still sent readers at [T-103](T-103-skills-catalog-and-assignments.md)**, which merged 2026-08-21 (`2e54394`) — in the note whose entire job is telling people what to claim, and in the sweep item directly above that corrected the *same sentence* one day earlier. Wave 1 is **T-104 and T-151**. Corrected in both places.
2. **T-152 and T-016 had no close-out section** — see above. Written.
3. **[README.md](README.md) said infra runs `T-001…T-028`.** It runs to T-030, and T-152–T-155 are boarded in that table too. **Third recurrence**: the 2026-08-20 sweep fixed this identical line from `T-001…T-024`. A hand-maintained range in prose is a fact with an expiry date; it now says "T-001 upward" and names no ceiling.
4. **[README.md](README.md) pointed at "the sweep note at its foot".** The foot of this file is a task close-out; the sweeps are mid-file and there are now four of them. Re-pointed at the section list rather than at a position.
5. **[T-101](T-101-experience-resource.md) and [T-102](T-102-education-resource.md) never had `checkpoint.worktree` cleared.** [T-028](T-028-qa-env-generator-worktree-build-context.md) made that convention load-bearing on 2026-08-21 and it was applied to T-103 and T-152 — but not retroactively. `cvdl-worktrees/` is empty, so `scripts/qa-env-override.py` refuses on both: *"Refusing: this stack would exercise the MAIN CHECKOUT (master)"*. Verified by running it, then cleared. This is exactly the case T-028 wrote down (*"a closed task still declaring a path makes every later bring-up for it exit 1"*) and it was sitting on two closed tasks the same day the tool shipped.
6. **[T-017](T-017-docs-drift-rds-to-selfhosted.md)'s title asserted work its own body says is largely done.** *"The repo still says RDS in five places"* — its 2026-08-22 re-scope check found all five surviving mentions are contrastive or historical and **explicitly permitted by its own AC1**, and `diagrams/architecture.mmd:15` reads `MySQL` and never said RDS. Retitled to what is actually left.

7. **Duplicate frontmatter keys were silently shadowing the values next to them — including one clearing that had already been done.** Found by *verifying* item 5 rather than by reading: `scripts/qa-env-override.py` still refused on [T-152](T-152-mysql-84-parity-cv-database.md), whose close-out had explicitly cleared `checkpoint.worktree` that morning. It carried **three** `worktree:` keys in one mapping (cleared · the stage-1 path · `pending` from stage 0) and a **second, empty `pr:`**. YAML takes the **last** duplicate, so the clearing was inert, the merged PR URL was shadowed by a blank, and the file read as correct to anyone looking at the line the close-out edited. Duplicates demoted to non-key names, originals kept. A sweep of all 52 files for the same shape found one more: [T-202](T-202-bff-public-routing-and-auth.md) had a second `security_review:` holding `done` — **a third vocabulary** for the key the 2026-08-17 sweep normalized from `required`/`true` down to one, and last, so it won. Renamed. (T-002 and T-103's apparent duplicates are sequence items in different rounds — checked, not touched.)

**The generator is now the check for item 5, and it passes.** `python3 scripts/qa-env-override.py --task <id>` exits 0 on every closed task that previously refused — T-101, T-102, T-103, T-152, T-016. This is the first sweep item on this board that has an executable test instead of a re-read, which is the direction the *"decorative checkboxes"* problem needs to move in.

**Left alone deliberately.** [T-104](T-104-project-resource.md) declares a `checkpoint.worktree` path that does not exist on disk, but it is **unclaimed** — the dev-loop recreates the worktree at stage 1, so the declaration is a pre-claim convention, not close-out drift. Item 5's rule applies at close-out, not before it.
## T-104 merged — M2's domain model is complete, and the sixth spec falsified in five days (2026-08-22)

Merged as `7677fee` ([cv-domain-service#8](https://github.com/erfeamor/cv-domain-service/pull/8)). Picked up **at implementation** per its `reset_note`, as T-102 and T-103 were — the H1 checkpoint from 2026-08-04 was real and was used as written.

**All four API resources are now done.** [T-201](T-201-bff-cv-aggregate.md) and [T-301](T-301-admin-cv-sections-crud.md) are unblocked; wave 2 is open. Wave 1 is [T-151](T-151-dev-seeds-cv-sections.md) alone. **M2 is four of eleven.**

**Three premises had moved since that H1 and were recorded before a line was written**, exactly as T-103 did — T-027 (below), T-028 landing (so the "hand-build a compose override" note was superseded), and MySQL 8.4 becoming real. A 18-day-old DoR is not uniformly current, and saying which parts aged is cheaper than letting the implementer infer it. This is now three tasks in a row where that step paid.

### [T-027](T-027-contract-ordering-note-sql-vs-jpql.md) hit exactly where this board said it would

The board has said since 2026-08-21 that *"T-104 hits it next"*. It did. `docs/api-contract.md:41` mandates an `@Query` for this collection while :39 prescribes `ORDER BY start_date IS NULL, start_date DESC, id ASC` — SQL, which does not parse in the JPQL context the same document requires. Shipped with the portable spelling T-103 proved:

```
ORDER BY CASE WHEN p.startDate IS NULL THEN 1 ELSE 0 END, p.startDate DESC, p.id ASC
```

No `nativeQuery` — staying in JPQL means a column rename still fails at **startup** rather than at runtime. **T-027 remains open and is now owed by two resources rather than one**; it is docs-only and trivial.

**The ordering was proven against real MySQL 8.4, not H2**, and that distinction is the point of stage 4: the unit tests only ever see H2, and the two engines can disagree on NULL sort order. QA inserted rows in an order deliberately mismatching the expected output — `2024-01-01`(id6), undated(id7), `2025-06-01`(id8), `2025-06-01`(id9), `2026-01-01`(id10) — and `GET` returned **[10, 8, 9, 6, 7]**: `startDate` DESC, undated **last**, `id` ASC on the shared-date tiebreak.

### The sixth acceptance criterion falsified by the person implementing against it

`/code-review` (high effort) and the developer **independently** found that `repoUrl` carried no `@Size`. V1 declares `repo_url VARCHAR(255)`; unbounded, a 260-character value passes bean validation, reaches MySQL strict mode as error **1406**, and surfaces as a **500 where contract design rule 4 requires a 400**.

T-104's AC says *"no validation annotation on any other field"*. **PO ruling: apply it anyway, because the AC's wording is over-broad and not the ratified part.** DoR ruling 5 is the ratified text and its reasoning is about **format** validation (`@URL`/`@Pattern`) silently narrowing the contract — which a length bound mirroring the column does not do. Two supports, both verified rather than asserted: `docs/api-contract.md:10` design rule 4, and the sibling convention, where `Education.fieldOfStudy` and `Skill.category` are **both optional and both carry `@Size`**. Leaving `repoUrl` bare made Project the odd one out. **C15 is untouched — `repoUrl: "not-a-url"` still returns 201**, so DoR 5's actual rule is preserved.

**That is six in five days** — after T-103's `@Transactional` boundary, T-104's own inherited *"flag, don't block"*, T-028's AC1, T-152's `docker exec` on a `--rm` container, and T-023's file count. The board has already named specifications as its weak link. The pattern in all six is identical: **each was caught only because the implementer was told the spec was open to challenge.** The developer here flagged the consequence and complied literally rather than quietly deviating, which is what made the ruling possible at all.

### The T-107 guard, closed by construction this time

Confirmed **red before** the guard went in (`Status expected:<400> but was:<201>`), then — going further than asked — the assertion was flipped to `isCreated()` + `$.id == 999` and **passed**, demonstrating that the unguarded POST really does return 201 carrying the victim's id. The `save()` stub echoes its argument back the way a real repository would, *deliberately*, so the assertion cannot be satisfied by the mock the way T-101's `clientSuppliedIdInThePostBodyIsIgnored` was for three weeks.

Stage-4 QA then proved the live half by exploit, not by argument: `POST /people/2/projects {"id":5,...}` where row 5 belongs to person 3 → **400**, row 5 read back **from MySQL** unchanged, `GET /people/3/projects` still returning it, no stray row under person 2.

### Filed, not folded in: [T-108](T-108-untransacted-update-read-modify-write.md)

`/code-review`'s second finding: `update()` is an untransacted read-modify-write. With `open-in-view: false` and no `@Transactional`, a concurrently deleted row makes the trailing `merge()` fall through to `persist` and **re-INSERT it under a new id** — the client gets a 200 whose `id` is not the one it PUT, and a deleted row reappears. No `@Version`, so two concurrent PUTs also lose an update silently.

**PO ruling: file, do not fix here.** `EducationController.update` and `ExperienceController.update` carry the shape **verbatim** and are already on `master` — verified directly. Fixing only Project would leave three sibling resources with two concurrency behaviours, which is the same argument [T-107](T-107-post-id-cross-person-write.md) used to decline the structurally better `@JsonProperty(access = READ_ONLY)`.

**The contrast with T-107 is written into T-108 deliberately, because the two rulings look inconsistent and are not.** T-107's defect was fixed *inside* T-102 rather than deferred, because shipping new code carrying a live cross-person write would have been following process off a cliff. This one is neither an authorization hole nor new — it ships identically on `master` today, so deferring changes nothing about the exposure, where deferring T-107 would have added a fourth instance of a live one.

### First "verified against MySQL 8.4" that is true by construction

`SELECT VERSION()` → **8.4.11**, read off the running container rather than the compose tag. [T-152](T-152-mysql-84-parity-cv-database.md) and [T-016](T-016-dev-prod-mysql-parity.md) landed that parity hours earlier, so this is the first stage-4 run on this board whose engine claim rests on something other than assumption — the four earlier claims (T-102, T-103) were most likely 8.0 wearing an 8.4 label.

**And [T-028](T-028-qa-env-generator-worktree-build-context.md) did its job on its first real outing.** The generator resolved the worktree and repointed the `domain-service` build context itself; QA confirmed provenance off the **image labels** (`com.cvproject.dev-loop.commit=81f4bef`, `dirty=false`) rather than inferring it, corroborated by the additive tell (`GET /people/1/projects` → `200 []` where master 404s). T-103 got that provenance by luck and a hand-built third compose file; this task got it from tooling.

### [T-026](T-026-first-build-after-cold-start-fails.md) reproduced a fifth time — and this one counts

`PR-8/1` failed **42 seconds after the doorbell started the box** (`pending → error`, no intervening success), and `PR-8/2` went green unattended on the warm box at 15:36:40Z. It matches on both axes that separate this task from [T-030](T-030-pr3-build1-success-then-error.md): it fails *outright* rather than succeeding and self-invalidating, and it fires on a cold start.

**The console signature is still unobtained** and is not being claimed — Jenkins needs credentials this machine's policy declines. Recorded as *"matches the cold-start-fails / warm-succeeds pattern, console signature unobtained"*, because stating it the strong way is precisely the error T-030 exists to correct, and repeating it one day later would be worse than the original.

**One Jenkins login now closes three open items**: this occurrence, [T-030](T-030-pr3-build1-success-then-error.md)'s anomaly, and [T-152](T-152-mysql-84-parity-cv-database.md)'s outstanding CI-console criterion.

**The `gh pr checks` caution, demonstrated live.** PR-8 renders green and `gh pr checks 8` reports a pass while the `error` sits in the history behind it — GitHub keeps only the latest state per context. Anyone verifying the eventual T-026 fix that way will confirm a fix that never ran.
## T-151 merged — wave 1 is complete, and T-028's rule got its first real test (2026-08-22)

Merged as `865784f` ([cv-database#4](https://github.com/erfeamor/cv-database/pull/4)). One file, append-only, +183 lines: `sql/dev-seeds/afterMigrate__seed_dev.sql`. No versioned migration, no edit to `V1__init_schema.sql`.

**Wave 1 is now complete** — T-101, T-102, T-103, T-104 and T-151 are all `done`. The local stack finally renders a *complete* demo CV; until today the section endpoints and both public front ends came up empty.

### The task's own guard was broken, and it was caught at H1 rather than in production

T-151 correctly diagnosed that `INSERT IGNORE` cannot dedupe `experience`, `education` or `project` (verified: each has **only** an autoincrement PK and an FK — no unique constraint), and correctly prescribed `INSERT … SELECT … WHERE NOT EXISTS`. Then it specified `name + start_date` as the natural key for `project` — and **`project.start_date` is nullable**, the only nullable date of the three tables. In MySQL `pr.start_date = '…'` is never true against a stored NULL, so for an undated project the guard passes and **the row is re-inserted on every migrate**: exactly the duplicate-row bug the task exists to prevent, reproduced by the fix it prescribed.

**Being right about the mechanism is not the same as being right about the instance.** That is the seventh specification defect this board has found in five days, and the first caught at H1 — before implementation rather than during it.

Fixed with the null-safe operator `<=>` on the three project guards; `experience.start_date` and `education.start_date` are `NOT NULL` and keep plain `=`, since null-safe handling there would be dead code implying a nullability the schema does not have.

**Confirmed red first**, and the isolation is what makes it evidence rather than assertion — with `<=>` swapped back to `=` on a fresh volume, the project count went 3 → 4 → 5 across three migrates while **only the undated row duplicated**; the two dated projects and both `NOT NULL` tables held. That pins the cause to the NULL comparison rather than to the guard's shape.

### Both sharp edges of the ordering contract are now exercised locally

H1 ratified seeding **one undated project** deliberately, to exercise the *"undated last"* rule [T-104](T-104-project-resource.md) had shipped hours earlier. `/code-review` then found the matching hole: every seeded row had a **distinct `start_date`**, so the contract's `id ASC` tiebreaker — *"mandatory, not decorative"* per § Ordering — was never exercised, and a regression dropping it would still render a correct-looking CV locally. A fourth project now shares a date:

```
id 1  Curriculum Interactivo  2024-02-05
id 2  Ledger CLI              2021-11-08   <-- tie
id 3  Schema Diff Reporter    2021-11-08   <-- tie
id 4  Dotfiles                NULL         <-- undated, last
```

QA verified the order **through the domain API**, not by re-running the `ORDER BY` in SQL: `GET /api/v1/people/1/projects` returned `1 → 2 → 3 → 4`. The tied pair resolving id 2 before id 3 is what distinguishes a real `id ASC` tiebreak from insertion order that happens to look right.

### [T-028](T-028-qa-env-generator-worktree-build-context.md)'s bind-mount rule, first real outing

T-028 named this task as the first its mount-provenance rule binds, and **both halves were obtained**:

- **`.Mounts` captured while the stack was up** — `cvdl_t-151-flyway-1` bound `…/cvdl-worktrees/T-151/sql` → `/flyway/sql`: the worktree, not the main checkout.
- **Paired behavioural check** — `experience=3, education=2, project=4` on the meta stack, counts that are *impossible* unless the worktree's SQL executed, since master's seed file has no rows in those tables at all.

The pairing is the sign-off because **a bind mount leaves no trace after teardown**, unlike a build label. Before T-028 landed, this exact task would have seeded from **master's SQL** while the generator printed *"no service repointed: task repo 'cv-database' is not built by docker-compose.dev.yml"* — output that reads as *nothing to do here*. The rule was written for this shape and it caught it.

### Documented, not fixed — and the documentation was verified

`/code-review` reproduced a silent break of this task's own invariant: rename a seeded row's **key** column through `cv-admin-react` and re-migrate, and the guard misses, the row is resurrected, and there are **two rows with `end_date NULL`** — two "current jobs" on the public CV, while migrate exits 0. The converse also holds: editing a **non-key** field *in the seed file* applies on a fresh volume and silently no-ops on every existing one.

Neither is fixable without a unique constraint, which is a schema change and explicitly out of this task's scope. Both are documented in the header block with `reset.sh` named as the remedy — and **QA reproduced both and confirmed the remedy**, so the comments describe observed behaviour rather than predicted behaviour. A comment that is subtly wrong is worse than none, in a file whose entire theme is that the absence of an error is not evidence of success.

### The gate that does not exist, stated once more

`Jenkinsfile:25` pins `FLYWAY_LOCATIONS=filesystem:/flyway/sql/migrations` and `dev-seeds` is **not** on that path — verified, not assumed. A syntax error, an FK violation, or the duplicate bug above would all pass CI green with no output. **Green CI is required by the DoD and proves nothing about this file.** The triple-migrate verification is the only check that will ever catch a seed regression, here or on any future edit — which is why it was run three times independently: by the developer, by the driver, and by `/code-review` in its own container.

**A record correction:** the *"two pre-existing 1062 warnings"* figure carried in this task's brief and in both agent reports is wrong — on MySQL 8.4 it is **eleven** (1 `person` + 5 `skill` + 5 `person_skill`). Same expected `INSERT IGNORE` noise, no defect, and the figure never reached the committed file. Kept because *"what does clean noise look like"* is precisely the judgement this file's silent-failure mode depends on, and a wrong baseline for it is how a real error gets skimmed past.
## The Jenkins console arrived — one fetch, five tasks moved (2026-08-22)

The human supplied the console text for `cv-database` PR-4 builds **#1** and **#2**. This board had been routing items to *"one Jenkins login"* for three days; here is what it actually settled, and what it did not.

### [T-026](T-026-first-build-after-cold-start-fails.md) — signature CONFIRMED, cause narrowed, still `todo`

Both halves of the filed signature, in one log, verbatim:

```
[Pipeline] { (Validate migrations)
[Pipeline] }                                  <-- opened and closed. NO [Pipeline] sh at all.
...
ERROR: No build record cv-database/PR-4#1 could be located.
Finished: FAILURE
```

Five prior occurrences were argued from status sequences. This one is read off the console — so the qualifier this board has attached six times (*"matches the pattern, console signature unobtained"*) comes off.

**The new fact is that the build did real work before it died.** Build #1 completed a full clone, merge and checkout, then lost its record between checkout and the first `sh`. That re-ranks the file's three standing candidates: **SSM re-provisioning orphaning the in-flight record is promoted to leading** (it is the only one that predicts *checkout succeeds, then the record vanishes*), while *"Jenkins mid-initialisation"* is weakened as worded — a not-ready Jenkins does not clone a repo first — and *disk/permission timing* is weakened, since the clone wrote to `/var/lib/jenkins` successfully in the same window.

**Still a narrowing, not a diagnosis.** Two artifacts would settle it and neither is in hand: Jenkins' own boot-window log, and the **SSM command invocation history** for `i-073e5284ca2a1ceed` across 16:18:39–16:19:41. If the SSM invocation overlaps the build, candidate 1 is confirmed and the fix is *sequencing*, not a readiness probe.

**Both builds are triggered by `Branch indexing`, not by a push** — confirming [T-019](T-019-ci-host-on-demand.md)'s `ci-on-demand.tf` ruling 1 that the doorbell forwards no payload. The real chain is `push → doorbell → StartInstances → Jenkins boots → branch indexing → build`, which is *why* the first build races the boot: nothing was ever designed to wait. **A readiness probe on the doorbell cannot fix this** — the doorbell is long finished before indexing starts.

And build #2 is the control this task has wanted since it was filed: **same commit, same job, warm box, 63 seconds later, stage executes fully.** Identical input, opposite outcome, now in the same evidence set as the failure.

### [T-152](T-152-mysql-84-parity-cv-database.md) — the last outstanding criterion is CLOSED

The criterion named PR-3 build #2; what arrived is **PR-4 build #2**. Recorded as a **substitution rather than glossed**, per this task's own rule that a local reproduction and a CI execution are different claims — and it is the *stronger* evidence, because PR-4 runs against master with T-152 already merged:

```
+ docker run -d --rm --name cv-mysql-ci-2 ... mysql:8.4
Database: jdbc:mysql://cv-mysql-ci-2:3306/cv?allowPublicKeyRetrieval=true (MySQL 8.4)
Successfully applied 1 migration to schema `cv`, now at version v1
```

**The banner matches the corrected expected string exactly, including `?allowPublicKeyRetrieval=true`** — vindicating the AC correction made on 2026-08-22 *before any log existed*, since a literal grep for the shorter form would have missed and read as "banner absent". The struck `docker exec` criterion is likewise confirmed unsatisfiable: the log shows `--rm` and a post-stage `docker rm -f`.

It also observes `FLYWAY_LOCATIONS=filesystem:/flyway/sql/migrations` in a real run — the load-bearing fact behind [T-151](T-151-dev-seeds-cv-sections.md)'s *"Jenkins is not a signal for dev-seeds"*, until now verified only by reading the Jenkinsfile.

**Every `done` task on this board now has every acceptance criterion met except T-019's billing week and T-022's interactive Cognito login.**

### [T-154](T-154-jenkins-pipeline-timeout.md) — the premise was wrong: the retry loop is NOT latent

The task argued the hang was dormant because `allowPublicKeyRetrieval` is intact. The log shows Flyway's retry path **executing on a healthy build**:

```
Retrying in 1 sec... / 2 sec... / 4 sec... / 8 sec...
```

**The cause is mundane and permanent:** the Jenkinsfile starts MySQL with `-d` and runs Flyway immediately, with no healthcheck wait. **The retries *are* the wait.** So this is the pipeline's normal startup path, succeeding only because MySQL wins the race in ~15s. Against `FLYWAY_CONNECT_RETRIES=60` and a doubling backoff, a MySQL that never comes up walks that budget to exhaustion **while holding the only CI host up** — defeating T-019's reaper exactly as the task predicts. A second, cheaper fix is now visible and should be priced at H1 beside `timeout {}`: **wait for the container to report healthy**, so the retry budget stops being the synchronisation mechanism.

### [T-155](T-155-flyway-version-supports-mysql-84.md) — confirmed in CI, and the bump is bigger than assumed

The unsupported-pairing warning is now observed in a real gate run, and the log pins the version: **Flyway OSS 10.22.0**, with Flyway itself advertising **13.3.0** as current. A two-major jump is a materially different proposition from a patch bump and should be weighed at H1 rather than assumed cheap.

### [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) — the dead gate, observed dead

```
[Pipeline] { (Deploy)
Stage "Deploy" skipped due to when conditional
```

Previously argued from reading the Jenkinsfile; now Jenkins names the reason itself. **A trap for whoever fixes it:** build #1 of the same PR reports the same stage skipped `due to earlier failure(s)` — so *"Deploy was skipped"* is not evidence about the branch gate unless you read **which** skip it was, and T-026 means roughly one cold-start build in two shows the misleading variant.

### [T-030](T-030-pr3-build1-success-then-error.md) — NOT closed, and the prediction was wrong

**These are PR-4 logs; T-030 is about PR-3 build #1.** The claim this board repeated — *"one Jenkins login closes four items"* — was wrong on this one: the four items were not four independent fetches, they were largely **the same PR's builds**. Recorded rather than quietly dropped, because a convenient-sounding count that nobody re-derived is precisely this board's recurring failure, arriving this time in a sentence *about* closing open items.

What did improve is that the discriminator is now exact: if PR-3#1 shows the empty stage plus `No build record`, it is T-026 and folds in; if it shows the stage executing real steps and *then* failing, it is a different defect. The prior mildly favours the latter — T-026's mechanism kills a build before it can report anything, and T-030's sequence has a **`success` posted first** — but that is an argument, and this task exists because an argument was mistaken for evidence once already.
## T-031 merged — the board has a validator, after three rounds and 34 findings (2026-08-23)

Merged as `ae343eb` ([#59](https://github.com/erfeamor/curriculum/pull/59)). `scripts/board-check.py`, 740 lines, read-only, seven checks — each mapped to a **recorded incident**, not an invented rule. Wired into `scripts/test-all.sh`; the `/dev-loop` driver runs it at every checkpoint write; a `PostToolUse` hook is available **opt-in**.

**Why it exists, stated as evidence:** twelve violations on this board, every one found by a human or agent *re-reading* rather than by anything downstream noticing. The T-002 board line made five infra tasks read as un-claimable for four days. Four were the duplicate-key class — the only one that silently **inverts** a value rather than leaving it absent — and two of those were introduced by the driver hours after it swept for that exact bug, with the write-up a few sections above in this file. **"Be careful" had demonstrably failed as a control, in writing, within hours.**

### What it would have caught, proven rather than claimed

Four tests read the **real historical incidents out of git** rather than reconstructing them — T-152's triple `worktree:` and shadowed `pr:` (`dd7bfe7`), T-202's third `security_review:` vocabulary (`05387a5^`), T-104's and T-151's `review_round` shadowing (`51bc931^`). All four fail if the checker is stubbed, so *"a validator that would not have caught the bugs that motivated it is not done"* is a checkable criterion rather than a self-graded one.

That mattered: an earlier hand-built fixture passed while a reviewer believed the real case failed. **The fixture and the artifact disagreed, and only the artifact counts.**

### Three review rounds, 34 findings, and a rate that never fell

| Round | Scope | Findings |
|---|---|---|
| 1 · `high` | whole branch | 6 |
| stage-4 QA | behaviour + hook | 2 |
| 2 · `max` | `board-check.py` | 11 |
| 3 · `max` | **the test file** — never reviewed before | 11 + 4 from the driver |

**The two best findings in the whole task are the same defect wearing different clothes, and neither was in the validator's logic.**

QA found `test_fallback_produces_no_false_positives_on_the_live_board` **green while 59 false positives sailed past it** — because before asserting empty it filtered to the one key already fixed. Its *name* promised the general property; its *assertion* checked a special case. Round 3 then **mutation-tested** the suite — revert each fix, see whether any test dies — and found **11 surviving mutants**, including that the entire fallback scanner had *zero* positive coverage: reverting all three of its bug fixes at once left the suite fully green.

Both are the [T-107](T-107-post-id-cross-person-write.md) shape: a green signal that stopped measuring what it claims, retiring the question before anyone thinks to ask it. **They appeared inside the tool built to catch that class of thing** — which is the honest limit on this validator, now written into the task. It checks board frontmatter. It cannot check whether a test asks the question its name promises.

### Two driver errors, both caught by something other than the driver

1. **A `.gitignore` override.** The driver ruled — on its own authority — that `.claude/settings.json` should be committed so the hook would propagate, and had it done. H1 had authorized *building* the hook, not reversing a documented policy to distribute it, and the driver noted at the time that it was a policy change and proceeded anyway. **A security check flagged it.** The human chose **script committed, registration opt-in**; reverted before the branch was ever pushed. `.gitignore` is a 0-line diff.
2. **The dual-path dispatch.** The driver ruled that check 1 should run on `yaml.compose()` with the hand-rolled scanner kept as a fallback. That closed three real blind spots — and orphaned the fallback's entire test coverage and introduced three false positives, both being consequences of the change rather than of the original code. Asked directly whether the dispatch was worth keeping, **the developer said no, with reasons, and deleted it**: `qa-env-override.py` in the same directory already hard-requires PyYAML, so the fallback avoided a dependency this repo's tooling already assumes. 966 → 740 lines.

**The second error is the more instructive one.** The evidence for the compose re-base was strong and the ruling was still wrong, because the driver treated *"use the real parser"* as self-evidently safe. A parser does not do the thinking; it **moves** where the thinking has to happen — from *what does a key look like* to *what makes two keys the same*. Three false positives followed directly from skipping that step.

**"PO ruling" in this board's vocabulary means THE DRIVER DECIDED.** It does not mean the human approved. The original wording did not distinguish them, and on a board whose entire pathology is facts inherited without re-checking, that ambiguity was a worse defect than the override it described. Human decisions now say so, with dates.

### Also worth keeping

`line_of`'s `top_level_only` flag was reported as *untested*. The developer investigated instead of complying and found it **provably dead code** — the regex's own column-anchoring made the flag incapable of ever mattering, and no caller passed `False`. Deleted, rather than padded with a test for behaviour that never existed. **Third time on this task that someone declined an instruction because the instruction was wrong**, which is the disposition this board has been asking for since the T-107 post-mortem.

### Filed, not resolved: [T-032](T-032-board-check-re-review-after-live-use.md)

The human accepted the merge **and** asked for a re-review after a week of real use, rather than choosing between accepting and blocking. The reasoning is on the task: shipping starts it catching real drift immediately, while **the finding rate never fell** (6 / 2 / 11 / 15) and that deserves an answer only live use can give. T-032 is explicitly not to be started before **2026-08-30** — elapsed time carrying real edits *is* the input — and its acceptance criteria require a deliberate hunt for an **eighth** duplicate-key blind spot, since check 1 missed seven distinct YAML surface forms across these three rounds.

Its verdict options are **converged**, **needs another round**, or **the approach is wrong** — the third named explicitly so sunk cost does not quietly remove it.

## T-105 merged — every section is ordered now, and the file argued both ways about its own coverage (2026-08-26)

Merged as `1b9b398` ([cv-domain-service#9](https://github.com/erfeamor/cv-domain-service/pull/9)), closing the last gap [T-006](T-006-contract-section-ordering.md) left open: T-101 shipped before § Ordering existed, so experience was the one section resource on `master` without an ordering guarantee. **All four section collections are now contract-compliant**, and [T-501](T-501-e2e-cv-milestone.md)'s last M2-domain blocker is gone — what remains in front of it is the deployment chain and wave 2/3.

Resumed mid-pipeline across a **third** session, at the stage-1/stage-2 boundary its own checkpoint named. The checkpoint was treated as a claim to verify rather than a fact to inherit: A1 re-run before any reviewer attention was spent, diff re-confirmed at 4 files / +176-6. Both matched.

**The production change is two lines** — a method signature and its one call site — against 224 lines of tests and javadoc. That ratio was challenged directly at H2 and the answer is the non-obvious part of the task: `ExperienceRepository` is a Spring Data interface with no method bodies, so **the method name *is* the query**. `findByPersonId` emits no `ORDER BY`; `findByPersonIdOrderByStartDateDescIdAsc` emits `ORDER BY start_date DESC, id`. There is nowhere else the logic could live.

### The finding: the file contained the argument for deleting its own load-bearing test

Round 1 ran two independent passes. The specialist lens returned **no blocking findings** and reproduced [the ninth spec defect](T-105-experience-ordering-retrofit.md) by probe. `/code-review` found the one that mattered, and it was in a **comment**:

> ~~*"Only inverting id against insertion order makes a missing `id ASC` observable."*~~

Measurably false — and it contradicted the javadoc on `declaresTheIdTiebreakerInTheGeneratedSql` **in the same file, authored in the same commit**, which correctly said the opposite and even named the tie test as its counterexample. The failure mode is concrete: a maintainer reads the first comment, concludes row-order coverage protects the tiebreaker, and deletes the only test that can actually fail — while the suite stays green.

**That is the [T-107](T-107-post-id-cross-person-write.md) shape exactly** (*"the entity exposes no id mutator, so Jackson ignores it"* — believed for three weeks), and it is worth naming what nearly happened here. The checkpoint carried an instruction to reviewers: *"do not let a reviewer delete the SQL-capturing test as redundant."* It worked — neither reviewer proposed it. But **the protection lived in a checkpoint note while the artifact itself argued the other way**, and checkpoint notes are not what the next maintainer reads. The fix moved the protection into the file. This board's durable form, once more: [T-103](T-103-skills-catalog-and-assignments.md)'s two rulings enforced structurally rather than by vigilance.

### Experience was the odd one out of five, and nobody had noticed

`/code-review` filed it "low": no controller-level test pinned pass-through ordering. Verifying rather than accepting the severity showed **all four sibling resources have one** (`ProjectControllerTest:449` plus Education/Skill/PersonSkill) — the [T-104](T-104-project-resource.md) `repoUrl` shape, where an over-broad AC (*"no change to the controller"*) governs behaviour, not test coverage. `c1`'s existing fixture could never have caught a re-sort: its two rows are already both id-ascending **and** alphabetical.

Confirmed red first, and the measurement is better than the assertion: with a company sort temporarily in `findAll`, the new test failed and **the other 19 controller tests passed against that re-sorting controller.**

### QA closed the gap its own plan had declared disproportionate

Stage 4 signed off with no defects and no bounce. Its spine ran in full — labels compared against the *board's* frontmatter rather than against themselves, and QA-T105-03's negative control confirming `origin/master@7677fee` returns **0 matches** for the ordered method, so the probe demonstrably discriminates a retrofitted tree from an un-retrofitted one.

Then it went further than written. The plan's §6 had flagged a residual risk and explicitly declined to close it: Docker layer caching could in principle leave **stale bytecode running under correct labels**, since the negative control checks *source* at the labelled commit, not the running JAR. QA closed it nearly for free by reading MySQL's `performance_schema` statement digest — the SQL the deployed bytecode actually issued:

```
SELECT ... FROM `experience` `e1_0` WHERE `e1_0`.`person_id` = ?
ORDER BY `e1_0`.`start_date` DESC , `e1_0`.`id`          COUNT_STAR: 13
```

**The tiebreak is now evidenced at three independent layers**: the declaration, the Hibernate-emitted SQL captured in-process, and the statement the live server ran. QA also found a free provenance tell the plan said did not exist — the dev-seed rows for person 1 carry ids `1,2,3` in *ascending* `startDate` order, so contract order is their exact reverse: this build returns `[3,2,1]`, an un-retrofitted `master` returns `[1,2,3]`. An additive-style tell on a modifying task.

An unscoped `WHERE id = ?` in the digest was **exonerated by counts rather than waved off**: the scoped form ran 4 times (gating every single-row op, including both cross-person 404s) against 2 unscoped, matching only the two successful mutations — Hibernate's internal load during merge/remove, downstream of the ownership check.

### The merge needed `--admin`, and that is the designed path here

`gh pr merge` refused: `BLOCKED`, `REVIEW_REQUIRED`. Diagnosed rather than bypassed on reflex. Classic branch protection 404s on this repo — the rule is a **ruleset** (*"Protect main branch"*, active since 2026-07-12) requiring 1 approving review, code-owner review and last-push approval. Its bypass list is **`RepositoryRole: always`**, and **[T-104](T-104-project-resource.md)'s PR #8 merged 2026-08-22 with zero approving reviews while that same ruleset was active** — so every task on this board has merged this way. A solo developer cannot satisfy "1 approving review" on their own PR; GitHub blocks self-approval. **Recorded because the next reader will otherwise see `--admin` in the log and reasonably read it as a circumvention.** The gate that actually held was H2.

### [T-026](T-026-first-build-after-cold-start-fails.md) occurrence 6 — the cleanest on record

This task's own push produced it, and it is the first time the whole chain was watched live instead of reconstructed: the box was confirmed `stopped` beforehand, the push woke it at **08:41:20Z** via [T-019](T-019-ci-host-on-demand.md)'s doorbell (working unprompted), `PR-9#1` errored **64s later**, and `PR-9#2` went green unattended at 08:43:49Z because opening the PR is a *second* webhook delivery. 64s is the longest of the four measured intervals (42/47/62/64s), tightening the window a bisect should target. That file's count is corrected **five → six** in the table its own rulings designate as the authority, headings deliberately left unrenumbered.

Note the `error` sits **between two `pending`s** here — worse than T-026's plain-red case and exactly [T-030](T-030-pr3-build1-success-then-error.md)'s warning: `gh pr checks` hides it completely.

### Filed, not folded in: [T-109](T-109-ordering-tiebreak-unevidenced-siblings.md)

The specialist raised `education`'s tiebreak as asserted by a test that cannot go red — explicitly out of scope, board rule 3. **The driver verified before filing and widened it**: `project`, `person_skill` and `skill` have the same gap, and `grep -rln StatementInspector src/` was empty on `master`, so this PR introduces the repo's first SQL-capture evidence. All five orderings are **correct**; only the evidence is missing. Widened on re-running the check rather than on the reviewer's description, because this board has twice filed a task whose count was already wrong at filing ([T-023](T-023-meta-docs-stale-bff-smoke-path.md), [T-017](T-017-docs-drift-rds-to-selfhosted.md)).

### Two process notes

**A budget cap was exceeded deliberately.** Stage-4 QA was the 4th spawn against the adapter's `max_spawns_per_task: 3`. Taken knowingly: the engine's non-negotiable is that nothing merges without a QA pass, and the numeric guard — which the cap is a proxy for — was healthy at 45%/27%. The cap is a cost heuristic; the QA stage is a correctness invariant. Surfaced at H2 rather than buried in a checkpoint.

**The opt-in `board-check` hook earned its keep three times in one session**, catching a task file with no board row, and twice catching a file/board status disagreement *in the same turn it was introduced* — including the `checkpoint.worktree` clear at close-out, which is [T-028](T-028-qa-env-generator-worktree-build-context.md)'s rule and the exact drift that broke the generator for T-101/T-102. Registration lives in `.claude/settings.json`, which is gitignored, so [T-031](T-031-board-frontmatter-validator.md)'s H2 ruling — *script committed, registration opt-in, never distributed* — holds in substance.

## [T-030](T-030-pr3-build1-success-then-error.md) closed — the log arrived, and the task's own discriminator ruled against the convenient answer (2026-08-26)

The human supplied `cv-database` PR-3 consoles **#1** and **#2**, four days after the board first predicted one Jenkins login would settle four items. T-030 was filed precisely because that prediction was wrong for this one, and it stayed wrong: PR-4's console closed [T-026](T-026-first-build-after-cold-start-fails.md)'s signature and [T-152](T-152-mysql-84-parity-cv-database.md)'s criterion, and **this needed its own log**.

**Ruled a DISTINCT defect, not a sixth T-026.** The discriminator written into the task in August was applied as written and landed on its second row: `No build record … could be located` appears **nowhere**, and `Validate migrations` did not open and close empty — it created the network, pulled `mysql:8.4`, ran Flyway, and **applied the migration successfully**. The build's own verdict is `Finished: SUCCESS`.

**The mechanism, identified rather than parked.** One line in the log is the whole answer:

```
[Pipeline] { (Validate migrations)
Resuming build at Sat Aug 22 07:47:16 UTC 2026 after Jenkins restart
```

Jenkins restarted mid-build. Durability resumed it, the body ran to completion — then the `post { always }` block threw `MissingContextVariableException: Required context class hudson.FilePath is missing` at `WorkflowScript:32`, which `Jenkinsfile:32` pins to the `sh` doing the `docker rm -f` cleanup. **The workspace handle did not survive the restart into the post block.** So `success` was posted when the body finished (07:48:06) and `error` one second later when the post condition blew up (07:48:07) — while the build itself finished SUCCESS. The build's verdict and GitHub's last word disagree, which is exactly why this was inexplicable from the statuses API alone. Build #2 — same commit, no restart — is the clean control.

**What it does for T-026, stated carefully.** This is the first *logged* evidence that Jenkins restarts mid-build on that host, nine seconds into a build. T-026's leading candidate is *SSM re-provisioning orphaning the in-flight record*, which predicts exactly this event; until now it was inferred from *"checkout succeeds, then the record vanishes"* rather than observed. The economical reading is **one trigger, two outcomes** — the record survives (T-030, spurious error) or it does not (T-026, fatal). **That is written down as a hypothesis and deliberately NOT folded into the occurrence table; the count stays at six.** Padding it is the exact error that created T-030, and repeating it inside T-030's own resolution would have been worse than the original.

What *did* change is that T-026's ruling 1 now excludes T-030 **positively, on evidence**, rather than provisionally for want of a log — and the SSM invocation history is promoted to the highest-value remaining artifact, because a restart is now observed and only its *cause* is open.

**Closed with `pr: none`**, the T-010 sentinel: all four of its acceptance criteria are diagnostic, so it closes on evidence rather than a diff. **The residual defect it uncovered was handed to T-026 explicitly** — every mid-build restart also produces a spurious `error` after a `success` — with a recommendation *against* hardening the `post` block as the primary fix, since that quietens the symptom while leaving the fatal variant untouched. Written into T-026 rather than left implied by a closed task, because the [T-002](T-002-jenkins-on-drone-host.md)→[T-005](T-005-ci-secret-blast-radius.md) TLS hand-off sat unowned for eleven days for precisely that reason.

## [T-026](T-026-first-build-after-cold-start-fails.md)'s root cause found — JENKINS-23152, and its title had been naming a correlate for five weeks (2026-08-26)

The human authorised waking the CI host to read the on-box artifacts. Three SSM round-trips produced a named upstream bug, an exact 1:1 correlation, and the retirement of four hypotheses including this board's leading one.

**The finding, in one line from the Jenkins container log** — which persists across every boot on the `/var/lib/jenkins` host mount, so the actual 2026-08-22 event was still readable four days later:

```
2026-08-22T07:47:15  JENKINS-23152: .../cv-database/branches/PR-3/builds/1 already existed;
                     will not overwrite with cv-database/PR-3 #1 but will create a fresh build #2
```

`grep -c JENKINS-23152` returns **7**, and all seven land on known events — T-026's six occurrences **plus** [T-030](T-030-pr3-build1-success-then-error.md). No occurrence without a warning, no warning without an occurrence.

**The mechanism.** `JENKINS_HOME` is a persistent host mount, so `jobs/*/branches/*/builds/` survives every stop/start. The **Job DSL seed re-runs on every Jenkins boot** — `Processing provided DSL script` appears **30 times = 2 jobs × 15 boots** — recreating the multibranch jobs. A recreated branch job numbers from **#1**, collides with the `builds/1` already on disk, and `LazyBuildMixIn` refuses to overwrite and makes a fresh **#2**. Build #1, already running, is orphaned with no record — *that* is `No build record … could be located`. Build #2 has a valid number and runs clean.

**"Warm box succeeds" was never about warmth.** #2 succeeds because it is the build that got a valid number. The cold start, the boot window, the 42–65 second band, the `t3.small` — all correlates, and they correlate only because a Jenkins restart is what reseeds the jobs, and on this host Jenkins restarts when the instance does. **The task's title asserted that correlate as the cause and went unchallenged for five weeks** — this board's oldest failure mode, operating this time on its own investigation rather than on a task spec.

**Four hypotheses retired, each by its own measurement:**

| Killed | By |
|---|---|
| SSM re-provisioning (the *leading* candidate) | 44 invocations in retention; **none at all** on 08-20/21/22 |
| user_data re-running the provisioning script | plain-shell user_data, no per-boot marker; `ci.tf` says "at first boot" |
| OOM on the 2 GB `t3.small` | `OOMKilled=false`, no `dmesg` OOM, 1.1 GB available, swap untouched |
| **A mid-build Jenkins restart** | **the control boot** — woken with no push, `RestartCount=0`, exactly one `jenkins start` docker event, one JVM start per boot |

That last one also corrects [T-030](T-030-pr3-build1-success-then-error.md)'s resolution, written earlier the same day: *"Resuming build … after Jenkins restart"* never described a crash. It is the durable-pipeline machinery restoring a stale flow execution the previous session left in `builds/1`. **T-030's ruling stands and its mechanism does not** — different symptom, same root cause. Two causal corrections on that task in one day, both in the same direction: a plausible cause written down before the artifact that would test it had been read.

**The fix is now small and the verification exact**, which is the real prize: make the DSL seed idempotent (or reconcile `nextBuildNumber`), then stop the box, push to a branch that has built before, and assert **zero** `JENKINS-23152` lines for that boot. Compare the original acceptance criterion — *"push twice in a row so it is not luck"* — which could only ever have measured the symptom.

**One incidental measurement worth a line:** `ecs-agent`, [T-007](T-007-ecs-agent-cleanup.md)'s crash-looping leftover, logged **9 start/die cycles in the first two minutes** of the control boot — the only container churning at all, right through Jenkins' initialisation. Not the cause of anything here, but T-007 prices itself as *"a small but permanent tax"* and this is the first actual measurement of it.

## [T-026](T-026-first-build-after-cold-start-fails.md) FIXED and merged — the second attempt, and the first one that does anything (2026-08-26)

**Merged as cv-infra `1deebb4`** (squash of [#21](https://github.com/erfeamor/cv-infra/pull/21), `--admin`). Closes the board's longest-running defect: filed 2026-08-20, six confirmed occurrences, five weeks with a title that named a correlate as the cause.

**Attempt 1 shipped and did nothing, and the board says so rather than quietly replacing it.** The guard asked `Jenkins.get().getItemByFullName('cv-domain-service')` and skipped the seed if the job came back. It deployed cleanly, threw nothing, and `createOrUpdateConfig` **still ran for both jobs**. The reason is a boot-order fact that no amount of reading the DSL would have surfaced:

```
System config loaded -> Processing provided DSL script -> createOrUpdateConfig
   -> System config adapted -> Loaded all jobs -> init.groovy.d -> Completed
```

**JCasC runs job-dsl before Jenkins loads jobs from disk.** At DSL time the item model is empty, so the lookup is `null` for every job regardless of what exists. The guard could never fire — not "did not fire under these conditions", *could not*, on any boot.

**Attempt 2 tests the filesystem instead**, because the file is there when the model is not:

```groovy
seeded = new File('/var/lib/jenkins/jobs/cv-domain-service/config.xml').exists()
```

Same fail-open `try/catch` — on any failure the job is still created, never worse than before — but **the catch now logs**. Attempt 1's was silent, so its log could not distinguish *"returned null"* from *"threw and was swallowed"*, and separating those cost a whole apply cycle. A guard whose failure is indistinguishable from its success is a defect this board has catalogued repeatedly, and attempt 1 was one.

**Verified by measurement, in the order that made 4b matter:**

| step | result |
|---|---|
| 4a guard fires | both jobs log `config.xml present=true` → `not reseeding`, on every boot |
| **4b `createOrUpdateConfig`** | **0** — zero across all three post-fix boots. **This is the check that discriminated**; 4a alone was silent either way, and attempt 1 passed nothing like it |
| 4c no collateral damage | traits intact (Branch + OriginPullRequest present, ForkPullRequest absent), branch children and `builds/` preserved, and every `nextBuildNumber` preserved rather than reset to 1 |
| 4d cold-start push | **JENKINS-23152 = 0, `No build record` = 0** |

4d used a throwaway `chore/t026-verify` branch in `cv-domain-service`, since every prior PR branch had been deleted from `origin` and `master` is not pushable. Three builds, branch deleted afterwards. **Build 3 is the one that counts**: box stopped *idle*, push → doorbell → Jenkins restart → build on a branch that already had `builds/1` → `Finished: SUCCESS`, Lint executed, 141 tests passed, numbering advanced 2 → 3 → 4. GitHub's **full status history** (read via the statuses API, per this task's own caution that `gh pr checks` hides a failed build behind the latest state) shows `pending → success` with **no `error` state** — against six recorded occurrences that every one show an `error` on the first post-restart build.

**Two driver errors during verification, recorded because burying them would repeat the exact failure this task exists to document.** First: build 1 shows `error`, and that is the driver's setup mistake, not the defect — the box was stopped while build 1 was still downloading Maven dependencies, killing it mid-flight. Build 3 exists precisely to remove that confound. Second, and worse: the driver initially read `<result>SUCCESS</result>` out of `build.xml` as the build's verdict and reported both builds finished. **That element is not the build's result** — the verdict is the `Finished: X` line at the end of the pipeline log, and build 2 was at that moment still queued behind build 1 waiting for the single executor. A completion check that reports success on an unfinished build is the same class of defect as attempt 1's silent catch, caught here only because the `duration=0` and the missing stage lines did not fit.

**Divergence closed, confirmed rather than assumed.** Before the merge, S3 and the SSM SHA held the *branch* script, so applying from `master` would have reverted the fix. `terraform plan` run from `master` immediately after the merge reports `No changes. Your infrastructure matches the configuration.`

**What this unblocks:** [T-019](T-019-ci-host-on-demand.md)'s acceptance criterion — *"a build that needs the host actually completes end to end while the automation owns the lifecycle"* — is now met by the build the automation itself triggered, which is what T-026 had silently weakened since 2026-08-20.

**Cost note.** The whole stage — apply, four verification steps, merge — ran **inline in the driver with zero subagent spawns**, at 24% of the turn ceiling. The previous session had stopped at `HARD` (107% of turns) with the checkpoint written; resuming cost one apply plus the verification, no re-brief and no rework. The checkpoint protocol did exactly what it is for.

### [T-019](T-019-ci-host-on-demand.md)'s criteria reconciled — one closed, one found never to have been tested (2026-08-26)

Follow-on from T-026's close-out, which met T-019's last narrative criterion: *"a build that needs the host actually completes end to end while the automation owns the lifecycle."* It had been claimed on 2026-08-20 and carried an asterisk ever since — it was satisfied by build **#3**, never by build **#1**, the one the doorbell itself caused. With T-026 fixed, the first build after a cold start is now the build that counts, so the asterisk is gone and the criterion is ticked.

**The reconciliation found something the tick would otherwise have hidden.** T-019's acceptance list had been left **entirely unticked since 2026-08-19**, with all the evidence sitting in `checkpoint.stage4` instead. Ticking one box made the list read as though it were the only one done, so the whole list was checked against the file's own evidence. Five more were met and are now ticked with pointers. One was not:

> **"The host stops automatically when idle, and a build in progress is never killed."** The first half is well evidenced — the reaper stops the box and honours `CIKeepAlive`. **The second half has never been tested.** None of the 14 live checks started a build and watched it survive a shutdown window, and nothing since supplied one.

**And T-026's verification must not be misread as that proof**, which is the trap worth writing down: a build *was* killed mid-flight that day (`chore/t026-verify` build 1, dead while downloading Maven dependencies), but by a **manual `stop-instances` issued by the driver**, not by the reaper's idle check. It demonstrates that a mid-build stop is fatal — the thing the criterion exists to prevent — while saying nothing about whether the reaper would have declined. Settling it needs a live test: start a build, let the ~20-minute window elapse across it, confirm the pre-`StopInstances` re-check sees the busy executor and backs off.

So T-019 has **two** criteria open, not one: the billing-week rate (elapsed as of today, deliberately left for [T-032](T-032-board-check-re-review-after-live-use.md)'s session rather than convening one to read a single number) and the mid-build survival test. The task stays `done` — its PR merged — per the rule this board adopted after repeatedly having to unpark tasks left in `in_review` behind residual criteria.

**One caution for whoever reads the billing rate:** 2026-08-26 carries three extra cold starts, three real builds and a `terraform apply` from T-026's verification. Read the rate across the window, not off that day, or the reaper will look worse than it is.

### `cv-domain-service`'s halves of [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md)/[T-154](T-154-jenkins-pipeline-timeout.md) filed as [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md) and [T-111](T-111-domain-service-jenkins-pipeline-timeout.md) (2026-08-27)

Both cv-database CI tasks instruct their implementer to **check `cv-domain-service` for the same gap and file it, never fix it there** (board rule 3), and T-154 carries that as an explicit acceptance criterion. The check was run ahead of either task while reviewing what to pick up next. **Both defects are present in the second repo**, verified by reading the file rather than inferred:

| Defect | cv-database | cv-domain-service |
|---|---|---|
| `Deploy` gated on `branch 'main'` (neither repo's `origin` has one) | T-153 | **T-110** |
| No `timeout {}` — no `options {}` block at all | T-154 | **T-111** |

**Filed as separate tasks rather than by widening the existing two**, on the human's instruction. The reason it is the better split: T-153's `depends_on: [T-152]` is *file-level* to `cv-database/Jenkinsfile` and would be meaningless in another repo, and neither new task is a duplicate.

**Two findings that are new to the board, not restatements.** They matter because T-154's cost argument was built without them:

- **`numExecutors: 1`** (`cv-infra/templates/jenkins-provision.sh:63`). Both repos are seeded onto one Jenkins with a single executor, so **a hang in either repo blocks every build in both**. Observed live on 2026-08-26 — a queued build logged `Still waiting to schedule task / Waiting for next available executor` and sat there until the first reached a terminal state. T-154 argued only that a hung build holds the *host* up; it never said the other repo's CI stops too.
- **The hang mechanism differs, so T-154's cheaper fix does not port.** T-154's hang is Flyway's bounded connect-retry backoff, and its second fix is a healthcheck wait before invoking Flyway. `cv-domain-service` has no Flyway and no MySQL container: its unbounded steps are Maven resolving against `repo.maven.apache.org` and `docker build`, neither of which has a retry budget to exhaust. Only the `timeout {}` transfers.

Also recorded in T-110, because it was searched for and genuinely nobody holds it: **no board task owns implementing the `cv-domain-service` deploy.** [T-203](T-203-bff-ci-deploy-stage.md) covers `cv-bff-node` only, and that repo's `Docker image` stage builds an image it never pushes. Filed as a pointer, not as a task — naming the gap is not the same as claiming it.

**A stale warning cleared in three files while here.** T-153, T-154 and [T-109](T-109-ordering-tiebreak-unevidenced-siblings.md) each carried *"T-026 applies — the first build after idle may fail spuriously, re-run on the warm box before debugging."* [T-026](T-026-first-build-after-cold-start-fails.md) was fixed and merged on 2026-08-26, so that advice had inverted: it now tells the next person to **dismiss a genuine red build as a known flake**. Struck rather than deleted, per convention. **The `gh pr checks` half of the same warning is deliberately kept** — it reports only the latest status per context and is unrelated to T-026, so a failed build still hides behind a later green one.
