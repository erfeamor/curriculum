---
id: T-110
title: "cv-domain-service's Deploy stage is gated on a branch that does not exist, and its placeholder describes a target that now exists"
repo: cv-domain-service
status: todo
owner:
branch: fix/jenkins-deploy-stage-gate
pr:
depends_on: []
risk: low
security_review: true   # adapter §5 — `Jenkinsfile` is an unconditional /security-review path, regardless of how small the diff is
---

## Goal

`cv-domain-service/Jenkinsfile:43-52` carries the **same dead gate** as [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md)'s, in a different repo, plus a placeholder comment whose premise has since been falsified:

```groovy
stage('Deploy') {
    when {
        branch 'main'          // <-- the mainline in every repo in this workspace is `master`
    }
    steps {
        // Placeholder until cv-infra exposes a deploy target:
        // push the image to ECR and roll the EC2 service via SSM.
        echo 'Deploy stage not yet implemented'
    }
}
```

1. **The gate can never match.** `master` is the protected mainline in all nine repos (meta `CLAUDE.md`, board `README.md` rule 2). `origin` in this repo holds `master` and nothing else — confirmed 2026-08-27. `when { branch 'main' }` means this stage has never run and never will. Harmless while the body is an `echo`; it stops being harmless the moment someone implements the body and cannot work out why deploys never fire.
2. **"Until cv-infra exposes a deploy target" is no longer true.** `cv-infra/registry.tf:5` defines `aws_ecr_repository.domain_service`, and the live account returns it as an output (`domain_service_ecr_repository_url = 760904708057.dkr.ecr.eu-west-3.amazonaws.com/cv-project-domain-service`, read 2026-08-26). The target the comment waits for has existed for some time. This is the same class of drift as T-153's RDS comment — a stale premise in a pipeline file rather than in prose — with different content.

**A third fact, recorded but deliberately NOT in scope:** the `Docker image` stage (`Jenkinsfile:37-41`) runs `docker build -t $IMAGE_NAME:$GIT_COMMIT .` and **never pushes**, so every build produces an image that is discarded. That is the missing half of the deploy, not of this task.

## What this task is NOT

**Do not implement the deploy.** Same ruling as [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md): that is a separate, larger task with real credential and blast-radius questions ([T-005](T-005-ci-secret-blast-radius.md) is directly relevant, and [T-203](T-203-bff-ci-deploy-stage.md) is the shape it would take for the BFF). This task makes the stage honest, nothing more.

> ~~**Nothing on the board currently owns the cv-domain-service deploy.**~~ **NOW OWNED — filed 2026-08-27 as [T-112](T-112-domain-service-ci-ecr-deploy.md)**, on the human's instruction, immediately after this pointer was written. The gap was real: searched 2026-08-27, the only files mentioning the deploy were [T-002](T-002-jenkins-on-drone-host.md) (which built the pipeline) and T-153 (the sibling repo), and [T-203](T-203-bff-ci-deploy-stage.md) covers `cv-bff-node` only — deliberately, in terms. **T-112 `depends_on` this task**, because implementing the deploy into a stage still gated on `main` would ship something that can never run.

## Scope

- Correct the branch condition to `master`.
- Resolve the placeholder comment: either rewrite it to describe the **actual** state (ECR repo exists; what is missing is the push and the roll), or delete it. **Decide at H1** — T-153's ruling applies verbatim: *a comment that is merely less wrong is not obviously better than none.*
- The stage must still do nothing at runtime.

**Out of scope:** the missing `timeout {}` — that is **[T-111](T-111-domain-service-jenkins-pipeline-timeout.md)**, this repo's sibling of T-154. See the bundling note below; the two files are adjacent and H1 should price them together exactly as T-153/T-154 were.

## Acceptance criteria

- [ ] `when { branch 'master' }`, matching the actual protected mainline.
- [ ] The placeholder comment either describes the current state accurately or is gone — no surviving claim that cv-infra has yet to expose a deploy target.
- [ ] The stage still does nothing at runtime — this task must not turn a placeholder into a deploy.
- [ ] Jenkins goes green on the branch. **Note the stage will still not execute on a PR build** (PR builds are not `master`), so a green build does not prove the new condition works; state that limitation in the PR rather than implying it was verified.

## Watch-outs

- **Verification is genuinely weak here and should be stated, not dressed up.** Nothing available on a PR build exercises a `branch 'master'` condition. The honest evidence is the diff plus the workspace-wide fact that `master` is the mainline. Do not claim a green PR build verified the gate — this board has a standing problem with green signals that measured the wrong thing ([T-107](T-107-post-id-cross-person-write.md)'s mock-measuring test, [T-028](T-028-qa-env-generator-worktree-build-context.md)'s master-building QA stack).
- **Read the statuses API, not `gh pr checks`**, which reports `pass` while a failed build sits in the history behind it.
- ~~**[T-026](T-026-first-build-after-cold-start-fails.md) applies** — the first build after idle may fail spuriously.~~ **No longer true as of 2026-08-26**: T-026 is FIXED and merged (cv-infra `1deebb4`, [#21](https://github.com/erfeamor/cv-infra/pull/21)), and the fix was verified by exactly this shape — a cold-start push to a branch with an existing `builds/1`, green. The first build after idle is now trustworthy. Kept struck rather than deleted because every sibling task still carries the live version of this warning.

## Definition of done

PR open against `master` from `fix/jenkins-deploy-stage-gate`, task updated to `in_review` with the PR URL.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2 — `cv-domain-service` is its layer). **Reviewers:** `/code-review` + `infrastructure-engineer` (owns all CI config) + `/security-review` (adapter §5, forced by the `Jenkinsfile` path).
- `risk: low` and it is genuinely small, but it does **not** take the trivial fast-path: adapter §5's fast-path covers "isolated non-security config", and a CI pipeline file is neither.
- **Bundle with [T-111](T-111-domain-service-jenkins-pipeline-timeout.md), for the same reason T-153/T-154 were bundled.** Same file, same repo, same forced `/security-review`; run separately they cost two branches, two PRs, two security reviews and two gate pairs on one file. **H1 decides**, and T-153's option (a) — one task absorbs the other, the absorbed one closing with a record of where its criteria went — is the recommended resolution there and applies here unchanged.

## Provenance

Found 2026-08-27 while answering *"what should be the next tasks?"* against the board. Both [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) and [T-154](T-154-jenkins-pipeline-timeout.md) instruct their implementer to **check `cv-domain-service` for the same gap and file it, never fix it there** (board rule 3) — T-154 carries it as an explicit acceptance criterion. That check has now been run ahead of either task: **both defects are present in this repo**, verified by reading the file and by confirming `origin` holds no `main` branch. Filed rather than left for T-153/T-154 to rediscover, so that criterion can be closed by reference instead of by repeating the work.
