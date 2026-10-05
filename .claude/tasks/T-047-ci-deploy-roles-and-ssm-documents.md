---
id: T-047
title: "cv-infra: GitHub OIDC deploy roles for cv-domain-service and cv-bff-node, and one SSM document per service that runs only `cv-redeploy <svc>`"
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: feat/ci-deploy-roles
pr: https://github.com/erfeamor/cv-infra/pull/37
depends_on: [T-044, T-045]   # cv-redeploy on the host; the OIDC provider
risk: normal   # IAM + SSM documents only; no host or edge change
security_review: true   # new trust relationships and a remote-execution path to production — adapter §5
checkpoint:
  stage: h2   # applied 2026-10-06 (IAM + SSM documents); simulator 16/16 as designed; awaiting human acceptance
  repo: cv-infra
  branch: feat/ci-deploy-roles
  worktree: none
  commit: 19dd954
  pr: https://github.com/erfeamor/cv-infra/pull/37
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-06T10:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 50245
    spawns: 1   # infrastructure-engineer (fresh)
    status: ok   # human-reported /usage 40–75%
    checked: 2026-10-06T10:00:00+02:00
---

## Why

Filed at the shared H1 of [T-112](T-112-domain-service-ci-ecr-deploy.md) and [T-203](T-203-bff-ci-deploy-stage.md) (2026-10-06). **No deploy credential may live on the CI host:** Jenkins and Drone mount `docker.sock`, so any build is effectively root there ([T-005](T-005-ci-secret-blast-radius.md)). Both repos therefore deploy from **GitHub Actions** via the OIDC provider T-045 created.

## H1 — decided by the human, 2026-10-06

1. **Two roles**, each trusted only via `StringEquals` on `aud = sts.amazonaws.com` and `sub = repo:erfeamor/<repo>:ref:refs/heads/master`: `cv-project-domain-service-deploy` (cv-domain-service) and `cv-project-bff-node-deploy` (cv-bff-node).
2. **Each role may:**
   - `ecr:GetAuthorizationToken` (resource `*`, as ECR requires);
   - push to **its own** ECR repository only: `BatchCheckLayerAvailability`, `InitiateLayerUpload`, `UploadLayerPart`, `CompleteLayerUpload`, `PutImage`, `BatchGetImage`;
   - `ssm:SendCommand` only with **its own** SSM document **and** only on the app instance's ARN;
   - read its command's result (`ssm:GetCommandInvocation`, `ssm:ListCommandInvocations`).
   - Nothing else.
3. **Two SSM documents** (`aws_ssm_document`, type Command): `cv-redeploy-domain-service` and `cv-redeploy-bff-node`. Each runs exactly `/usr/local/bin/cv-redeploy <svc>` and takes **no parameters**, so there's no injection surface and no arbitrary shell.
4. **Outputs:** both role ARNs and both document names (the driver sets them as repo variables).

## Implement, review and apply — 2026-10-06 (19dd954, cv-infra#37)

- Developer (fresh infrastructure-engineer, ~50k tokens): `ci-deploy.tf`: two Command documents (schema 2.2, one step, exactly `cv-redeploy <svc>`, **no parameters**); two roles (`StringEquals` aud + master `sub`); each policy = GetAuthorizationToken `*`, push and pull on its own repo, SendCommand on its own document + `instance/*` **conditioned on `ssm:resourceTag/Name = cv-project-domain-service`** (a mid-task driver change: target by tag, since the host is replaced often), Get/ListCommandInvocations `*`. check-static 2c (mutation-checked). Red first → `terraform test` 24/24 (scoped, 18 s).
- **Review round 1 (code + security): clean.** Applied: **6 added** (IAM + SSM only). Both role ARNs are set as `AWS_DEPLOY_ROLE_ARN` repo variables on cv-bff-node and cv-domain-service.
- **Simulator, 16/16 as designed** (per role): PutImage own repo allowed / other repo implicitDeny; SendCommand own document allowed / other document and `AWS-RunShellScript` implicitDeny; SendCommand on the app instance (`Name=cv-project-domain-service`) allowed / the CI host (`cv-project-drone`) implicitDeny; `iam:PassRole` implicitDeny. The branch plans **No changes**.

## Acceptance criteria

- [x] Offline (red first): the exact trust conditions; each role's actions and resources (own ECR repo; own document + the app instance only; no `*` resource except `GetAuthorizationToken`); the documents run the exact command and take no parameters.
- [x] Applied (IAM + SSM documents only).
- [x] Live: `simulate-principal-policy`. Each role may push to its own repo but not the other's; may send its own document to the app instance but not the other document, not `AWS-RunShellScript`, and not to the CI host.
- [x] Gates green; `/security-review` clean.
