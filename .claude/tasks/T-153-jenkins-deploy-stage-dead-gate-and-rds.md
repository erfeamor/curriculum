---
id: T-153
title: "cv-database Jenkinsfile hygiene: the Deploy stage is gated on a branch that does not exist and still targets RDS; the pipeline has no timeout and no MySQL health wait; the repo's docs never name MySQL 8.4 (absorbs T-154, T-017)"
repo: cv-database
status: done
owner: tech-product-owner
branch: fix/jenkins-pipeline-hygiene   # renamed 2026-09-23 from fix/jenkins-deploy-stage-gate when T-154 was absorbed — the branch now carries all four items; never pushed under the old name
pr: https://github.com/erfeamor/cv-database/pull/5
depends_on: [T-152]   # FILE-LEVEL, not scheduling: both tasks edit cv-database/Jenkinsfile. T-152 changes the image pin at line 18, this task changes the Deploy stage below it. Sequenced to keep the diffs reviewable and conflict-free, not because this task needs 8.4.
risk: normal   # raised 2026-09-23 from low: absorbing T-154 brings its `normal` and its deliberate hang on the shared single-executor CI host
security_review: true   # adapter §5 — `Jenkinsfile` is an unconditional /security-review path, regardless of how small the diff is
checkpoint:
  stage: done   # merged 80b6665 (squash of cv-database#5), 2026-09-24 — H2 accepted by the human
  repo: cv-database
  branch: fix/jenkins-pipeline-hygiene
  worktree: none   # removed after merge
  pr: https://github.com/erfeamor/cv-database/pull/5
  commit: 80b6665   # squash merge on master (branch head was 2b725f4)
  developer: backend-developer
  reviewers: [code-review, infrastructure-engineer, security-review]
  risk: normal
  security_review: true   # adapter §5: Jenkinsfile
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: none   # verification is Jenkins on the CI host, not a compose stack
  updated: 2026-09-24T14:43:29+02:00   # earlier checkpoint times in this block were estimates ahead of the clock; this one is real
  budget:
    turns: 95   # --since 2026-09-24T10:59:18.694Z
    total_tokens: 7900000
    subagent_tokens: 121512
    spawns: 3   # QA plan, backend-developer, infrastructure-engineer (cap reached — developer resumed via SendMessage)
    status: ok
    checked: 2026-09-24T13:46:07+02:00
---

## ✅ H1 — 2026-09-24, approved by the human

