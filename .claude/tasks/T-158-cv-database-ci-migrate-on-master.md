---
id: T-158
title: "cv-database: apply new migrations to production automatically on master (GitHub Actions after Jenkins is green → SSM `cv-redeploy-migrate`)"
repo: cv-database
status: in_progress
owner: tech-product-owner
branch: feat/ci-migrate-on-master
pr:
depends_on: [T-049]
risk: normal
security_review: true   # CI config + AWS credentials — adapter §5
checkpoint:
  stage: implement   # H1 2026-10-06; parallel build with T-049, serial end
  repo: cv-database
  branch: feat/ci-migrate-on-master
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

Filed by the 2026-10-06 board review; see [T-049](T-049-ci-migrate-role-and-ssm-document.md) for the hazard: an automated domain deploy whose schema change hasn't reached production fails to start (`ddl-auto: validate`). Migrations are additive by convention (T-157), so **migrating first is always safe** for the running image.

## Scope (mirror T-112's `deploy.yml`)

- `.github/workflows/migrate.yml`, on a push to `master` only: a **`wait-for-jenkins`** job (the commit's newest `continuous-integration/jenkins/branch` status: success → go, red → stop, bounded) whose Jenkins gate already runs the Flyway migration against MySQL 8.4. Then a **`migrate`** job: OIDC → `vars.AWS_DEPLOY_ROLE_ARN` (T-049's role), `aws ssm send-command --document-name cv-redeploy-migrate --targets Key=tag:Name,Values=cv-project-domain-service`, a bounded `list-command-invocations` poll, print the output, fail unless `Success`. Timeouts on every job.
- **Ordering rule, documented** in cv-database and cv-domain-service CLAUDE.md: a schema change merges in cv-database **first** and its migrate run must be green before the domain change that needs it merges.
- Docs: the repo variable, the flow, and what to do if a migration fails (the domain service keeps running on the old schema; fix forward).

## Acceptance criteria

- [ ] PRs never migrate; a master push migrates only after Jenkins is green.
- [ ] Proven live with the next real migration, or with a no-op run (`cv-redeploy migrate` reports "up to date") on a docs-only master push.
- [ ] The ordering rule is in both repos' CLAUDE.md.
