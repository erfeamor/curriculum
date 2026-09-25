---
id: T-111
title: "cv-domain-service Jenkinsfile hygiene: no pipeline timeout on the CI host's ONLY executor (shared with cv-database), and a Deploy stage gated on a branch that does not exist (absorbs T-110)"
repo: cv-domain-service
status: done
owner: tech-product-owner
branch: fix/jenkins-pipeline-hygiene   # renamed 2026-09-23 from fix/jenkins-pipeline-timeout when T-110 was absorbed; matches T-153's name for the same bundle in cv-database. Never pushed under the old name.
pr: https://github.com/erfeamor/cv-domain-service/pull/10
depends_on: []
risk: normal
security_review: true   # adapter §5 — `Jenkinsfile` is an unconditional /security-review path
checkpoint:
  stage: done   # merged 0f59782 (squash of cv-domain-service#10), 2026-09-24 — H2 accepted by the human
  repo: cv-domain-service
  branch: fix/jenkins-pipeline-hygiene
  worktree: none   # removed after merge
  pr: https://github.com/erfeamor/cv-domain-service/pull/10
  commit: 0f59782   # squash merge on master (branch head was f54866b)
  developer: tech-product-owner   # proposed at H1: ~10-line Jenkinsfile change done inline, as T-156
  reviewers: [code-review, infrastructure-engineer, security-review]
  risk: normal
  security_review: true   # adapter §5: Jenkinsfile
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: none   # verification is Jenkins on the CI host
  updated: 2026-09-25T14:45:41+02:00
  budget:
    turns: 232   # --since 2026-09-24T10:59:18.694Z
    total_tokens: 31500000
    subagent_tokens: 47951
    spawns: 1   # infrastructure-engineer review
    status: ok
    checked: 2026-09-24T23:04:19+02:00
---

## H1 + QA record — 2026-09-24 (PR [#10](https://github.com/erfeamor/cv-domain-service/pull/10) @ `f54866b`)

**H1 (human-approved):**
- Bound: 20-minute pipeline timeout. Jenkins history on this host: warm builds 44–97 s, slowest cold build (`~/.m2` empty) 488 s.
- The placeholder comment points at T-112.
- Both hang tests run.
- The driver implements inline; one reviewer spawn.

**Review round 1:** no blocking findings.
- **Applied:** `junit` gets `allowEmptyResults: true`, so a timeout before Surefire has written a report stays ABORTED.
- **Noted in the PR:** the 488 s cold build probably had a warm Docker cache; a freshly replaced host would also cold-pull both base images.
- **Checked:** with BuildKit, a killed `docker build` cancels on the daemon side and leaves no orphan behind.

| AC | Evidence | Result |
|---|---|---|
| Fails on timeout; bound justified in the PR | Scratch `chore/t111-hang-guard` (Test stage `sleep 3600`, real bound). Console: `Timeout set to expire in 20 min` → `Cancelling nested steps due to timeout` → `Timeout has been exceeded` → `Finished: ABORTED`. Duration 1207 s. `junit` printed *No test report files were found* and the result **stayed ABORTED** (the review fix working) | ✅ |
| Normal build well inside the bound | PR-10 build 1: **71 s** (141 tests), 6% of the bound. The 488 s historical cold build is 41% | ✅ |
| Guard demonstrated firing | as above | ✅ |
| `branch 'master'` | diff. PR-10 console: `Stage "Deploy" skipped due to when conditional`. The PR states that a PR build cannot prove the gate; the post-merge master build will run it | ✅ |
| Placeholder accurate | now says the ECR push and the roll are T-112's | ✅ |
| Deploy still a no-op | body is the comment plus `echo` | ✅ |
| PR states the limitation | § Verification | ✅ |
| Executor released → reaper stops the host | `busyExecutors: 0` after the builds. Reaper at 22:04:15Z: `stopped i-073e5284ca2a1ceed after 20 idle minutes` | ✅ |

**Also confirmed:** `Timeout set to expire` is logged **before** `Declarative: Tool Install`, so JDK and Maven provisioning is inside the bound (review point 1).

**T-019's open AC is settled.** Scratch `chore/t111-hang-t019` used a 35-minute bound and a quiet sleep. Once the CPU window cleared, three consecutive reaper checks (21:49, 21:54, 21:59) logged `cpu quiet: peak 4.7–5.0%` and then **`busy: 1 executor(s) running`**, and declined to stop. The build ran on until its own bound. Recorded in T-019.

**Host time:** woken by the PR push at about 21:00:30Z and stopped at 22:04:17Z, so **~64 min**, about $0.05.

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
- **(from T-110)** Correct the `Deploy` stage's branch condition to `master` (`Jenkinsfile:45` on `origin/master` `1b9b398`, re-verified 2026-09-23; T-110 cited `:43-52`).
- **(from T-110)** Resolve the placeholder comment at `Jenkinsfile:48-49` (*"Placeholder until cv-infra exposes a deploy target"*) — the ECR repo it waits for exists (`cv-infra/registry.tf:5`). Either describe the **actual** state (target exists; what is missing is the push and the roll, owned by [T-112](T-112-domain-service-ci-ecr-deploy.md)) or delete it. **Decide at H1** — T-153's ruling applies: *a comment that is merely less wrong is not obviously better than none.*
- **(from T-110)** The `Deploy` stage must still do nothing at runtime. **Do not implement the deploy** — that is T-112.

