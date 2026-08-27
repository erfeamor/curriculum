---
id: T-112
title: "cv-domain-service CI: push the image to ECR and roll the container on master"
repo: cv-domain-service
status: todo
owner:
branch: chore/ci-ecr-deploy-stage
pr:
depends_on: [T-110]   # SCHEDULING, not file-level: T-110 fixes `when { branch 'main' }`. Landing this first would implement a stage that can never run.
risk: normal
security_review: true   # adapter §5 — `Jenkinsfile` is an unconditional /security-review path, and this diff introduces registry credentials into CI
---

## Why this exists

`cv-domain-service/Jenkinsfile:37-52` builds an image and throws it away:

```groovy
stage('Docker image') {
    steps {
        sh 'docker build -t $IMAGE_NAME:$GIT_COMMIT .'   // built, never pushed
    }
}

stage('Deploy') {
    when { branch 'main' }                                // dead gate — T-110
    steps {
        // Placeholder until cv-infra exposes a deploy target:
        // push the image to ECR and roll the EC2 service via SSM.
        echo 'Deploy stage not yet implemented'
    }
}
```

**The deploy target it waits for already exists.** `cv-infra/registry.tf:5` defines `aws_ecr_repository.domain_service`, and `cv-infra/compute.tf:46` already points the instance at `${aws_ecr_repository.domain_service.repository_url}:latest`. What is missing is the push and the roll — nothing else.

**Today's deploy is manual and the user-data says so in terms.** `cv-infra/templates/domain-service-user-data.sh:188` reads *"The image is pushed manually/by CI after this instance first boots"*, and the boot path is `aws ecr get-login-password` → `until docker pull "${image}"; do … retry 60s` → `docker run -d --name domain-service`. So a new image reaches production **only when the instance reboots**, and only if someone pushed `:latest` by hand first. `README.md:273` records this as backlog: *"backend services still deployed manually."*

**Filed 2026-08-27 after being searched for and found unowned.** [T-203](T-203-bff-ci-deploy-stage.md) is the same task for `cv-bff-node` and says in terms: *"Closing this task for the BFF does not close it for `cv-domain-service`, which is still manual — do not widen this task to cover both repos."* It was correct to refuse, and nothing was filed on the other side of that sentence until now. Noted as a gap in [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md); this is that task.

## What makes this different from T-203 — do not copy its answers

T-203 is **GitHub Actions**; this is **Jenkins on our own EC2 host**. The credential question therefore has a different shape and a different set of traps:

- T-203 can prefer **GitHub OIDC → IAM role**. There is no equivalent here. The Jenkins container runs on an instance with an instance profile, so the tempting answer is "let the build use the host's instance profile".
- **That tempting answer collides head-on with [T-005](T-005-ci-secret-blast-radius.md)**, whose entire purpose is to **block IMDS from containers** on that host. Granting ECR-push and `ssm:SendCommand` to the instance profile and then reaching them from inside a build container is exactly the blast radius T-005 exists to close — and a build container on this host already has the **docker socket** mounted. **Read T-005 before choosing, decide explicitly, and write the reasoning into the PR.** Do not re-solve T-005 here, and do not quietly design something T-005 will have to undo.
- The CI host is **shared with `cv-database`** and runs Drone as well, so anything granted to it is granted to every pipeline on it.

## Scope

- Push the built image to `aws_ecr_repository.domain_service`, on `master` only, never on PRs.
- Roll the running container on the domain-service instance. **SSM `send-command` is the mechanism the account already supports** — there is no SSH anywhere in this estate. Scope the permission to that one instance ARN.
- **Decide the tag contract, and say why.** The build already produces `$IMAGE_NAME:$GIT_COMMIT`, but `compute.tf:46` pins `:latest`, which T-152's security review flagged as a mutable-tag NOTE. Options are to push both (immutable SHA for provenance, `:latest` for the boot path) or to move the instance off `:latest` — the second touches `cv-infra` and is a cross-repo change, so **price it at H1 rather than assuming it**.
- **Check the ECR lifecycle policy against the chosen tag scheme.** `registry.tf:16` keeps only the **two most recent images** because Free-Tier private ECR storage is 500 MB. A per-commit tag scheme churns that window fast; confirm the rollback story survives it.

