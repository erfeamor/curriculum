---
id: T-203
title: "BFF CI: push the image to ECR and roll the container on master"
repo: cv-bff-node
status: todo
owner:
branch: chore/ci-ecr-deploy-stage
pr:
depends_on: [T-014]
risk: normal
security_review: true
---

## Why this exists

`cv-bff-node/.github/workflows/ci.yml` ends its `docker` job with a promise:

```yaml
# Placeholder until cv-infra exposes a registry + deploy target:
# push to ECR and roll the service on main.
```

T-014 creates exactly that registry and deploy target, so the placeholder becomes actionable. Until then the image is built and thrown away on every run.

This is the same gap the meta README backlog records as *"Automated backend deploy stages in CI (… backend services still deployed manually)"*. Closing it for the BFF does not close it for `cv-domain-service`, which is still manual — do not widen this task to cover both repos.

## Scope

- Add a deploy stage to the existing `docker` job (or a new job gated on it) that authenticates to ECR, pushes the image, and rolls the container on the instance — on `master` pushes only, never on PRs.
- **Credentials:** prefer GitHub OIDC → an IAM role over a long-lived access key. If an access key is used instead, it must be a **dedicated, least-privilege** principal (ECR push to the BFF repo only) — not a reuse of the `cv-project-drone-deploy` user, whose key already fronts S3 and CloudFront for the frontends. Whichever is chosen, write the reasoning into the PR.
- **Rolling the container** without SSH (there is none anywhere): SSM `send-command` against the instance is the mechanism the account already supports via the instance profile. Scope the IAM permission to that instance.
- Keep the existing `test` → `docker` job ordering; a failing test must still block the push.

## Acceptance criteria

- [ ] PR builds do **not** push or deploy — asserted by the workflow's own `if`/`when` conditions, not by convention.
- [ ] A `master` push publishes an image to the T-014 ECR repository and the running container ends up on that image.
- [ ] The IAM principal used can push to the BFF ECR repo and roll that one instance, and nothing else — the policy is in the PR (in `cv-infra` if the role is Terraform-managed; if so, note the cross-repo ordering in the checkpoint).
- [ ] No credential value in the repo; secrets come from GitHub secrets / OIDC.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` still pass; the workflow is valid YAML and runs green end-to-end at least once.

## Definition of done

PR open against `master` from `chore/ci-ecr-deploy-stage`, GitHub Actions green **including the new stage on the merge commit**, merged.

## dev-loop notes

- **Developer:** `infrastructure-engineer` — adapter §2 assigns **all CI config** to this persona, even though the file lives in a `fullstack-developer` repo. **Reviewers:** `/code-review` + `infrastructure-engineer` + `/security-review`.
- **`security_review: true`, forced by adapter §5:** `.github/workflows/**` is a named CI security path, and this diff introduces AWS credentials into CI. T-005 (*limit CI secret blast radius*) is the existing task on that theme — read it before choosing the credential model, and do not re-solve it here.
- **Not on the critical path.** T-501's end-to-end verification needs the BFF *deployed* (T-014), not *auto-deployed*. If the budget is tight, T-014's manual deploy is a legitimate stopping point and this task can wait — but the placeholder comment must then be updated to say so rather than continuing to promise a stage that does not exist.
- Gates (adapter §3): the `cv-bff-node` row — lint, typecheck, test, build. Authoritative CI: **GitHub Actions**.
