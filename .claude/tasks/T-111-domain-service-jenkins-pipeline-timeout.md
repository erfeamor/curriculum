---
id: T-111
title: "cv-domain-service's Jenkins pipeline has no timeout, and it shares the CI host's ONLY executor with cv-database"
repo: cv-domain-service
status: todo
owner:
branch: fix/jenkins-pipeline-timeout
pr:
depends_on: []
risk: normal
security_review: true   # adapter §5 — `Jenkinsfile` is an unconditional /security-review path
---

## Goal

`cv-domain-service/Jenkinsfile` has **no `timeout {}` wrapper** and no `options {}` block at all — verified 2026-08-27. Its failure mode is not a red build, it is an unbounded one. This is [T-154](T-154-jenkins-pipeline-timeout.md)'s defect in a second repo, with a **different hang mechanism** and a **worse blast radius**.

## Why this is worth its own task and not a footnote on T-154

T-154's argument is the cost model: one CI host, started on push and stopped when quiet since [T-019](T-019-ci-host-on-demand.md), and a hung build defeats the "stopped when quiet" half. **That argument transfers unchanged.** Two things do not, and they are why this is filed separately rather than as a line in T-154:

### 1. The hang mechanism is different, so T-154's fix does not port

T-154's hang is Flyway's connect-retry backoff against a MySQL container that has not come up, and its cheaper second fix is *wait for the healthcheck before invoking Flyway*. **There is no Flyway and no MySQL container in this pipeline.** The unbounded steps here are:

- `mvn -B checkstyle:check`, `mvn -B test`, `mvn -B package` — Maven resolving against `repo.maven.apache.org`, which has no bounded retry budget at all. A slow or wedged connection stalls indefinitely rather than backing off to a limit.
- `docker build` (`Jenkinsfile:39`) — a base-image pull with the same property.

**Observed, not hypothesised (2026-08-26):** during T-026's verification a build sat in `Downloaded from central: …` for minutes, and the surviving log ends mid-download. That build was killed by a deliberate `stop-instances`, so it is **not** evidence of a spontaneous hang — but it does establish that this pipeline spends real, unbounded wall-clock in a step nothing bounds.

### 2. `numExecutors: 1` — the two repos are not independent

`cv-infra/templates/jenkins-provision.sh:63` sets **`numExecutors: 1`** on the single Jenkins instance, and both `cv-domain-service` and `cv-database` are seeded onto it. So a hang in *either* repo blocks *every* build in *both*.

**Observed live on 2026-08-26**, and this is the part neither T-154 nor anything else on the board records: with one build occupying the executor, the next build logged

```
[Pipeline] node
Still waiting to schedule task
Waiting for next available executor
```

and sat there until the first reached a terminal state. **The queue is real and it is repo-blind.** T-154's cost argument therefore understates the damage in both directions: a hung `cv-database` build also blocks `cv-domain-service`, and vice versa. Neither task said so.

**This also sharpens the priority ordering between the two.** `cv-domain-service` is the busier repo on this host — 9 PR branch children versus 4 for `cv-database` (read off `/var/lib/jenkins/jobs/*/branches/` on 2026-08-26) — so it holds the shared executor more often and is the likelier place for a hang to start.

## The reaper is NOT a mitigation — confirmed on T-154, and it applies here identically

T-154 records the reaper's source being read on 2026-08-26: `lambda/ci_reaper/index.py` requires two signals, CPU is a **veto and never the sole signal**, and `jenkins_is_idle()` returns busy on any unclear answer. A Maven download burns almost no CPU, so it sails through the CPU veto and is then held indefinitely by the executor count. `IDLE_WINDOW_MINUTES = 20` never elapses in Jenkins' eyes while the build is running.

**Do not re-derive this** — it is settled evidence, quoted here so this task is not refined against the wrong premise. The `timeout {}` really is the only bound.

## Scope