| Decision | Choice |
|---|---|
| Deploy-stage comment | **Neutral placeholder** that names no architecture, so it cannot go stale: not implemented; credentials and blast radius are open (T-005); read the board before implementing |
| Timeout | **`options { timeout(time: 10, unit: 'MINUTES') }` on the whole pipeline**, about 6× a normal 90–100 s build, leaving room for cold image pulls (Flyway 13's included, once T-156 lands). The MySQL health wait has its **own 120 s bound** inside it, so "never healthy" fails fast and distinctly |
| T-156 | **Separate PR right after**, in the same CI-host session: one task per branch, and this task's evidence is not mixed with a first pull of the new image |
| Plan | Developer `backend-developer`; reviewers `/code-review` + `infrastructure-engineer` + `/security-review`; the forced 10-min hang on a scratch branch and the reaper stop are both included |

### Stage-0 QA plan (quality-assurance, run at stage 4)

**Reach.**
- Jenkins sits behind the CI host's EIP.
- Admin password: SSM `/<project>/<env>/ci/jenkins-admin-password`, user `erfeamor`.
- Console: `$JENKINS/job/cv-database/job/<branch>/<n>/consoleText`.
- Status: `gh api repos/erfeamor/cv-database/commits/<sha>/statuses`, never `gh pr checks`.
- Reaper logs: `/aws/lambda/<project>-ci-reaper`.

**Order: one wake.** Push the PR branch, then immediately push the scratch branch `chore/t153-hang-verify`, so both builds queue on the single executor.

1. `branch 'master'` in the diff; `main` is gone.
2. `git grep -niw rds` leaves only `CLAUDE.md:70` (contrastive).
3. The Deploy stage is still `echo` only.
4. + 6. On the scratch branch, `FLYWAY_URL` points at an unreachable host (`10.255.255.1`). The console shows the build aborted **by the timeout at the bound**: diff the timestamps, and read the timeout line itself. Keep the full console as evidence.
5. The PR build's duration, recorded against the bound. FAIL if it comes within 20% of the bound.
7. The PR build console has **no** `Connection refused` / `Retrying` lines.
8. After the hang, `busyExecutors` drops to 0, the reaper logs the idle quorum and `StopInstances`, and the instance reads `stopped`. *Optional:* reaper checks that land during the hang log a busy executor and decline to stop, which is evidence for T-019's open AC.
10. The docs name MySQL 8.4 at `CLAUDE.md:3`, `CLAUDE.md:8` and `README.md:9`.
11. PR build green, and its console shows `Stage "Deploy" skipped due to when conditional`. The PR states that a PR build cannot prove the `master` gate.

**Never-healthy path.** It gets no scratch run. It is covered by review: the wait loop must have its own bound and a distinct failure message.

**Cleanup.** Delete the scratch branch (local and remote), confirm the host `stopped`, and record how long the host was up.

## Stage-4 QA record — 2026-09-24 (PR [#5](https://github.com/erfeamor/cv-database/pull/5) @ `2b725f4`)

One wake of the CI host: the push at 11:32:47Z started it at 11:32:50Z. Jenkins indexed both branches and ran the scratch branch first, so PR-5 queued behind the hang on the single executor. That turned out to be a useful test in its own right, below.

| # | Check | Evidence | Result |
|---|---|---|---|
| 1 | `branch 'master'` | diff | ✅ |
| 2 | No current-architecture RDS | `git grep -niw rds` → only `CLAUDE.md:70` (contrastive) | ✅ |
| 3 | Deploy still a no-op | the stage body is the comment plus `echo` | ✅ |
| 4, 6 | **Timeout fires** | Scratch `chore/t153-hang-verify` build 1 (`a510339`: unreachable `10.255.255.1`, retries 60). The console shows `Timeout set to expire in 10 min`, Flyway retrying 1…120 s, then `Cancelling nested steps due to timeout`, `After 20s process did not stop`, `Timeout has been exceeded`, `Finished: ABORTED`. Duration 632 s | ✅ |
| — | **Review finding 1 confirmed real** | In the same console, the post cleanup's `docker rm -f cv-flyway-ci-1` printed the name, so **the Flyway container outlived the abort**, and `docker network rm cv-db-ci-1` then succeeded. Without `2b725f4` both would have leaked | ✅ fixed |
| 5 | Normal build well inside the bound | PR-5 build 1 ran for **~24 s**: status `being built` 11:44:51Z → `success` 11:45:15Z. Jenkins' 652 s `duration` includes 10 min queued behind the hang | ✅ (~4% of the bound) |
| — | Queue time doesn't count against the bound | `Timeout set to expire` appears after `Running on`, so the timeout wraps the pipeline inside `node`. PR-5 waited 10 min and was **not** aborted | ✅ |
| 7 | Flyway only after healthy | PR-5 console: 8 health polls, `MySQL healthy; running Flyway`, **0** `Retrying` / `Connection refused` lines (T-154's evidence had 4 rounds) | ✅ |
| 11 | Jenkins green, limitation stated | statuses API `success` on `2b725f4`. Console: `Stage "Deploy" skipped due to when conditional`. The PR says a PR build cannot prove the `master` gate | ✅ |
| 8 | Executor released → reaper stops the host | `busyExecutors: 0`, queue empty right after. Reaper at 12:09:15Z: `cpu quiet: peak 5.8% over 20 min across 4 datapoints`, then `stopped i-073e5284ca2a1ceed after 20 idle minutes`; instance `stopped` 12:09:17Z. **Host up 36.5 min** (11:32:50 → 12:09:17), ≈ $0.03 | ✅ |
| 10 | MySQL 8.4 in the docs | `CLAUDE.md:3`, `:8`, `:42`; `README.md:9` | ✅ |

**T-019's open AC ("a build in progress is never killed"): observed, but not settled.** The reaper checks that landed during the hang declined to stop the host at 11:34 (`busy: 2 item(s) queued`), 11:39 and 11:44 (`busy: CPU peaked at 36.6% over 20 min`). So the build survived, but the **CPU veto** decided it, not the `busyExecutors` read that the criterion is about. A clean test needs a hang long enough to outlast the 20-minute CPU window. Recorded for T-019; not claimed here.

The PR-5 flow also still prints Flyway 10's *"upgrade recommended"* warning, as expected; T-156 removes it.

## Goal

`cv-database/Jenkinsfile`'s `Deploy` stage carries two stale facts. Neither breaks a build today, which is exactly why they have survived.

```groovy
stage('Deploy') {
    when {
        branch 'main'          // <-- the mainline in every repo in this workspace is `master`
    }
    steps {
        // Placeholder: run Flyway against RDS with credentials from
        // SSM Parameter Store once the dev environment exists.
        echo 'Deploy stage not yet implemented'
    }
}
```

1. **The gate can never match.** `master` is the protected mainline in all nine repos (meta `CLAUDE.md`, board `README.md` rule 2). `when { branch 'main' }` means this stage has never run and never will. It is currently harmless because the body is an `echo` — it stops being harmless the moment someone implements the body and cannot work out why deploys never fire.
2. **The comment describes an architecture that was dismantled.** MySQL left RDS for a self-hosted 8.4 container on the domain-service EC2 (cv-infra PR #8); `cv-infra/templates/domain-service-user-data.sh:164` is the current truth. The comment also defers to "once the dev environment exists" — it exists, and has since before [T-001](T-001-selfhost-mysql-followups.md) put nightly backups on it.

## Bundle with T-154 — one Jenkinsfile PR, not two (2026-08-24, on the human's instruction)

> **DECIDED 2026-09-23 — option (a), by the human; this task is the anchor.** [T-154](T-154-jenkins-pipeline-timeout.md) is closed as absorbed. Its four contributions are now in this task's Scope, Acceptance criteria, Watch-outs and Definition of done below, each marked *(from T-154)*. Re-verified on `cv-database` `origin/master` (`865784f`) the same day: no `timeout`/`options` block, Flyway runs straight after `docker run -d` with `FLYWAY_CONNECT_RETRIES=60`, `branch 'main'` at `Jenkinsfile:42`, RDS comment at `:45`. The note below is kept as the reasoning.

**[T-154](T-154-jenkins-pipeline-timeout.md) edits the same file in the same repo with the same forced reviewer set.** Both are `cv-database/Jenkinsfile`; both carry `security_review: true` because adapter §5 makes a `Jenkinsfile` diff an unconditional `/security-review` path. Run separately they cost **two branches, two PRs, two `/security-review` rounds and two H1/H2 gate pairs** — and the second one merges into a file the first just changed.

**Recommendation: one "Jenkinsfile hygiene" PR covering all of it:**

| Item | From | What |
|---|---|---|
| `when { branch 'master' }` | this task | the gate that can never match |
| the RDS placeholder comment | this task | describes an architecture that was dismantled |
| `timeout {}` | [T-154](T-154-jenkins-pipeline-timeout.md) | a hung build holds the only CI host up |
| wait for MySQL healthy before Flyway | [T-154](T-154-jenkins-pipeline-timeout.md) | its console evidence shows the retry budget is the de-facto sync mechanism on **every** build |

**Why it is more than convenience:** T-154's healthcheck fix and this task's `Deploy`-stage edit are a few lines apart in one file, and a reviewer looking at the whole pipeline at once can see things neither PR shows alone — `post { always }` swallowing cleanup failures with `|| true`, and images pulled by mutable tag, both raised as NOTEs in [T-152](T-152-mysql-84-parity-cv-database.md)'s security review and both still open. **That does not mean fix them here** (board rule 3), but one review pass over the whole file is a better place to decide than two partial ones.

**The tension, named:** board rule 2 says *"one branch per task"*. **H1 picks the resolution; this note does not:**
- **(a) One task absorbs the other**, with a widened scope and merged acceptance criteria, and the absorbed task closes recording where its criteria went. Rule 2 intact. **Recommended** — and if taken, this task is the natural anchor since it is already sequenced behind T-152 for exactly this file-collision reason.
- **(b) Both tasks stay, one PR references both**, accepting the rule-2 deviation deliberately and recording it.

**Do not lose T-154's acceptance criteria in the merge.** Its *"demonstrate the guard actually fires"* is the sharpest check either task has — a timeout nobody has watched trigger is the unverified-claim class this board keeps cataloguing — and its *"check `cv-domain-service`'s pipeline for the same gap"* is a separate-repo finding that must still be filed, not fixed.

> **DECIDED 2026-09-23 — absorbed, by the human.** [T-017](T-017-docs-drift-rds-to-selfhosted.md) is closed; its surviving work is in this task's Scope and Acceptance criteria, marked *(from T-017)*.

**[T-017](T-017-docs-drift-rds-to-selfhosted.md)'s `cv-database` half can ride the same PR** (`CLAUDE.md:3`, `README.md:9` — naming MySQL 8.4 as the target engine). Different files, same repo, and its meta-repo half is already satisfied, so this would **close T-017 entirely**. It also sits naturally with this task's own RDS-comment fix: both are the same drift, one in a pipeline file and one in prose.

## The same dead gate exists in `cv-domain-service` — filed 2026-08-27 as [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md)

`cv-domain-service/Jenkinsfile:43-52` carries an identical `when { branch 'main' }` on its own `Deploy` stage, on a repo whose `origin` likewise holds only `master`. **Checked and filed ahead of this task; do not fix it here** (board rule 3 — different repo).

It is not a pure duplicate: that repo's placeholder comment reads *"Placeholder until cv-infra exposes a deploy target"*, and `cv-infra/registry.tf:5` defines `aws_ecr_repository.domain_service` — so its stale premise is a **target that now exists**, where this task's is an architecture that was **dismantled**. Same class of drift, opposite direction. T-110 also records a gap neither task owns: **nothing on the board owns implementing the cv-domain-service deploy** ([T-203](T-203-bff-ci-deploy-stage.md) covers `cv-bff-node` only).

## Scope

- Correct the branch condition to `master`.
- Rewrite the placeholder comment to describe the **actual** deploy target (self-hosted MySQL 8.4 on the domain-service instance, credentials from SSM Parameter Store), or delete the comment if the stage is better left undescribed until someone implements it. **Decide this at H1** — a comment that is merely less wrong is not obviously better than none.
- **Do not implement the deploy.** That is a separate, larger task with real credential and blast-radius questions ([T-005](T-005-ci-secret-blast-radius.md) is directly relevant). This task makes the stage honest, nothing more.

- **(from T-154)** Wrap the pipeline (or at minimum the `Validate migrations` stage) in `timeout(time: N, unit: 'MINUTES')`. Pick N from observed build times — successful builds run ~90–100s. **Justify the number rather than copying one.** The reaper is **not** a mitigation (T-154 § *cost premise CONFIRMED*): a hung low-CPU build passes its CPU veto and is then held up by `busyExecutors` indefinitely, so the timeout is the only bound.
- **(from T-154)** **Wait for the MySQL container to report healthy before invoking Flyway**, so the retry backoff stops being the pipeline's synchronisation mechanism. T-154 § *The retry loop is NOT latent* has the console evidence: four `Connection refused … Retrying` rounds on a perfectly healthy build.
- **(from T-017)** Name **MySQL 8.4** as the target engine in the repo's prose. Re-grepped on `origin/master` (`865784f`) 2026-09-23 — three lines, not the two T-017 named:
  - `CLAUDE.md:3` — *"MySQL 8 schema managed exclusively through Flyway 10…"*
  - `CLAUDE.md:8` — `docker compose up -d  # MySQL 8 on :3306` — **new 2026-09-23**: the compose file pins `mysql:8.4`, and line 15 of the same file already says so.
  - `README.md:9` — *"- MySQL 8"*
  - **Leave alone:** `CLAUDE.md:57`'s *"every MySQL 8 JDBC URL"* (a driver fact true across the 8.x family) and `CLAUDE.md:70`'s *"instead of RDS"* (contrastive — T-017's standard permits it).

**Out of scope:** the `mysql:8.0` → `8.4` pin four lines above, which is **[T-152](T-152-mysql-84-parity-cv-database.md)'s** — this task depends on it so the two diffs do not collide in one file. **Also out of scope (carried from T-154):** the `post { always }` cleanup swallowing failures via `|| true`, and images pulled by mutable tag — both NOTEs from T-152's security review, pre-existing, unrelated to hanging. The bundle note above argues a whole-file reviewer will *see* them; seeing is not fixing — file them if review wants them fixed.

## Acceptance criteria

- [x] `when { branch 'master' }`, matching the actual protected mainline.
- [x] No reference to RDS remains in the file, other than deliberately historical wording if any is kept ([T-017](T-017-docs-drift-rds-to-selfhosted.md)'s standard: prose explaining *why* RDS was dropped may keep the word; prose describing current architecture may not).
- [x] The stage still does nothing at runtime — this task must not turn a placeholder into a deploy.
- [x] **(from T-154)** The pipeline fails on timeout rather than hanging, with the bound and its justification recorded in the PR.
- [x] **(from T-154)** A normal build still passes comfortably inside the bound — verified against real build durations, not an estimate.
- [x] **(from T-154)** **Demonstrate the guard actually fires.** Force a hang on a scratch branch (e.g. point `FLYWAY_URL` at an unreachable host) and show the build failing at the bound. A timeout nobody has watched trigger is the unverified-claim class this board keeps cataloguing — **the sharpest check in either task; do not let it thin out in the merge.**
- [x] **(from T-154)** Flyway starts only after MySQL reports healthy: the console of a healthy build shows **no** `Connection refused … Retrying` rounds.
- [x] **(from T-154)** After the forced hang, the executor is released and the reaper subsequently stops the CI host — the argument is cost, so a guard that fires but leaves the host up has not delivered.
- [x] **(from T-154)** `cv-domain-service`'s pipeline checked for the same gap — done 2026-08-27, filed as [T-111](T-111-domain-service-jenkins-pipeline-timeout.md). Do not re-run it and do not fix it here.
- [x] **(from T-017)** MySQL **8.4** is named as the target engine in `cv-database`'s docs (`CLAUDE.md:3`, `CLAUDE.md:8`, `README.md:9`).
- [x] **(from T-017)** `git grep -niw rds` across `cv-database` returns nothing that describes current architecture — after this PR only `CLAUDE.md:70`'s contrastive line should remain.
- [x] Jenkins goes green on the branch. **Note the stage will still not execute on a PR build** (PR builds are not `master`), so a green build does not prove the new condition works; state that limitation in the PR rather than implying it was verified.

## Watch-outs

- **(from T-154)** Verifying the timeout means *deliberately hanging a build on the shared host* — and `numExecutors: 1` (`cv-infra/templates/jenkins-provision.sh:63`) means a hang here also queues every `cv-domain-service` build. Do it on a scratch branch, keep the test bound short, and confirm the box is released afterwards.
- **Verification is genuinely weak here and should be stated, not dressed up.** Nothing available on a PR build exercises a `branch 'master'` condition. The honest evidence is the diff plus the workspace-wide fact that `master` is the mainline. Do not claim a green PR build verified the gate — this board has a standing problem with green signals that measured the wrong thing ([T-107](T-107-post-id-cross-person-write.md)'s mock-measuring test, [T-028](T-028-qa-env-generator-worktree-build-context.md)'s master-building QA stack).
- ~~**[T-026](T-026-first-build-after-cold-start-fails.md) applies** — `cv-database` is wired to the on-demand CI host, so the first build after idle may fail spuriously with an empty stage. Re-run on the warm box before debugging.~~ **FIXED 2026-08-26** (cv-infra `1deebb4`, [#21](https://github.com/erfeamor/cv-infra/pull/21)) — the first build after idle is now trustworthy, and a red one means what it says. Struck rather than deleted per strike-don't-delete. **The `gh pr checks` half of this warning still stands and is unrelated to T-026**: it reports only the latest status per context, so read `gh api repos/:owner/:repo/commits/:sha/statuses` or a failed build stays invisible behind a later green one.

## Definition of done

PR open against `master` from `fix/jenkins-pipeline-hygiene`, the timeout guard demonstrated firing *(from T-154)*, task updated to `in_review` with the PR URL.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2 — `cv-database` is its layer). **Reviewers:** `/code-review` + `infrastructure-engineer` (owns all CI config) + `/security-review` (adapter §5, forced by the `Jenkinsfile` path).
- ~~`risk: low` and it is genuinely small~~ **`risk: normal` since 2026-09-23** (T-154 absorbed: a deliberate hang on the shared CI host is not small). It does **not** take the trivial fast-path: adapter §5's fast-path covers "isolated non-security config", and a CI pipeline file is neither.

## Provenance

Found 2026-08-22 during T-152's stage-0 refinement, while reading the Jenkinsfile to confirm that its throwaway MySQL container is `--rm`'d (it is — which is why T-152's AC3 had to change). Filed rather than fixed inside T-152 per board rule 3, and filed rather than folded into [T-017](T-017-docs-drift-rds-to-selfhosted.md) because T-017 is a docs task and this is a pipeline file with a live, if inert, logic error. Ratified at T-152's H1 gate, 2026-08-22.


## Confirmed from the console — the stage is skipped, in as many words (2026-08-22)

`cv-database` PR-4 build #2, a fully green run on the merged 8.4 gate:

```
[Pipeline] stage
[Pipeline] { (Deploy)
Stage "Deploy" skipped due to when conditional
```

The `when { branch 'main' }` gate evaluates false and the stage is skipped, on a repo whose default branch is `master`. This task previously argued the gate was dead **by reading the Jenkinsfile**; it is now observed being dead in a real run, with Jenkins naming the reason itself.

**Note the contrast with build #1 of the same PR**, which reports the same stage skipped for an entirely different reason:

```
Stage "Deploy" skipped due to earlier failure(s)
```

Two different skip reasons for a stage that has never once executed. Worth recording because it is a small trap for whoever fixes this: *"Deploy was skipped"* in a log is not evidence about the branch gate unless you read **which** skip it was — and ~~[T-026](T-026-first-build-after-cold-start-fails.md) means roughly one build in two on a cold start shows the misleading variant~~ **(T-026 fixed 2026-08-26, so cold starts no longer manufacture the `earlier failure(s)` variant; the trap survives for any build that fails for an unrelated reason, which is why the distinction still matters)**.
