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
