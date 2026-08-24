---
id: T-154
title: "cv-database's Jenkins pipeline can hang indefinitely and tie up the only CI host"
repo: cv-database
status: todo
owner:
branch: fix/jenkins-pipeline-timeout
pr:
depends_on: []
risk: normal
security_review: true   # adapter §5 — `Jenkinsfile` is an unconditional /security-review path
---

## Goal

`cv-database/Jenkinsfile` has **no `timeout {}` wrapper**. Its failure mode is not a red build, it is an unbounded one.

Flyway 10 bundles the MariaDB driver, so a MySQL 8 JDBC URL missing `?allowPublicKeyRetrieval=true` **does not error — it retries**, and `Jenkinsfile:26` sets `FLYWAY_CONNECT_RETRIES=60`. With no pipeline timeout, that build occupies the executor until someone notices.

## Why this is worth a task, and why the cost model is the argument

The reviewer flagged this **moderately urgent for a cost reason, not a correctness one**. There is exactly one CI host, it is shared by `cv-database` and `cv-domain-service`, and since [T-019](T-019-ci-host-on-demand.md) it is **started on push and stopped when quiet**. A hung build defeats the "stopped when quiet" half: the reaper sees an active build and leaves the box up.

[T-020](T-020-cost-model-correction.md) prices that box at **~$17.24/month** if left running, and the measured run rate ($0.6837/day) *depends on it being stopped* — a point [T-012](T-012-aws-endgame-decision.md) makes in terms: "the low rate rests on a stopped box, and one forgotten `start-instances` restores the November cliff." A hung build is that forgotten start, arriving by accident instead of by hand.

**It is latent, not live.** `allowPublicKeyRetrieval` is verified intact at `flyway.conf:6` and `Jenkinsfile:22` as of [T-152](T-152-mysql-84-parity-cv-database.md) (2026-08-22). This task adds the guard that makes the failure loud if it ever regresses.

## Bundle with T-153 — see that task for the full proposal (2026-08-24, on the human's instruction)

**[T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) edits the same file, in the same repo, with the same forced `/security-review`.** Running both separately spends two of everything — branches, PRs, security reviews, gate pairs — on one file. **The proposal, options and the board-rule-2 tension are written up in [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md); H1 decides.**

**What must survive the merge, if it happens** — these are this task's contributions and they are the substantive half:
- **`timeout {}` with a justified bound**, not a copied number.
- **The healthcheck wait** (below): the console evidence shows Flyway's retry budget is the pipeline's *actual* synchronisation mechanism on **every** build, not a dormant safety net.
- **"Demonstrate the guard actually fires."** A timeout nobody has watched trigger is exactly the unverified-claim class this board keeps finding. Force a hang on a scratch branch and show the build failing at the bound.
- **The `cv-domain-service` check** — same gap, different repo, so it is *filed*, never fixed here (board rule 3).

**Do not let this become "T-153 plus a timeout".** The healthcheck finding below changed this task's premise after it was filed — the hang is not latent — and that is the more valuable half.

## Scope

- Wrap the pipeline (or at minimum the `Validate migrations` stage) in `timeout(time: N, unit: 'MINUTES')`. Pick N from observed build times — successful builds run ~90–100s, so a generous bound is still an order of magnitude tighter than "forever". **Justify the number rather than copying one.**
- Consider whether `cv-domain-service`'s Jenkinsfile has the same gap. If it does, say so — **do not fix it here** (different repo, board rule 3); file it.

**Out of scope:** the `post { always }` cleanup swallowing failures via `|| true`, and images being pulled by mutable tag. Both were raised as NOTEs in T-152's security review, both pre-existing, neither related to hanging.

## Acceptance criteria

- [ ] The pipeline fails on timeout rather than hanging, with the bound and its justification recorded in the PR.
- [ ] A normal build still passes comfortably inside the bound — verify against real build durations, not an estimate.
- [ ] **Demonstrate the guard actually fires.** A timeout nobody has seen trigger is the same class of unverified claim this board keeps finding; force a hang (e.g. point `FLYWAY_URL` at an unreachable host on a scratch branch) and show the build failing at the bound.
- [ ] `cv-domain-service`'s pipeline checked for the same gap, and the finding recorded either way.

## Watch-outs

- **[T-026](T-026-first-build-after-cold-start-fails.md) applies** — the first build after idle may fail spuriously. Re-run on the warm box before debugging. Read the statuses API, not `gh pr checks`, which reports `pass` while a failed build sits in the history.
- Verifying this task means *deliberately hanging a build on the shared host*. Do it on a scratch branch, keep the bound short for the test, and confirm the box is released afterwards — the whole point is cost.

## Definition of done

PR open against `master` from `fix/jenkins-pipeline-timeout`, the guard demonstrated firing, task updated.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2 — `cv-database`). **Reviewers:** `/code-review` + `infrastructure-engineer` (owns all CI config) + `/security-review` (forced by the `Jenkinsfile` path).

## Provenance

Raised by `infrastructure-engineer` in [T-152](T-152-mysql-84-parity-cv-database.md)'s stage-2 review, 2026-08-22, and flagged there as out of scope for that PR under board rule 3. Filed at T-152's H2 gate.


## The retry loop is NOT latent — it engages on every build (2026-08-22)

This task called the hang *"latent, not live"*, on the grounds that `allowPublicKeyRetrieval` is intact so Flyway never enters its retry path. **The console log for `cv-database` PR-4 build #2 shows the retry path executing**, four times, on a perfectly healthy build:

```
+ docker run -d --rm --name cv-mysql-ci-2 ... mysql:8.4
+ docker run --rm ... -e FLYWAY_CONNECT_RETRIES=60 flyway/flyway:10 migrate
WARNING: Connection error: ... Socket fail to connect to host:cv-mysql-ci-2, port:3306. Connection refused
Retrying in 1 sec...
WARNING: Connection error: ... Connection refused
Retrying in 2 sec...
WARNING: Connection error: ... Connection refused
Retrying in 4 sec...
WARNING: Connection error: ... Connection refused
Retrying in 8 sec...
Database: jdbc:mysql://cv-mysql-ci-2:3306/cv?allowPublicKeyRetrieval=true (MySQL 8.4)
```

**The cause is mundane and permanent: the Jenkinsfile starts MySQL with `-d` and immediately runs Flyway against it, with no healthcheck wait.** The retries *are* the wait. So the mechanism this task is about is not dormant waiting for a config regression — it is the pipeline's normal startup path, and it succeeds only because MySQL happens to win the race within ~15 seconds.

**Sharpen the argument accordingly.** The observed backoff **doubles** (1, 2, 4, 8 …) against `FLYWAY_CONNECT_RETRIES=60`. If MySQL fails to come up at all — a bad image pull, a full disk, the 8.4 tag moving — the build does not fail fast; it walks that backoff to exhaustion while **holding the only CI host up**, defeating [T-019](T-019-ci-host-on-demand.md)'s reaper exactly as this task predicts. Do not put a number on the total in the task record without checking Flyway 10's `connectRetriesInterval` cap; the point stands without one, and an unverified figure here would be the kind of claim this board keeps having to retract.

**A second, cheaper fix is now visible** and should be priced at H1 alongside `timeout {}`: **wait for the MySQL container to report healthy before invoking Flyway**, so the retry budget stops being the synchronisation mechanism. That does not replace the timeout — a timeout bounds *every* hang, not just this one — but it removes the path that currently exercises it on every single build.
