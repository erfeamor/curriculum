---
id: T-026
title: "The first Jenkins build after a cold start fails: 'No build record could be located'"
repo: cv-infra
status: todo
owner:
branch: fix/first-build-after-cold-start
pr:
depends_on: [T-019]
risk: normal
security_review: false   # no security path in adapter §5 — CI reliability, not exposure
---

## Why this exists

**Found 2026-08-20 by the first real push through [T-019](T-019-ci-host-on-demand.md)'s doorbell** — which is precisely what T-019's outstanding acceptance criterion existed to do, and exactly the class of defect that only a real push finds.

The on-demand chain worked end to end on its first genuine use:

```
push to cv-domain-service (08:11:58Z, delivery 200)
  -> doorbell Lambda -> ec2:StartInstances
  -> i-073e5284ca2a1ceed stopped -> running
  -> Jenkins boots, multibranch scan discovers PR-4
  -> build #1 starts 08:12:45Z
```

**And build #1 then failed**, 47 seconds after the instance started:

```
[Pipeline] { (Lint)          <- opened and closed with NO sh step and no output
[Pipeline] { (Test)
Stage "Test" skipped due to earlier failure(s)
...
ERROR: No build record cv-domain-service/PR-4#1 could be located.
Finished: FAILURE
```

**The same commit passed on a settled box.** Build #2 (triggered manually, ~10 minutes later) and build #3 (triggered automatically) both ran all four stages to `SUCCESS` in ~97s: checkstyle 0 violations, 35 tests green, Docker image tagged. Nothing about the commit changed between #1 and #2.

## Why this matters more than one red build

**Every developer's first push after an idle period gets a red X**, and the fix is "push again" — which nobody will know. It converts T-019's win (the box is up when work needs it) into a papercut that looks like a broken pipeline, and it will be blamed on whatever code happened to be pushed. T-106's PR was the first thing through and it briefly looked like T-106 had broken CI.

**Narrowed 2026-08-21 by T-103 — the fourth reproduction, and the first one that MASKED ITSELF.** T-103's PR ([cv-domain-service#7](https://github.com/erfeamor/cv-domain-service/pull/7)) reproduced the defect exactly, on a box the reaper had stopped at 12:24 the previous day:

```
06:45:54  error    .../PR-7/1/   "This commit cannot be built"
06:47:42  success  .../PR-7/2/   "This commit looks good"
```

**Nobody had to retrigger anything.** Pushing the branch and opening the PR fire *two separate webhook deliveries* — `push` at 06:44:50 and `pull_request` at 06:45:13 — and the second one triggered build #2 on the now-warm box ~90 seconds later. Build #1 died, build #2 passed, unattended.

Two consequences, and they pull in opposite directions:

- **The severity claim above is too strong for the normal workflow.** GitHub's status API keeps only the *latest* state per context, so the PR renders **green** and the failure is invisible unless someone reads the commit's full status history. Anyone whose habit is push-then-immediately-open-a-PR never sees a red X at all. That is most PRs on this board, which is a better explanation than "nobody noticed until T-106" for why a defect this reproducible went unfiled for so long.
- **It is *worse* for the case the paragraph above describes**, i.e. a push to an existing branch with no PR event behind it. There the red stands, and it is still blamed on the code.

So the papercut is real but **conditional on the shape of the push**, not universal. Fix the defect on the same terms — but drop "every developer's first push" from the argument for prioritising it, because it is not what the evidence shows. **The diagnostic signature is unchanged** (`No build record … could be located`, `Lint` opening and closing having executed nothing), so nothing about the hypothesis below is affected.

**A caution for whoever verifies the fix:** `gh pr checks` reports only the latest status per context and will show `pass` while a failed build sits in the history. Verify against `gh api repos/:owner/:repo/commits/:sha/statuses`, which lists every transition, or you will "confirm" a fix that never ran.

It also **silently weakens T-019's own acceptance criterion**. *"A build that needs the host actually completes end to end while the automation owns the lifecycle"* is now met — by build #3 — but was **not** met by the build the automation itself triggered.

## What is probably happening — a hypothesis, not a diagnosis

