---
id: T-001
title: "Self-hosted MySQL follow-ups: backup, dev parity, docs"
repo: cv-infra + meta
status: todo
owner:
branch: feat/selfhost-mysql-followups
pr:
depends_on: []
---

## Goal

Close the loose ends left by moving MySQL off RDS onto a self-hosted 8.4 container on the domain-service EC2 (cv-infra PR #8). Self-hosting removed the RDS instance cost and the MySQL 8.0 Extended Support charge, but it also dropped RDS's managed backups and left some docs/config referencing the old setup.

## Scope (three independent pieces — split into separate PRs if convenient)

### 1. Backup — replace RDS managed backups
- Nightly logical dump on the domain-service EC2: `mysqldump` from the `mysql` container → `aws s3 cp` to a dedicated bucket/prefix. A systemd timer (or cron) provisioned via `templates/domain-service-user-data.sh`.
- IAM: extend the instance role (`iam.tf`) with least-privilege `s3:PutObject` to that prefix only. Retention via an S3 lifecycle rule (keep it Free-Tier — a handful of daily dumps).
- Verify a dump can be restored into a throwaway MySQL 8.4 container.

### 2. Dev / prod parity
- `docker-compose.dev.yml` still pins `mysql:8.0` while prod now runs `mysql:8.4`. Bump dev to `8.4` (note: an existing `cv-dev-mysql-data` volume created under 8.0 may need `docker compose down -v`, or rely on MySQL's in-place 8.0→8.4 upgrade).
- Re-run the local stack + `curl :3000/api/v1/people/1` to confirm parity (already verified once during the migration).

### 3. Docs drift — RDS → self-hosted
- Root `README.md` / `README.es.md`: the architecture layer + the roadmap infra line still say "RDS MySQL". Update to self-hosted MySQL 8.4 on EC2.
- `docs/architecture.md` + `diagrams/architecture.mmd`: drop RDS from the topology/flow (MySQL is now on the domain-service box).
- `cv-database` CLAUDE.md / README: clarify the target is MySQL 8.4.

## Acceptance criteria

- [ ] Nightly `mysqldump→S3` runs on a schedule, lands in S3, and a restore is verified; IAM is least-privilege; `terraform fmt`/`validate`/`test` pass.
- [ ] `docker-compose.dev.yml` runs `mysql:8.4` and the local E2E smoke passes.
- [ ] No "RDS" references remain in the root docs, architecture notes/diagram, or cv-database docs.

## Definition of done

PR(s) open against `master` from `feat/selfhost-mysql-followups`, CI/offline gates green, task updated.
