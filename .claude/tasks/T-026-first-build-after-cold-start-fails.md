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

## Acceptance criteria

- [ ] The cause is identified from evidence (Jenkins log at boot, SSM command invocation history for the instance, `docker logs jenkins`), and written down — not inferred from this file's guesses.
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
