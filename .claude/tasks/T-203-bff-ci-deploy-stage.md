---
id: T-203
title: "BFF CI: push the image to ECR and roll the container on master"
repo: cv-bff-node
status: in_progress
owner: tech-product-owner
branch: chore/ci-ecr-deploy-stage
pr: https://github.com/erfeamor/cv-bff-node/pull/13
depends_on: [T-014, T-044, T-047]   # T-044 added 2026-10-04: rolling the container uses its `cv-redeploy bff-node`; the GitHub → AWS credential (OIDC) is decided at T-403's H1 and reused here
risk: normal
security_review: true
---

## H1 — decided by the human, 2026-10-06 (shared with [T-112](T-112-domain-service-ci-ecr-deploy.md))

- **No deploy credential on the CI host** (every build there is effectively root through `docker.sock`, T-005). **Both repos deploy from GitHub Actions via OIDC**, on a master push only.
- **The deploy call** is `aws ssm send-command` with this service's **own SSM document** (`cv-redeploy-bff-node`, created by [T-047](T-047-ci-deploy-roles-and-ssm-documents.md)), which runs only `cv-redeploy bff-node` on the app host. Wait for the invocation's result and fail the job if it fails.
- **Multi-arch** (`linux/amd64,linux/arm64`, since the app host is Graviton, T-035) via `docker/setup-qemu-action` + buildx on `ubuntu-latest`, pushed to ECR `:latest`.
- **The role ARN comes from a repo variable** (`vars.AWS_DEPLOY_ROLE_ARN`, set by the driver after T-047's apply); the document name and region are workflow constants.
- The deploy job **`needs`** the existing `test` and `docker` jobs (both green) in `ci.yml`.
- **Budget:** `/usage` 40–75%: implement and review, **checkpoint before the merge** (the merge is the first live deploy).


> **Board review 2026-09-28**: **one session, one H1** for T-112 + T-203, with [T-005](T-005-ci-secret-blast-radius.md)'s remainder decided at the same gate as their credential model's input. After H1 the two implementations run in parallel (different repos); their cv-infra IAM changes share one apply.

## Shared decision (added 2026-09-25, board review)

Decide the credential model **together with [T-112](T-112-domain-service-ci-ecr-deploy.md)** (the Jenkins twin), with [T-005](T-005-ci-secret-blast-radius.md) as the input. See T-112's note. Both need an IAM principal in **cv-infra**, so both run in the serial cv-infra chain after T-014.

## Merged 2026-10-06 (2f379c3, cv-bff-node#13), and the first live deploy FAILED: fix forward

- **Proven:** OIDC assumed `cv-project-bff-node-deploy`, and the ECR login succeeded (T-047's trust and permissions work live).
- **Failed:** the QEMU-emulated multi-arch build on `ubuntu-latest` **stalled** (deploy job started 23:47:34Z; no progress or push in 70 min). **The driver cancelled the run.** Nothing reached ECR and no roll ran; production is unaffected (`/cv` 200).
- **H1 amended by the human (2026-10-06):** **native arm64 runners**: a matrix build (amd64 on `ubuntu-latest`, arm64 on `ubuntu-24.04-arm`, free for public repos), each pushing by digest, then a merge job creating the multi-arch `:latest` + `:<sha>` manifest (`docker buildx imagetools create`), then the unchanged SSM roll and smoke. Fix forward on a new branch `fix/native-arm-build`; done when a master deploy run is green end to end.

## Implement + review — 2026-10-06 (e232297)

- Developer (fresh fullstack-developer, ~28k tokens: a `deploy` job (`needs: [test, docker]`, master push only), OIDC, multi-arch QEMU build + push `:latest` + `:<sha>`, `send-command` **by tag**, bounded poll of `list-command-invocations --details` (exactly one, `Success`), a CloudFront smoke on `/cv`.
- Driver-verified: the workflow read; YAML parses; Actions green on the PR (`test` ✓, `docker` ✓, `deploy` skipped as designed). **Review round 1: clean.** Non-blocking: `:<sha>` tags never expire under the untagged-only lifecycle (T-035), so they accumulate (~100 MB per deploy, cents); worth a tagged-image retention rule later.
- **Checkpoint (usage 40–75%): not merged.** The merge to master **is the first live deploy**, so H2 = merge, then watch the run.

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
- [ ] **(board review 2026-10-01; decide at this task's H1 — T-014 declined multi-arch for its one-off builds)** The pushed image is **multi-arch** (`linux/amd64` + `linux/arm64`, one manifest), so [T-035](T-035-app-host-to-graviton.md)'s Graviton swap needs no rebuild here.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` still pass; the workflow is valid YAML and runs green end-to-end at least once.

## Definition of done

PR open against `master` from `chore/ci-ecr-deploy-stage`, GitHub Actions green **including the new stage on the merge commit**, merged.

## dev-loop notes

- **Developer:** `infrastructure-engineer` — adapter §2 assigns **all CI config** to this persona, even though the file lives in a `fullstack-developer` repo. **Reviewers:** `/code-review` + `infrastructure-engineer` + `/security-review`.
- **`security_review: true`, forced by adapter §5:** `.github/workflows/**` is a named CI security path, and this diff introduces AWS credentials into CI. T-005 (*limit CI secret blast radius*) is the existing task on that theme — read it before choosing the credential model, and do not re-solve it here.
- **Not on the critical path.** T-501's end-to-end verification needs the BFF *deployed* (T-014), not *auto-deployed*. If the budget is tight, T-014's manual deploy is a legitimate stopping point and this task can wait — but the placeholder comment must then be updated to say so rather than continuing to promise a stage that does not exist.
- Gates (adapter §3): the `cv-bff-node` row — lint, typecheck, test, build. Authoritative CI: **GitHub Actions**.