`ci-on-demand.tf`'s ruling 1 is that the doorbell deliberately forwards no payload: Jenkins' `periodicFolderTrigger` rediscovers the branch after boot. So build #1 is triggered by a folder scan running against a **Jenkins that has just come up**, while the box is still finishing its boot-time work.

`No build record could be located` is Jenkins failing to persist or re-read the build record it just created. Candidates, in rough order of likelihood:

1. **The boot-time SSM re-provisioning races the scan.** If JCasC/job-dsl re-creates the job definition while a build is in flight, the in-flight record is orphaned. T-019's own apply note records SSM re-provisioning taking 37s — the same order as the 47s gap.
2. **Jenkins is mid-initialisation** when the scan fires: the job exists but its build directory or the queue is not ready.
3. Disk/permission timing on `/var/lib/jenkins` after the volume is remounted at boot.

**Establish which before changing anything.** All three have different fixes and two of them are one-liners.

## A control, added 2026-08-20 — it points at *cold start*, not at first builds

T-102's PR was pushed a few hours later to the **same repo**, with the box **already running**. Its first build **succeeded**. Two data points now:

| push | box state | first build |
|---|---|---|
| T-106 (`fix/restrict-openapi-actuator`) | **cold** — started by the doorbell seconds earlier | **FAILED**, `No build record ... could be located` |
| T-102 (`feat/education-resource`) | already running | **SUCCESS** |

That is one control, not a proof, but it narrows the hypothesis list above: candidates 1 and 2 (boot-time re-provisioning racing the scan; Jenkins mid-initialisation) survive it, and "first build of a new PR job is fragile in general" does not.

**REPRODUCED 2026-08-20, same signature, same conditions** — T-107's push woke the box from `stopped` (the reaper had stopped it at 09:59:17) and `cv-domain-service/PR-6#1` failed identically: `No build record cv-domain-service/PR-6#1 could be located`, with the `Lint` stage opened and closed having executed nothing. A manually triggered rebuild on the now-warm box went green.

Three data points, and the pattern is exact:

| push | box state at push | first build |
|---|---|---|
| T-106 | **cold** (started by the doorbell seconds earlier) | **FAILED** |
| T-102 | already running | SUCCESS |
| T-107 | **cold** (reaper had stopped it at 09:59:17) | **FAILED** |

This is no longer an anecdote — it is **reproducible on demand**: stop the box, push, watch the first build die. That also makes it cheap to bisect, which the acceptance criteria below assume.

## The occurrence ordinals do not reconcile — count by PR, not by ordinal (added 2026-08-24)

**The section headings below number occurrences up to "sixth", but this file's own enumeration only supports five red builds.** The count is not cosmetic here: this task's argument for prioritisation is *"reproducible on demand"*, and the occurrence count is the evidence base for that claim. Enumerated from the evidence in this file, every confirmed instance is a **first build after a verified-or-inferred cold start that failed while a later build on the warm box passed**:

| # | Repo / build | Task that hit it | Cold start | Console signature |
|---|---|---|---|---|
| 1 | `cv-domain-service` PR-4#1 | [T-106](T-106-restrict-openapi-and-actuator-exposure.md) | doorbell, seconds earlier | not obtained |
| 2 | `cv-domain-service` PR-6#1 | [T-107](T-107-post-id-cross-person-write.md) | reaper stopped it 09:59:17 | not obtained |
| 3 | `cv-domain-service` PR-7#1 | [T-103](T-103-skills-catalog-and-assignments.md) | reaper stopped it 12:24 prev. day | not obtained |
| 4 | `cv-domain-service` PR-8#1 | [T-104](T-104-project-resource.md) | 42s after start | not obtained — headed *"Fifth occurrence"* below |
| 5 | `cv-database` PR-4#1 | [T-151](T-151-dev-seeds-cv-sections.md) | **verified** via `LaunchTime` 16:18:39 | **CONFIRMED** — headed *"Sixth occurrence"* below |
| 6 | `cv-domain-service` PR-9#1 | [T-105](T-105-experience-ordering-retrofit.md) | **verified** via `LaunchTime` 08:41:20Z → `error` 08:42:24Z = **64s** (2026-08-26) | not obtained — console still needs credentials |

