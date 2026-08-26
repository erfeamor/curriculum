---
id: T-030
title: "A Jenkins build posted success then error one second later — DIAGNOSED: a mid-build Jenkins restart, NOT T-026"
repo: cv-infra
status: done
owner: tech-product-owner
branch: fix/build-status-success-then-error
pr: none                  # deliberately empty, same sentinel and reason as T-010: this task's four acceptance criteria are ALL DIAGNOSTIC ("obtain the log", "record a ruling", "identify the mechanism", "reflect the count"), so it closes on evidence, not on a diff. No code change was ever in its scope. The residual DEFECT it uncovered is handed to T-026 explicitly — see the resolution section and T-026's own "shared trigger" entry — rather than left implied by a closed task.
depends_on: []
resolved: 2026-08-26
risk: normal
security_review: false   # CI reliability, not exposure — same rationale as T-026
---

## Goal

Establish what happened to `cv-database` PR-3 build #1 on 2026-08-22, and whether it is [T-026](T-026-first-build-after-cold-start-fails.md) or a **different defect**.

Read via `gh api repos/erfeamor/cv-database/commits/b0f346c/statuses`:

```
07:47:14  pending  building           PR-3/1
07:48:06  success  "looks good"       PR-3/1
07:48:07  error    "cannot be built"  PR-3/1   <-- one second after its own success
07:48:07  pending  building           PR-3/2
07:48:31  success  "looks good"       PR-3/2   <-- unattended, nobody retriggered
```

## Why this is a separate task and not a fifth T-026 entry

**It was written into T-026 as "occurrence five" and that attribution was withdrawn within the hour**, after stage-4 QA challenged it. The reasoning matters more than the outcome:

- T-026's filed signature is `No build record … could be located` **plus a stage that opened and closed having executed nothing**. That evidence was never obtained here — the Jenkins console is authenticated and the credential path was declined.
- What is actually known is a *status sequence* on the same host, in a repo wired to the same doorbell. Suggestive; not diagnostic.
- T-026's occurrence count is the evidence base for its claim of being "reproducible on demand". Padding it with an unverified instance would corrode exactly the thing that makes it actionable.

**The distinguishing detail is that build #1 posted `success` first.** All confirmed T-026 occurrences *(“four” as written on 2026-08-22; the reconciled count is **five** — see T-026's 2026-08-24 occurrence table, which found the ordinals inflated by a withdrawn attribution: this one)* are a build that fails outright. A build that succeeds and then invalidates itself one second later points at something *after* completion — status reporting, a post-build step, the multibranch scan — rather than at a build that never started. If that holds, it is a different defect with a different fix.

## The one action that settles it

Fetch the console log for `http://13.39.59.12/jenkins/job/cv-database/job/PR-3/1/`. Requires Jenkins credentials (`/cv-project/dev/ci/jenkins-admin-password` in SSM).

- **Empty stage + `No build record`** → this *is* T-026 occurrence five. Fold this task into T-026 and close it as a duplicate.
- **Real stage output** → a separate defect. This task keeps its own life and needs its own diagnosis.

**The same fetch also closes [T-152](T-152-mysql-84-parity-cv-database.md)'s outstanding criterion** (build **#2**'s Flyway banner, which proves the migration gate ran on 8.4). One authenticated session settles both; do them together.

## Acceptance criteria

- [ ] Build #1's console log obtained and the signature stated.
- [ ] A ruling recorded: duplicate of T-026, or a distinct defect with its own diagnosis.
- [ ] If distinct: the mechanism identified, or the task explicitly parked as "reproduced, cause unknown" rather than left implying it was understood.
- [ ] T-026's occurrence count reflects the ruling — corrected upward only if the evidence supports it.

## Watch-out

**`gh pr checks` is useless here and actively misleading** — it keeps only the latest state per context, so it reports `pass` while both the `success` and the `error` sit in the history. Worse than in T-026's plain-red case: here the error is sandwiched *between two greens*, so even someone reading the history casually can skim past it. Always `gh api …/statuses`.

## Provenance

Observed on [T-152](T-152-mysql-84-parity-cv-database.md)'s PR, 2026-08-22. Misattributed to T-026 by the driver, caught by stage-4 QA, corrected in T-026 and filed here at T-152's H2 gate.


## Still open — but the discriminator is now exact (2026-08-22)

