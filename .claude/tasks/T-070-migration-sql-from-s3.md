---
id: T-070
title: "cv-redeploy migrate reads the migration SQL from S3 (git stays as fallback)"
repo: cv-infra
status: in_review
owner: claude
branch: feat/migration-sql-from-s3
pr: https://github.com/erfeamor/cv-infra/pull/54
depends_on: [T-067]
risk: high
security_review: true
---

## Why

Split out of T-068 at its H1 (2026-11-08). The no-public-IPv4 host cannot reach github.com (no IPv6, T-067), and `cv_sync_database_repo` clones cv-database from there. This task moves the delivery to S3 **while the host still has its public IP**, so the new path is proven before any network change.

## Scope

- Reuse the backups bucket (`aws_s3_bucket.backup`): a `migrations/` prefix holding one object, `migrations/cv-database-sql.tgz` (the `sql/` tree), with a lifecycle that keeps it from growing (noncurrent versions expire).
- IAM: the cv-database migrate role (T-049) may `s3:PutObject` that prefix only; the app host role may `s3:GetObject` it only. Update the check-static/plan tests that pin both policies.
- `templates/domain-service-provision.sh`: `cv_sync_database_repo` downloads and unpacks the object into `/opt/cv-database/sql` (replacing the directory atomically), falling back to the git clone **only when the object does not exist yet**; any other failure is fatal. T-068 removes the fallback.
- The cv-redeploy harness and golden fixtures cover both paths.
- Runbook `app-host-deploy.md` documents the order: the object must exist before a host replacement.

## Acceptance criteria

- [ ] Plan test and check-static pin the two scoped statements (write: cv-database role, `migrations/*`; read: app host, `migrations/*`).
- [ ] The harness proves: object present -> used; object missing -> git fallback; any other S3 error -> `cv-redeploy migrate` fails without touching the running container.
- [ ] After apply and a manual upload of the tarball, `cv-redeploy migrate` runs from S3 on the live host.
