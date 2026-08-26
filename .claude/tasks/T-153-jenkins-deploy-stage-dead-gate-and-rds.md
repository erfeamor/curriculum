---
id: T-153
title: "cv-database's Deploy stage is gated on a branch that does not exist, and still targets RDS"
repo: cv-database
status: todo
owner:
branch: fix/jenkins-deploy-stage-gate
pr:
depends_on: [T-152]   # FILE-LEVEL, not scheduling: both tasks edit cv-database/Jenkinsfile. T-152 changes the image pin at line 18, this task changes the Deploy stage below it. Sequenced to keep the diffs reviewable and conflict-free, not because this task needs 8.4.
risk: low
security_review: true   # adapter §5 — `Jenkinsfile` is an unconditional /security-review path, regardless of how small the diff is
---

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

**[T-017](T-017-docs-drift-rds-to-selfhosted.md)'s `cv-database` half can ride the same PR** (`CLAUDE.md:3`, `README.md:9` — naming MySQL 8.4 as the target engine). Different files, same repo, and its meta-repo half is already satisfied, so this would **close T-017 entirely**. It also sits naturally with this task's own RDS-comment fix: both are the same drift, one in a pipeline file and one in prose.

## The same dead gate exists in `cv-domain-service` — filed 2026-08-27 as [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md)

`cv-domain-service/Jenkinsfile:43-52` carries an identical `when { branch 'main' }` on its own `Deploy` stage, on a repo whose `origin` likewise holds only `master`. **Checked and filed ahead of this task; do not fix it here** (board rule 3 — different repo).

It is not a pure duplicate: that repo's placeholder comment reads *"Placeholder until cv-infra exposes a deploy target"*, and `cv-infra/registry.tf:5` defines `aws_ecr_repository.domain_service` — so its stale premise is a **target that now exists**, where this task's is an architecture that was **dismantled**. Same class of drift, opposite direction. T-110 also records a gap neither task owns: **nothing on the board owns implementing the cv-domain-service deploy** ([T-203](T-203-bff-ci-deploy-stage.md) covers `cv-bff-node` only).

## Scope

- Correct the branch condition to `master`.
- Rewrite the placeholder comment to describe the **actual** deploy target (self-hosted MySQL 8.4 on the domain-service instance, credentials from SSM Parameter Store), or delete the comment if the stage is better left undescribed until someone implements it. **Decide this at H1** — a comment that is merely less wrong is not obviously better than none.
- **Do not implement the deploy.** That is a separate, larger task with real credential and blast-radius questions ([T-005](T-005-ci-secret-blast-radius.md) is directly relevant). This task makes the stage honest, nothing more.

**Out of scope:** the `mysql:8.0` → `8.4` pin four lines above, which is **[T-152](T-152-mysql-84-parity-cv-database.md)'s** — this task depends on it so the two diffs do not collide in one file.

## Acceptance criteria

- [ ] `when { branch 'master' }`, matching the actual protected mainline.
- [ ] No reference to RDS remains in the file, other than deliberately historical wording if any is kept ([T-017](T-017-docs-drift-rds-to-selfhosted.md)'s standard: prose explaining *why* RDS was dropped may keep the word; prose describing current architecture may not).
- [ ] The stage still does nothing at runtime — this task must not turn a placeholder into a deploy.
- [ ] Jenkins goes green on the branch. **Note the stage will still not execute on a PR build** (PR builds are not `master`), so a green build does not prove the new condition works; state that limitation in the PR rather than implying it was verified.

## Watch-outs

- **Verification is genuinely weak here and should be stated, not dressed up.** Nothing available on a PR build exercises a `branch 'master'` condition. The honest evidence is the diff plus the workspace-wide fact that `master` is the mainline. Do not claim a green PR build verified the gate — this board has a standing problem with green signals that measured the wrong thing ([T-107](T-107-post-id-cross-person-write.md)'s mock-measuring test, [T-028](T-028-qa-env-generator-worktree-build-context.md)'s master-building QA stack).
- ~~**[T-026](T-026-first-build-after-cold-start-fails.md) applies** — `cv-database` is wired to the on-demand CI host, so the first build after idle may fail spuriously with an empty stage. Re-run on the warm box before debugging.~~ **FIXED 2026-08-26** (cv-infra `1deebb4`, [#21](https://github.com/erfeamor/cv-infra/pull/21)) — the first build after idle is now trustworthy, and a red one means what it says. Struck rather than deleted per strike-don't-delete. **The `gh pr checks` half of this warning still stands and is unrelated to T-026**: it reports only the latest status per context, so read `gh api repos/:owner/:repo/commits/:sha/statuses` or a failed build stays invisible behind a later green one.

## Definition of done

PR open against `master` from `fix/jenkins-deploy-stage-gate`, task updated to `in_review` with the PR URL.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2 — `cv-database` is its layer). **Reviewers:** `/code-review` + `infrastructure-engineer` (owns all CI config) + `/security-review` (adapter §5, forced by the `Jenkinsfile` path).
- `risk: low` and it is genuinely small, but it does **not** take the trivial fast-path: adapter §5's fast-path covers "isolated non-security config", and a CI pipeline file is neither.

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