**The console text that arrived is for PR-4, not PR-3.** This task is about `cv-database` **PR-3 build #1**, so it is **not** settled by it. Recorded plainly because the prediction repeated across several board entries — *"one Jenkins login closes four items"* — was **wrong on this one**: the fetch closed [T-026](T-026-first-build-after-cold-start-fails.md)'s signature and [T-152](T-152-mysql-84-parity-cv-database.md)'s outstanding criterion, but those two plus occurrences five and six were all the same PR's builds. T-030 needs its own log.

**What changed anyway is that the test is now exact rather than descriptive.** T-026's signature has been read off a real console, so PR-3 build #1's log settles this in one glance:

| If PR-3#1 shows | Then |
|---|---|
| `[Pipeline] { (Validate migrations)` immediately followed by `[Pipeline] }` with **no `[Pipeline] sh`**, and `ERROR: No build record cv-database/PR-3#1 could be located.` | It **is** T-026. Fold this task in as another occurrence and close it. |
| The `Validate migrations` stage executing real steps (`docker network create`, `docker run … mysql:8.4`, Flyway output) and **then** a failure | It is a **different defect** and this task stands on its own. The `success`-then-`error` one second apart points at status reporting or a post-build step, not at a build that never started. |

**One more reason to expect the second outcome.** T-026's confirmed mechanism is *the build record disappearing mid-build*, and a build in that state never reaches a terminal `success` — build #1 of PR-4 went straight to `FAILURE`. T-030's sequence has a **`success` posted first**, which means the build completed and reported. Those are hard to reconcile, so the prior mildly favours "different defect" — but that is an argument, and this task exists because an argument was mistaken for evidence once already. **Fetch the log.**

`http://13.39.59.12/jenkins/job/cv-database/job/PR-3/1/consoleText`


## RESOLVED — the console arrived, and this task's own discriminator ruled it a DIFFERENT DEFECT (2026-08-26)

The human supplied both consoles: `cv-database` PR-3 build **#1** and build **#2**. The discriminator table above was applied as written, and it landed on the second row.

### The signature, stated as this task required

**`No build record … could be located` appears NOWHERE in build #1's log**, and the `Validate migrations` stage did **not** open and close empty. It executed real steps, exactly the second row's wording:

```
[Pipeline] { (Validate migrations)
Resuming build at Sat Aug 22 07:47:16 UTC 2026 after Jenkins restart   <-- THE CAUSE
[Pipeline] sh
+ docker network create cv-db-ci-1
+ docker run -d --rm --name cv-mysql-ci-1 ... mysql:8.4
+ docker run --rm ... flyway/flyway:10 migrate
Successfully applied 1 migration to schema `cv`, now at version v1
```

**So: NOT [T-026](T-026-first-build-after-cold-start-fails.md). A distinct defect.** The prior recorded above — *"mildly favours the second outcome"* — was right, and it was right for the stated reason: T-026's mechanism kills a build before it reports anything, and this build reported `success` first because **its body genuinely succeeded**. `Finished: SUCCESS`.

### The mechanism — identified, not parked

**Jenkins restarted mid-build.** Build #1 started 07:47:07, cloned and checked out normally, entered `Validate migrations`, and then the controller went down. Pipeline durability **resumed** it at 07:47:16 (the log says so in as many words), it re-queued for an executor — *"Still waiting to schedule task / Waiting for next available executor"* interleaved with the `mysql:8.4` layer pull — and ran the stage to completion. Migrations applied. Stage-level cleanup ran.

Then, after `End of Pipeline`, the log shows a **second** resumption (`Ready to run at Sat Aug 22 07:48:05 UTC 2026`) and the actual failure:

```
Error when executing always post condition:
org.jenkinsci.plugins.workflow.steps.MissingContextVariableException:
    Required context class hudson.FilePath is missing
        at WorkflowScript.run(WorkflowScript:32)
```

**`Jenkinsfile:32` is the `sh` inside `post { always }`** (the `docker rm -f` / `network rm` cleanup); the second, identical exception at `WorkflowScript:9` is the main `sh` in `steps`. Both are the same fault: **the `hudson.FilePath` — the node/workspace handle — did not survive the restart into the post block, so `sh` had no context to run in.**

That is the whole `success`-then-`error` sequence, one second apart:

| | |
|---|---|
| 07:48:06 `success` | the pipeline **body** completed — migration applied, cleanup done |
| 07:48:07 `error` | the `post { always }` block then threw `MissingContextVariableException`, and the GitHub Branch Source plugin reported it |

