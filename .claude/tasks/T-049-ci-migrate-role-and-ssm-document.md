---
id: T-049
title: "cv-infra: an SSM document `cv-redeploy-migrate` and a master-only OIDC role for cv-database, so production migrations can be applied by CI"
repo: cv-infra
status: todo
owner:
branch: feat/ci-migrate-role
pr:
depends_on: [T-047]   # reuses T-045's OIDC provider and T-047's role/document pattern
risk: normal   # IAM + one SSM document; no host or edge change
security_review: true   # a new trust relationship and a remote-execution path to production — adapter §5
---

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
