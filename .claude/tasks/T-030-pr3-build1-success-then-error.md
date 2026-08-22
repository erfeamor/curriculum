---
id: T-030
title: "A Jenkins build posted success and then error one second later — cause unknown, not yet attributable to T-026"
repo: cv-infra
status: todo
owner:
branch: fix/build-status-success-then-error
pr:
depends_on: []
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

**The distinguishing detail is that build #1 posted `success` first.** All four confirmed T-026 occurrences are a build that fails outright. A build that succeeds and then invalidates itself one second later points at something *after* completion — status reporting, a post-build step, the multibranch scan — rather than at a build that never started. If that holds, it is a different defect with a different fix.

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