Note the build's own verdict is **`Finished: SUCCESS`** while GitHub's last word is `error`. The two disagree, which is why this looked inexplicable from the statuses API alone.

**The `|| true` in that post block is irrelevant here** — a NOTE from [T-152](T-152-mysql-84-parity-cv-database.md)'s security review and listed out-of-scope by [T-154](T-154-jenkins-pipeline-timeout.md). It suppresses a *command's* exit code; here `sh` never ran at all.

### Build #2 is the control, and it is clean

Same commit, same job, triggered 07:47:15 — it waited for the executor build #1 was holding, then ran start to finish with **no restart, no resume, no exception**, `Finished: SUCCESS`, and a single `success` status. Identical input, no restart, no anomaly.

### What this does for T-026 — corroboration, and a shared trigger

Stated carefully, because overstating an attribution is the error that created this task in the first place.

**These remain two distinct defects** — the discriminator settled that. But this log is the first **direct, logged evidence that Jenkins restarts mid-build on this host**, nine seconds after a build started, inside the cold-start window. T-026's leading candidate — promoted when the PR-4 console arrived — is *"SSM re-provisioning orphaning the in-flight record"*, the only candidate that predicts *checkout succeeds, then the record vanishes*.

~~This is exactly that event, **survived**.~~ **CORRECTED THE SAME DAY, 2026-08-26 — the SSM half of that sentence is REFUTED.** The invocation history was read hours after this section was written: **44 invocations, and not one on 2026-08-20, 08-21 or 08-22.** So the restart observed here was **not** SSM re-provisioning, and neither were the T-026 occurrences. What survives is the weaker but still useful half — *a restart happens mid-build, inside the first minute after boot* — with its **cause now open**, not identified. Full elimination table on [T-026](T-026-first-build-after-cold-start-fails.md).

**Recorded as a correction rather than an edit**, because the shape is this board's signature: a plausible attribution written down confidently, going stale within hours, in a task whose entire reason for existing is that exact error being made once already. Caught this time by reading the artifact instead of stopping at the narrative.

The most economical reading of both tasks:

| | Restart happens mid-build, and… | Result |
|---|---|---|
| **T-030** (this) | the build **record survives**; durability resumes it | body succeeds, post block loses its `FilePath` → spurious `error` after `success`, `Finished: SUCCESS` |
| **T-026** | the build **record does not survive** | `No build record … could be located`, stage never runs an `sh`, `Finished: FAILURE` |

**One trigger, two outcomes, depending on whether the build record survived the restart.** That is a hypothesis with strong support, not a proof — it is not being written into T-026 as a confirmed unification, and T-026's occurrence count is **unchanged at six** (see below).

### The residual defect is handed to T-026, not left in a closed task

The spurious `error` will recur on any Jenkins restart mid-build. **Both tasks plausibly share one fix**: stop Jenkins restarting while builds are in flight — i.e. sequence the cold-start provisioning so Jenkins does not accept work until it is done being provisioned. That is T-026's fix, and it would close this symptom as a side effect.

Hardening the `post` block against a lost `FilePath` would only make the symptom quieter while the restart kept happening, so it is **explicitly not recommended as the primary fix**. Recorded on [T-026](T-026-first-build-after-cold-start-fails.md) itself so the hand-off does not evaporate the way [T-002](T-002-jenkins-on-drone-host.md)'s TLS finding did into [T-005](T-005-ci-secret-blast-radius.md) for eleven days.

### Acceptance criteria — all four met

- [x] Build #1's console log obtained and the signature stated: no `No build record`, stage executed real steps, `Resuming … after Jenkins restart`.
- [x] Ruling recorded: **distinct defect**, not a duplicate of T-026.
- [x] Mechanism identified — a mid-build controller restart costing the post block its `hudson.FilePath`. Not parked as "cause unknown".
- [x] T-026's occurrence count reflects the ruling: **unchanged at six.** The evidence does not support adding this one — it now **excludes** it positively rather than for want of a log, which is a stronger statement than the provisional exclusion T-026's ruling 1 has carried since 2026-08-24.

### The prediction this task was filed to correct, closed out honestly

The board said four times that *"one Jenkins login closes four items"*. It did not: PR-4's console closed T-026's signature and T-152's criterion, and this needed **its own** log, obtained four days later. The count was wrong because nobody re-derived which PR each item actually belonged to. That is the whole reason this task exists as a separate line, and it is the reason it was right to keep it separate.