- Wrap the pipeline (or at minimum the Maven stages and `Docker image`) in `timeout(time: N, unit: 'MINUTES')`. **Justify N from observed build times rather than copying a number.** A useful datum: a clean, fully green run of this pipeline completed all five stages with 141 tests in roughly two minutes on a warm box (2026-08-26) — so a generous bound is still an order of magnitude tighter than "forever". A cold box with an empty `~/.m2` is materially slower and the bound must survive it.
- Consider whether the Maven steps deserve their own tighter bound than `docker build`.

**Out of scope:** the dead `branch 'main'` Deploy gate and its stale placeholder comment — that is **[T-110](T-110-domain-service-jenkins-deploy-dead-gate.md)**. See the bundling note. Also out of scope: making the `Docker image` stage actually push, which no board task owns (recorded in T-110).

## Acceptance criteria

- [ ] The pipeline fails on timeout rather than hanging, with the bound and its justification recorded in the PR.
- [ ] A normal build still passes comfortably inside the bound — verified against **real build durations on this host**, cold `~/.m2` included, not an estimate.
- [ ] **Demonstrate the guard actually fires.** T-154's sharpest criterion and it applies here unchanged: a timeout nobody has watched trigger is the unverified-claim class this board keeps cataloguing. Force a hang on a scratch branch and show the build failing at the bound.
- [ ] Confirm the executor is released afterwards and the reaper subsequently stops the box — the entire argument is cost, so a guard that fires but leaves the host up has not delivered.

## Watch-outs

- **Verifying this means deliberately hanging a build on the shared host, which blocks the other repo too** (`numExecutors: 1`). Do it on a scratch branch, keep the test bound short, and confirm the box is released afterwards.
- **This interacts with [T-019](T-019-ci-host-on-demand.md)'s one untested acceptance criterion** — *"a build in progress is never killed"*, whose second half has never been exercised (reconciled 2026-08-27). Whoever runs this task is already starting builds and watching the reaper, so it is the cheapest opportunity on the board to settle T-019's criterion too. **Not a dependency in either direction** — recorded so the chance is not missed, the way [T-002](T-002-jenkins-on-drone-host.md)→[T-005](T-005-ci-secret-blast-radius.md)'s hand-off sat unowned for eleven days.
- ~~**[T-026](T-026-first-build-after-cold-start-fails.md) applies** — the first build after idle may fail spuriously.~~ **Fixed 2026-08-26** (cv-infra `1deebb4`, [#21](https://github.com/erfeamor/cv-infra/pull/21)). The first build after idle is now trustworthy. Struck rather than deleted because sibling tasks still carry the live version of this warning.
- **Read the statuses API, not `gh pr checks`**, which reports `pass` while a failed build sits in the history behind it.

## Definition of done

PR open against `master` from `fix/jenkins-pipeline-timeout`, the guard demonstrated firing, task updated.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2 — `cv-domain-service` is its layer). **Reviewers:** `/code-review` + `infrastructure-engineer` (owns all CI config) + `/security-review` (forced by the `Jenkinsfile` path).
- **Bundle with [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md)** — same file, same repo, same forced reviewer set, exactly the T-153/T-154 situation. **H1 decides**; T-153's recommended option (a) — one task absorbs the other and the absorbed one closes recording where its criteria went — applies here unchanged. If bundled, **this task's "demonstrate the guard actually fires" must survive the merge**; it is the sharper of the two tasks' criteria.

## Provenance

Found 2026-08-27 while answering *"what should be the next tasks?"* against the board. [T-154](T-154-jenkins-pipeline-timeout.md) carries *"cv-domain-service's pipeline checked for the same gap, and the finding recorded either way"* as an explicit acceptance criterion, and [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) repeats the instruction. That check has now been run ahead of both: **the gap is present**, and the two findings above — the different hang mechanism, and the single shared executor with an observed queue — are new to the board rather than a restatement of T-154. Filed rather than left to be rediscovered, so T-154's criterion can be closed by reference.
