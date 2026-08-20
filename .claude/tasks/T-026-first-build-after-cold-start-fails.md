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
