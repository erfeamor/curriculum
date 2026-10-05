---
id: T-047
title: "cv-infra: GitHub OIDC deploy roles for cv-domain-service and cv-bff-node, and one SSM document per service that runs only `cv-redeploy <svc>`"
repo: cv-infra
status: in_progress
owner: tech-product-owner
branch: feat/ci-deploy-roles
pr:
depends_on: [T-044, T-045]   # cv-redeploy on the host; the OIDC provider
risk: normal   # IAM + SSM documents only; no host or edge change
security_review: true   # new trust relationships and a remote-execution path to production — adapter §5
checkpoint:
  stage: implement   # filed at the T-112/T-203 shared H1, 2026-10-06
  repo: cv-infra
  branch: feat/ci-deploy-roles
  worktree: none
  commit:
  pr:
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-06T10:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
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

## Acceptance criteria

- [ ] Offline (red first): the exact trust conditions; each role's actions and resources (own ECR repo; own document + the app instance only; no `*` resource except `GetAuthorizationToken`); the documents run the exact command and take no parameters.
- [ ] Applied (IAM + SSM documents only).
- [ ] Live: `simulate-principal-policy`. Each role may push to its own repo but not the other's; may send its own document to the app instance but not the other document, not `AWS-RunShellScript`, and not to the CI host.
- [ ] Gates green; `/security-review` clean.
