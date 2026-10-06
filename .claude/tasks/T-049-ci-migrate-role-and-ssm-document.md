---
id: T-049
title: "cv-infra: an SSM document `cv-redeploy-migrate` and a master-only OIDC role for cv-database, so production migrations can be applied by CI"
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: feat/ci-migrate-role
pr: https://github.com/erfeamor/cv-infra/pull/40
depends_on: [T-047]   # reuses T-045's OIDC provider and T-047's role/document pattern
risk: normal   # IAM + one SSM document; no host or edge change
security_review: true   # a new trust relationship and a remote-execution path to production — adapter §5
checkpoint:
  stage: apply   # review clean; CHECKPOINT before the apply (/usage 40–75%). Next: apply from the branch, set cv-database AWS_DEPLOY_ROLE_ARN, H2, merge, then T-158
  repo: cv-infra
  branch: feat/ci-migrate-role
  worktree: none
  commit: 63f5e1b
  pr: https://github.com/erfeamor/cv-infra/pull/40
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-06T23:45:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 70318
    spawns: 1   # infrastructure-engineer (fresh)
    status: ok   # human-reported /usage 40–75%: implement + review, checkpoint before the apply
    checked: 2026-10-06T23:45:00+02:00
---

## H1 — decided by the human, 2026-10-06 (T-049 + T-158 together)

1. **Trigger (T-158):** a push to `master` touching `sql/migrations/**` or the workflow file itself (so its own merge is the first live run), plus `workflow_dispatch` (still master-only: the OIDC trust pins `ref:refs/heads/master`). Docs- and seed-only pushes never touch production.
2. **Mode:** both implemented and reviewed in parallel against pinned names (document `cv-redeploy-migrate`, role `cv-project-database-migrate`, repo variable `AWS_DEPLOY_ROLE_ARN`, target `tag:Name=cv-project-domain-service`); then strictly serial: apply T-049 → set the variable on cv-database → merge T-049 → merge T-158.
3. **Ordering (schema first, then the domain change):** a documented rule in both repos' CLAUDE.md; no cross-repo guard.
4. **Budget:** `/usage` 40–75% → implement and review both, **checkpoint before the apply**.

## Implement + review — 2026-10-06 (63f5e1b, cv-infra#40)

- Developer (fresh infrastructure-engineer, ~70k tokens): `ci-deploy.tf` third block (document `cv-redeploy-migrate`, role `cv-project-database-migrate`, policy without ECR, two outputs); `terraform test` run `t049_database_migrate` (plan-only, target-scoped); check-static 2c extended (SendCommand count 4 → 6, no ECR, own document only, exact trust). Red first on both; 8 mutations each caught by at least one guard. The plan-time-known statements sit in a named local so `terraform test` can assert them at plan time (T-048's convention); check-static covers the own-document statement.
- Driver-verified: diff read; gate re-run green (fmt, validate, `terraform test` 26/26, check-static).
- **Review round 1 (driver, code + security): clean.** Equivalent to T-047's roles minus ECR; the trust is master-only; the app host's T-005 Deny-NotResource is untouched (the migrate path reads only parameters the host already may).

**Next (resume here):** back up state; plan from the branch, scoped (`-target` the document, role and policy); expect **3 to add, 0 change, 0 destroy**; apply; `gh variable set AWS_DEPLOY_ROLE_ARN -R erfeamor/cv-database` to the `database_migrate_role_arn` output; IAM simulator checks (own document on the tagged host allowed; other documents / `AWS-RunShellScript` / the CI host denied); unscoped plan = No changes; H2; merge cv-infra#40, then cv-database#8 (its merge is the first live run).

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
