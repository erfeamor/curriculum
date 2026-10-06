---
id: T-049
title: "cv-infra: an SSM document `cv-redeploy-migrate` and a master-only OIDC role for cv-database, so production migrations can be applied by CI"
repo: cv-infra
status: in_progress
owner: tech-product-owner
branch: feat/ci-migrate-role
pr:
depends_on: [T-047]   # reuses T-045's OIDC provider and T-047's role/document pattern
risk: normal   # IAM + one SSM document; no host or edge change
security_review: true   # a new trust relationship and a remote-execution path to production — adapter §5
checkpoint:
  stage: implement   # H1 2026-10-06; parallel build with T-158, serial end
  repo: cv-infra
  branch: feat/ci-migrate-role
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
  updated: 2026-10-06T23:45:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage 40–75%: implement + review, checkpoint before the apply
    checked: 2026-10-06T23:45:00+02:00
---

## H1 — decided by the human, 2026-10-06 (T-049 + T-158 together)

1. **Trigger (T-158):** a push to `master` touching `sql/migrations/**` or the workflow file itself (so its own merge is the first live run), plus `workflow_dispatch` (still master-only: the OIDC trust pins `ref:refs/heads/master`). Docs- and seed-only pushes never touch production.
2. **Mode:** both implemented and reviewed in parallel against pinned names (document `cv-redeploy-migrate`, role `cv-project-database-migrate`, repo variable `AWS_DEPLOY_ROLE_ARN`, target `tag:Name=cv-project-domain-service`); then strictly serial: apply T-049 → set the variable on cv-database → merge T-049 → merge T-158.
3. **Ordering (schema first, then the domain change):** a documented rule in both repos' CLAUDE.md; no cross-repo guard.
4. **Budget:** `/usage` 40–75% → implement and review both, **checkpoint before the apply**.

## Why

Filed by the 2026-10-06 board review. Since [T-112](T-112-domain-service-ci-ecr-deploy.md), a master push on cv-domain-service **deploys itself**. But a cv-database migration reaches production **only** if an operator runs `cv-redeploy migrate` (T-044) or the app host reboots. The domain service runs Hibernate with `ddl-auto: validate`, so the first domain change that needs a new column will deploy, **fail to start, and take the API down**. [T-158](T-158-cv-database-ci-migrate-on-master.md) adds the cv-database pipeline step; this task provides what it calls.

## Scope (mirror T-047)

- `aws_ssm_document` **`cv-redeploy-migrate`** (Command, schema 2.2, no parameters): exactly `/usr/local/bin/cv-redeploy migrate`.
- Role **`cv-project-database-migrate`**: trusted only via `StringEquals` `aud = sts.amazonaws.com` and `sub = repo:erfeamor/cv-database:ref:refs/heads/master`. It may `ssm:SendCommand` with **its own document** and on `instance/*` **conditioned on `ssm:resourceTag/Name = cv-project-domain-service`**, plus `ssm:Get/ListCommandInvocations`. **No ECR, nothing else.**
- An output with the role ARN; tests and check-static guards as in T-047.

## Acceptance criteria

- [ ] Offline (red first): the trust conditions, the policy shape, the parameterless document.
- [ ] Applied (IAM + SSM document only); simulator: own document on the tagged app host allowed; other documents, `AWS-RunShellScript` and the CI host denied; no ECR.
- [ ] Gates green; `/security-review` clean.