**Where the drift came from, as far as the record shows.** `cv-database` PR-3#1 was written up as *"fifth occurrence"*, then challenged by stage-4 QA and **de-attributed** to [T-030](T-030-pr3-build1-success-then-error.md) — correctly, since it posts `success` before `error` and no console signature was ever obtained for it. The heading was struck, but the **ordinals that had counted it were not rolled back**, so the two entries written afterwards inherited the inflated numbering. The separate *"fourth reproduction"* label on T-103 has the same shape: the *"three data points"* table directly above it counts **T-102's SUCCESS** as a data point, which it is — it is the control — but a success is not a *reproduction* of a failure.

**Rulings, so this is not re-derived from the headings again:**
1. ~~**Five confirmed occurrences, not six.**~~ **SIX as of 2026-08-26** — row 6 (`cv-domain-service` PR-9#1) was added by [T-105](T-105-experience-ordering-retrofit.md)'s stage 3 and is counted under this table's own axis, not by heading ordinal. The count is incremented **in the table, which rules 2–3 make the authority**; the section headings below are still not renumbered. T-030's PR-3 remains excluded by this task's axis (`pending → error` with no intervening `success`), ~~and it must stay excluded unless its console log shows the empty-stage signature.~~ **That log arrived 2026-08-26 and does NOT show the signature — no `No build record`, and the stage executed real steps. [T-030](T-030-pr3-build1-success-then-error.md) is now excluded POSITIVELY, on evidence, rather than provisionally for want of a log.** The count stays at six.
2. **The headings below are left as written**, per strike-don't-delete — renumbering them would destroy the record of how the count drifted, which is the more useful artifact. **This table is the authority; the ordinals in the headings are not.**
3. **Refer to occurrences by PR number from here on** (`cv-database PR-4#1`), never by ordinal. Every ordinal in this file has now been wrong at least once.
4. **Nothing about the diagnosis changes.** It is still reproducible on demand, the measured cold-start intervals (47s, 42s, 62s, **and 64s at PR-9#1**) are unaffected, and occurrence 5's confirmed console log is what actually narrowed the candidate list — the count was never load-bearing for the mechanism, only for the priority argument.

## PR-9#1 — the cleanest reproduction yet, and it cost a real task a red build (2026-08-26, from [T-105](T-105-experience-ordering-retrofit.md))

**The whole chain was observed live for the first time**, rather than reconstructed afterwards from status timestamps. The driver knew the box was `stopped` before pushing (checked minutes earlier), pushed, and read `describe-instances` and the statuses API in sequence:

```
08:41:20Z  instance cv-project-drone  stopped -> running   (doorbell, triggered by the push)
08:42:09Z  pending  "scheduled to be built"
08:42:22Z  pending  "being built"
08:42:24Z  error    "This commit cannot be built"   <-- PR-9#1, 64s after the instance started
08:42:25Z  pending  "being built"                   <-- PR-9#2, unattended
```

Three things this adds beyond the count:

1. **The cold start is verified from the instance's own `LaunchTime`, and the interval (64s) is the longest measured** — the four known intervals now span 42–64s, all inside the first ~65 seconds after boot. That is a tight, consistent window and it is what a bisect should target.
2. **The push-then-PR double delivery fired again**, exactly as recorded for `cv-database` PR-7: opening the PR is a *second* webhook delivery, so build #2 started 1 second after #1 died, **unattended**. Nobody retriggered anything. This is why the defect stays invisible in the normal workflow — and why it is *not* invisible for a push to an existing branch.
3. **`gh pr checks` is worse here than in the plain-red case**, matching [T-030](T-030-pr3-build1-success-then-error.md)'s warning rather than this task's: the `error` is sandwiched **between two `pending`s**, so even a careful reader skimming the check list sees only "pending → …" and never the failure. Read `gh api …/statuses`.

**The console signature is still unobtained** and is not being claimed — Jenkins needs credentials this machine's policy declines. Recorded as *"matches the cold-start-fails / warm-succeeds pattern, cold start verified from LaunchTime, console signature unobtained"*, which is the wording rulings 1–3 above exist to keep honest.

## [T-030](T-030-pr3-build1-success-then-error.md)'s console CORROBORATES the leading candidate — and hands this task a residual defect (2026-08-26)

T-030 is **not** an occurrence of this defect; its log settled that and the count above is unchanged. But it supplies something this task has never had: **direct, logged evidence that Jenkins restarts mid-build on this host.**

```
[Pipeline] { (Validate migrations)
Resuming build at Sat Aug 22 07:47:16 UTC 2026 after Jenkins restart
```

Nine seconds after that build started. **This task's leading candidate — SSM re-provisioning orphaning the in-flight record — predicts exactly this class of event**, and until now it was inferred from *"checkout succeeds, then the record vanishes"* rather than observed. Now the restart itself is in a log.

The economical reading of both tasks, stated as a hypothesis and not as a unification:

| | Restart happens mid-build, and… | Result |
|---|---|---|
| **T-030** | the build record **survives**; durability resumes the build | body succeeds; the `post` block loses its `hudson.FilePath` → spurious `error` one second after `success`; `Finished: SUCCESS` |
| **this task** | the build record **does not survive** | `No build record … could be located`; the stage never runs a single `sh`; `Finished: FAILURE` |

**One trigger, two outcomes, depending on whether the build record survived.** Not proven — deliberately not written into the occurrence table, and the count stays six. What it changes is the *diagnostic target*: the two artifacts named below are now more likely to settle both tasks at once, and the SSM invocation history is the one that discriminates.

**Residual defect inherited from T-030, recorded here because T-030 closed:** every Jenkins restart mid-build also produces a **spurious `error` status after a `success`** on whatever build was in flight. Both symptoms plausibly share this task's fix — stop Jenkins restarting while builds are in flight, i.e. sequence the cold-start provisioning so Jenkins does not accept work until provisioning is done. **Hardening the `post` block against a lost `FilePath` is explicitly NOT the recommended primary fix**: it would quieten the symptom while the restart kept happening, and it would leave this task's fatal variant untouched. Written down here rather than left implied by a closed task — the [T-002](T-002-jenkins-on-drone-host.md)→[T-005](T-005-ci-secret-blast-radius.md) TLS hand-off sat unowned for eleven days for exactly that reason, and became [T-033](T-033-ci-host-tls.md).

## Acceptance criteria

- [ ] The cause is identified from evidence (Jenkins log at boot, SSM command invocation history for the instance, `docker logs jenkins`), and written down — not inferred from this file's guesses.
  - **Sharpened 2026-08-26 by T-030's console:** the SSM command invocation history is now the highest-value of the three. A restart mid-build is *observed*; what is still unknown is what caused it. If an SSM invocation overlaps the build window, candidate 1 is confirmed and the fix is **sequencing**, not a readiness probe — and a readiness probe on the doorbell was already ruled incapable of fixing this (the doorbell finishes long before branch indexing starts).
- [ ] A push to a **stopped** CI host produces a build that **succeeds on the first attempt** — proven by actually stopping the box and pushing, twice in a row so it is not luck.
- [ ] If the fix is "wait until Jenkins is ready before scanning", the readiness check is a real probe (Jenkins `/login` 200, or the job's API answering), not a fixed sleep.
- [ ] `terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass.
- [ ] T-019's checkpoint is updated to record that its criterion was met by build #3 and not by build #1.

## Definition of done

PR merged, and a cold-start push demonstrated green on first attempt.

## dev-loop notes

- **Developer:** `infrastructure-engineer`. **Reviewer:** `/code-review` + `infrastructure-engineer`. No `/security-review` — this touches boot sequencing, not an adapter §5 security path.
- **Cheap mitigation if the cause proves hard:** the reaper already knows how to talk to Jenkins. A "wait for ready" gate in the doorbell path, or simply letting the *second* scan pick it up, may be enough. Do not reach for payload replay — T-019's ruling 1 rejected that deliberately and this defect is not an argument against it.
- **Do not fold this into T-019.** T-019 is `done` and merged; this is a follow-up defect found by using it, which is the healthy outcome of that task, not a reason to reopen it.

## ~~Fifth occurrence — and the status signature is NEW~~ → **UNATTRIBUTED anomaly on the same host** (2026-08-22, from [T-152](T-152-mysql-84-parity-cv-database.md))

> **Retitled within the hour, and the retitling is the point.** This section was first written as "fifth occurrence" of T-026. **Stage-4 QA challenged the attribution and was right:** T-026's filed signature is `No build record … could be located` **with a stage that opened and closed having executed nothing**, and *that evidence was never obtained here* — the Jenkins console needs credentials this machine's policy declined. What is actually known is a status sequence on the same host, in a repo wired to the same doorbell. That is suggestive, not diagnostic.
>
> Folding it in anyway would have inflated this task's occurrence count with an instance nobody verified, and the count is the evidence base for "reproducible on demand". **The driver made exactly the error this board keeps cataloguing** — a plausible attribution written down once, which every later reader would have inherited as fact. Recorded rather than quietly edited, per this board's convention.
>
> **To resolve it, one fetch covers both open items:** the console logs for `PR-3/1` (this anomaly) and `PR-3/2` (T-152's outstanding CI criterion) at `http://13.39.59.12/jenkins/job/cv-database/job/PR-3/`. If #1 shows the empty-stage signature, this *is* occurrence five and the section can be retitled back. If it shows real stage output, it is a **different defect** and deserves its own task.

Occurrences 1–4 all presented the same way: the first build after idle goes **red**, a later build on the warm box goes green. `cv-database`'s PR-3 produced a sequence this task had not seen — cause unestablished:

```
07:47:14  pending   PR-3/1/   "This commit is being built"
07:48:06  success   PR-3/1/   "This commit looks good"
07:48:07  error     PR-3/1/   "This commit cannot be built"     <-- ONE SECOND after its own success
07:48:07  pending   PR-3/2/   "This commit is being built"
07:48:31  success   PR-3/2/   "This commit looks good"
```

**Build #1 posted `success` and then `error` one second later, for the same build.** Nobody retriggered — push-then-PR fires two webhook deliveries, as this task already documents, so #2 ran unattended on the by-then-warm box.

Two things follow:

1. **The diagnostic signature in this file is incomplete.** Anyone bisecting this by looking for "first build is red" will not match this instance, because the first build is *also* green, momentarily. Whatever fails after the executor is allocated appears able to land a success status first and then invalidate it. That is a stronger clue about *where* the failure sits than four plain red builds were — it points at something after the build is considered complete, not at the build never starting.
2. **It makes this task's own detection advice more important, not less.** `gh pr checks` reports the latest state per context and would show `pass`; the error is only visible in the full status history via `gh api repos/:owner/:repo/commits/:sha/statuses`. In this instance the *success* is also latest-but-one, so a reader skimming the history could equally miss the error between two greens.

**This is the first such event recorded in `cv-database` rather than `cv-domain-service`.** Both are wired to the doorbell, which is *consistent with* a host-level rather than repo-level cause — but on one unverified instance that is a hypothesis, not a confirmation, and the sentence that stood here claimed the latter. Cost to T-152: one spurious red status and a paragraph of explanation in its PR; no manual retrigger was needed.


## Fifth occurrence — the pattern holds, and the console signature is still unobtained (2026-08-22, from [T-104](T-104-project-resource.md))

`cv-domain-service` PR-8, read from the statuses API:

```
15:33:34  i-073e5284ca2a1ceed  stopped -> running   (doorbell, T-104's push)
15:34:16  pending  "scheduled to be built"   PR-8/1
15:34:28  pending  "being built"             PR-8/1
15:34:31  error    "This commit cannot be built"   PR-8/1   <-- 42s after the box started
15:35:12  pending  "scheduled to be built"   PR-8/2
15:35:18  pending  "being built"             PR-8/2
15:36:40  success  "This commit looks good"  PR-8/2
```

**Why this one counts where the [T-030](T-030-pr3-build1-success-then-error.md) anomaly did not.** It matches on both axes this task uses to separate itself from that one:

- It **fails outright** — `pending → error`, no intervening `success`. T-030's distinguishing detail is a build that posts `success` and then invalidates itself one second later, which points at something *after* completion. This does not do that.
- It fires **42 seconds after a cold start**, against ~47s for the earlier confirmed occurrences. The box had been stopped by the reaper and was woken by the push that produced the build.

**What is still NOT evidenced, stated plainly because overstating it is the error this task already made once.** The filed signature is `No build record … could be located` **plus a stage that opens and closes having executed nothing**, and that requires the Jenkins console — authenticated, and the credential path is still declined on this machine. So this is *"matches the cold-start-fails / warm-succeeds pattern, console signature unobtained"*, not *"confirmed occurrence five"*. The same one fetch that settles [T-152](T-152-mysql-84-parity-cv-database.md)'s outstanding criterion and [T-030](T-030-pr3-build1-success-then-error.md) would settle this too — three open items behind a single Jenkins login.

**Nobody retriggered it.** Pushing the branch and opening the PR fire two separate webhook deliveries, so PR-8/2 ran unattended on the warm box — the corrected severity claim in this file, holding for a fourth time.

**The `gh pr checks` caution demonstrated live.** GitHub's status API keeps only the latest state per context, so PR-8 renders green and `gh pr checks 8` reports a pass while the `error` sits in the history behind it. Anyone verifying the eventual fix through `gh pr checks` will confirm a fix that never ran. The statuses API is the only honest read, and it is what produced the table above.


## Sixth occurrence — and this is the first one where the cold start was *verified* rather than inferred (2026-08-22, from [T-151](T-151-dev-seeds-cv-sections.md))

`cv-database` PR-4:

```
16:18:39  i-073e5284ca2a1ceed  LaunchTime  (reaper had stopped it after T-104's builds)
16:19:23  pending  "scheduled to be built"   PR-4/1
16:19:39  pending  "being built"             PR-4/1
16:19:41  error    "This commit cannot be built"   PR-4/1   <-- 62s after the box started
16:20:10  pending  "scheduled to be built"   PR-4/2
16:20:19  pending  "being built"             PR-4/2
16:20:44  success  "This commit looks good"  PR-4/2
```

**The premise was checked before the attribution was written, and that is the point of this entry.** The CI host had been `running` since 15:33:34 for [T-104](T-104-project-resource.md)'s builds, ~45 minutes earlier in the same session. **Had it still been up, this would not have been T-026 at all** — it would have been a warm-box failure, a different defect, and calling it T-026 would have repeated precisely the error that got [T-030](T-030-pr3-build1-success-then-error.md) filed the day before.

`aws ec2 describe-instances` settles it: `LaunchTime` had moved to **16:18:39**, so T-019's reaper stopped the box between the two tasks and T-151's push cold-started it again. The failure is 62 seconds after that start.

**Three confirmed cold-start intervals now: 47s, 42s, 62s.** All three are `pending → error` with no intervening `success`, which is the axis that separates this task from T-030.

**The console signature is still unobtained** — Jenkins needs credentials this machine's policy declines — so this is *"matches the cold-start-fails / warm-succeeds pattern, cold start verified, console signature unobtained"*. That qualifier is now attached to occurrences five and six identically, and it is not weakening with repetition: six matching status sequences are still not the one console log that would confirm the mechanism.

**What this occurrence adds beyond the count:** it is the first on **`cv-database`** whose shape is confirmed. The earlier `cv-database` anomaly (PR-3) is the one that became T-030 for lacking exactly this. So the defect is now observed in two repos, both wired to the same doorbell, which points at the shared Jenkins/host boot path rather than at anything repo-specific.

**One Jenkins login still closes four items**: occurrences five and six, [T-030](T-030-pr3-build1-success-then-error.md), and [T-152](T-152-mysql-84-parity-cv-database.md)'s outstanding CI-console criterion.


## THE CONSOLE LOG ARRIVED — signature confirmed, and the diagnosis is narrowed (2026-08-22)

The human supplied the console text for `cv-database` PR-4 builds **#1** and **#2** — the fetch this task, [T-030](T-030-pr3-build1-success-then-error.md) and [T-152](T-152-mysql-84-parity-cv-database.md) had all been waiting on. **Occurrence six is no longer "matches the pattern, signature unobtained". It is confirmed, both halves, verbatim.**

### The filed signature, exact

```
[Pipeline] stage
[Pipeline] { (Validate migrations)
[Pipeline] }                                  <-- opened and closed. NO [Pipeline] sh node at all.
[Pipeline] // stage
[Pipeline] stage
[Pipeline] { (Deploy)
Stage "Deploy" skipped due to earlier failure(s)
...
ERROR: No build record cv-database/PR-4#1 could be located.
Finished: FAILURE
```

Both halves this task filed — *`No build record … could be located`* **plus** *a stage that opened and closed having executed nothing* — are present in one log. Five prior occurrences were argued from status sequences; this one is read off the console.

### The new fact, and it moves the diagnosis

**The build did substantial real work before it died.** Build #1's `Declarative: Checkout SCM` stage ran a complete, successful clone into a fresh workspace:

```
Cloning the remote Git repository
 > git init /var/lib/jenkins/workspace/cv-database_PR-4
 > git fetch --no-tags --force --progress -- https://github.com/erfeamor/cv-database.git ...
Merge succeeded, producing e4313040115765aa0cd60aab0bddaa642cb537b0
Commit message: "docs(dev-seeds): document the key-only guard's two failure modes (T-151)"
First time build. Skipping changelog.
```

So the record was **lost mid-build**, between a successful checkout and the first `sh` step — not absent at build start. That single fact re-ranks this file's three standing candidates:

| Candidate (as filed) | Status after the log |
|---|---|
| **1. Boot-time SSM re-provisioning races the scan**, orphaning the in-flight record | **Promoted to leading.** It is the only candidate that predicts *checkout succeeds, then the record vanishes*: JCasC/job-dsl re-creating the job underneath a running build orphans exactly the record the next step needs. T-019's apply note puts SSM re-provisioning at ~37s, and the failure lands 62s after boot. |
| 2. Jenkins mid-initialisation — *"the job exists but its build directory or the queue is not ready"* | **Weakened as stated.** A not-ready Jenkins does not clone a repository, merge a commit and print a changelog line first. A *variant* survives — lazy-loading completing mid-build and replacing in-memory state — but the filed wording is not what happened. |
| 3. Disk/permission timing on `/var/lib/jenkins` after the boot remount | **Weakened.** The clone wrote to `/var/lib/jenkins/workspace/cv-database_PR-4` successfully in the same window. |

**This is a narrowing, not a diagnosis.** Acceptance criterion 1 requires the cause identified *from evidence* — the console is now on the table, but the two artifacts that would settle it are still missing: **Jenkins' own log for the boot window** and the **SSM command invocation history** for `i-073e5284ca2a1ceed` around 16:18:39–16:19:41. If the SSM invocation overlaps the build window, candidate 1 is confirmed and the fix is sequencing, not a readiness probe.

### Both builds are triggered by `Branch indexing`, exactly as designed

```
Branch indexing
Obtained Jenkinsfile from e431304...+5942881... (745afe3...)
```

Neither build says "Started by GitHub push". This **confirms [T-019](T-019-ci-host-on-demand.md)'s `ci-on-demand.tf` ruling 1** — the doorbell deliberately forwards no payload and Jenkins' own folder scan rediscovers the branch after boot. The real chain is:

```
push -> doorbell -> ec2:StartInstances -> Jenkins boots -> branch indexing -> build
```

That is *why* the first build races the boot: nothing waits for Jenkins to finish coming up, because nothing was ever designed to. Worth stating plainly, because it means **a readiness probe on the doorbell side cannot fix this** — the doorbell is finished long before Jenkins starts indexing. Acceptance criterion 3's *"if the fix is 'wait until Jenkins is ready before scanning'"* is aimed at the right layer: the scan, not the trigger.

### What build #2 proves by contrast

Same commit, same job, warm box, 63 seconds later — and the `Validate migrations` stage executes fully (network created, MySQL started, Flyway migrated, cleanup ran). **Identical input, opposite outcome**, with the only difference being that Jenkins had finished booting. That is the control this task has wanted since it was filed, and it is now in the same evidence set as the failure.