**Out of scope:** the dead `branch 'main'` gate ([T-110](T-110-domain-service-jenkins-deploy-dead-gate.md)) and the missing `timeout {}` ([T-111](T-111-domain-service-jenkins-pipeline-timeout.md)). This task depends on T-110 precisely so it is not also fixing it.

## Acceptance criteria

- [ ] PR builds do **not** push or deploy — asserted by the pipeline's own `when` conditions, not by convention.
- [ ] A `master` build publishes an image to the domain-service ECR repository and the running container ends up on that image — **verified by request against the live service**, not by reading the pipeline.
- [ ] The IAM principal used can push to that one ECR repo and roll that one instance, and nothing else. The policy is in the PR (in `cv-infra` if Terraform-managed; if so, record the cross-repo ordering in the checkpoint).
- [ ] **The credential model is reconciled with [T-005](T-005-ci-secret-blast-radius.md) in writing** — either it survives IMDS being blocked from containers, or the PR states plainly what T-005 will have to change and why that is acceptable.
- [ ] No credential value in the repo.
- [ ] The tag contract is documented, and `cv-infra/compute.tf:46` still resolves to the image the pipeline pushed.
- [ ] `mvn -B checkstyle:check` and `mvn -B test` still gate the push — a failing test must block the deploy.

## Watch-outs

- **A rolled container is a live production change.** This is the first task that lets CI mutate the running domain service, so a bad build stops being a red X and starts being an outage. Consider whether the roll should verify `/actuator/health` (or the smoke path) and what happens if it does not come back — an unverified roll that silently leaves the service down is worse than a manual deploy.
- **[T-021](T-021-mysql-password-rotation-persistent-datadir.md) is adjacent**: the same user-data path fetches `db_password` and aborts the whole bootstrap under `set -e` if Flyway fails auth. A roll that re-runs that path inherits the trap.
- **Read the statuses API, not `gh pr checks`** — it reports only the latest status per context, so a failed build hides behind a later green one.

## Definition of done

PR open against `master` from `chore/ci-ecr-deploy-stage`, Jenkins green **including the new stage on the merge commit**, the roll verified against the live service, merged.

## dev-loop notes

- **Developer:** `infrastructure-engineer` — adapter §2 assigns **all CI config** to this persona, even though the file lives in a `backend-developer` repo. Same split T-203 makes. **Reviewers:** `/code-review` + `infrastructure-engineer` + `/security-review`.
- **`risk: normal` on the diff, but the *blast radius* is the highest of the three cv-domain-service CI tasks** — it is the one that grants CI the ability to change production. If H1 wants to raise it to `high`, that is a defensible call and the reviewer set widens accordingly.
- **Not on M2's critical path.** [T-501](T-501-e2e-cv-milestone.md) needs the services *deployed*, not *auto-deployed*, exactly as T-203 argues for the BFF. This is a hygiene and demo-quality task, not a milestone blocker — but the placeholder comment must not go on promising a stage that does not exist, which is what [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md) settles in the meantime.
- Gates (adapter §3): the `cv-domain-service` row — `mvn -q -B checkstyle:check`, `mvn -q -B test`, `mvn -q -B package -DskipTests`. Authoritative CI: **Jenkins**.

## Provenance

Filed 2026-08-27 on the human's instruction, after [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md) recorded the gap as a pointer rather than claiming it. The gap was found by searching the board for an owner of the cv-domain-service deploy and finding only [T-002](T-002-jenkins-on-drone-host.md) (which built the pipeline) and [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) (the sibling repo) — T-203 covers `cv-bff-node` only, and says so deliberately.