**Out of scope:** ~~the dead `branch 'main'` Deploy gate and its stale placeholder comment — that is **[T-110](T-110-domain-service-jenkins-deploy-dead-gate.md)**.~~ *(in scope since 2026-09-23 — T-110 absorbed, see above.)* Also out of scope: making the `Docker image` stage actually push ~~, which no board task owns (recorded in T-110)~~ — owned by **[T-112](T-112-domain-service-ci-ecr-deploy.md)** since 2026-08-27, which now depends on this task.

## Acceptance criteria

- [x] The pipeline fails on timeout rather than hanging, with the bound and its justification recorded in the PR.
- [x] A normal build still passes comfortably inside the bound — verified against **real build durations on this host**, cold `~/.m2` included, not an estimate.
- [x] **Demonstrate the guard actually fires.** T-154's sharpest criterion and it applies here unchanged: a timeout nobody has watched trigger is the unverified-claim class this board keeps cataloguing. Force a hang on a scratch branch and show the build failing at the bound.
- [x] **(from T-110)** `when { branch 'master' }`, matching the actual protected mainline.
- [x] **(from T-110)** The placeholder comment either describes the current state accurately or is gone — no surviving claim that cv-infra has yet to expose a deploy target.
- [x] **(from T-110)** The `Deploy` stage still does nothing at runtime — this task must not turn a placeholder into a deploy.
- [x] **(from T-110)** The PR states plainly that a green PR build **does not** exercise the `branch 'master'` condition (PR builds are not `master`); the evidence for the gate is the diff plus the workspace-wide fact that `master` is the mainline.
- [x] Confirm the executor is released afterwards and the reaper subsequently stops the box — the entire argument is cost, so a guard that fires but leaves the host up has not delivered.

## Watch-outs

- **(from T-110)** **Verification of the gate is genuinely weak and should be stated, not dressed up.** Nothing available on a PR build exercises a `branch 'master'` condition. Do not claim a green PR build verified it — this board has a standing problem with green signals that measured the wrong thing ([T-107](T-107-post-id-cross-person-write.md)'s mock-measuring test, [T-028](T-028-qa-env-generator-worktree-build-context.md)'s master-building QA stack).
- **Verifying this means deliberately hanging a build on the shared host, which blocks the other repo too** (`numExecutors: 1`). Do it on a scratch branch, keep the test bound short, and confirm the box is released afterwards.
- **This interacts with [T-019](T-019-ci-host-on-demand.md)'s one untested acceptance criterion** — *"a build in progress is never killed"*, whose second half has never been exercised (reconciled 2026-08-27). Whoever runs this task is already starting builds and watching the reaper, so it is the cheapest opportunity on the board to settle T-019's criterion too. **Not a dependency in either direction** — recorded so the chance is not missed, the way [T-002](T-002-jenkins-on-drone-host.md)→[T-005](T-005-ci-secret-blast-radius.md)'s hand-off sat unowned for eleven days.
- ~~**[T-026](T-026-first-build-after-cold-start-fails.md) applies** — the first build after idle may fail spuriously.~~ **Fixed 2026-08-26** (cv-infra `1deebb4`, [#21](https://github.com/erfeamor/cv-infra/pull/21)). The first build after idle is now trustworthy. Struck rather than deleted because sibling tasks still carry the live version of this warning.
- **Read the statuses API, not `gh pr checks`**, which reports `pass` while a failed build sits in the history behind it.

## Definition of done

PR open against `master` from `fix/jenkins-pipeline-hygiene`, the guard demonstrated firing, task updated.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2 — `cv-domain-service` is its layer). **Reviewers:** `/code-review` + `infrastructure-engineer` (owns all CI config) + `/security-review` (forced by the `Jenkinsfile` path).
- **DECIDED 2026-09-23 — option (a), by the human; this task is the anchor.** [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md) is closed as absorbed; its items are in Scope, Acceptance criteria and Watch-outs above, marked *(from T-110)*. This task's *"demonstrate the guard actually fires"* is kept intact, as the note below required. The note is kept as the reasoning.
- **Bundle with [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md)** — same file, same repo, same forced reviewer set, exactly the T-153/T-154 situation. **H1 decides**; T-153's recommended option (a) — one task absorbs the other and the absorbed one closes recording where its criteria went — applies here unchanged. If bundled, **this task's "demonstrate the guard actually fires" must survive the merge**; it is the sharper of the two tasks' criteria.

## Provenance

Found 2026-08-27 while answering *"what should be the next tasks?"* against the board. [T-154](T-154-jenkins-pipeline-timeout.md) carries *"cv-domain-service's pipeline checked for the same gap, and the finding recorded either way"* as an explicit acceptance criterion, and [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) repeats the instruction. That check has now been run ahead of both: **the gap is present**, and the two findings above — the different hang mechanism, and the single shared executor with an observed queue — are new to the board rather than a restatement of T-154. Filed rather than left to be rediscovered, so T-154's criterion can be closed by reference.
