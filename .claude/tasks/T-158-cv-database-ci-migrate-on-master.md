---
id: T-158
title: "cv-database: apply new migrations to production automatically on master (GitHub Actions after Jenkins is green → SSM `cv-redeploy-migrate`)"
repo: cv-database
status: todo
owner:
branch: feat/ci-migrate-on-master
pr:
depends_on: [T-049]
risk: normal
security_review: true   # CI config + AWS credentials — adapter §5
---

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
