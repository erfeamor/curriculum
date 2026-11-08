---
id: T-071
title: "cv-database migrate workflow publishes sql/ to S3 before the redeploy"
repo: cv-database
status: done
owner: claude
branch: feat/publish-sql-to-s3
pr: https://github.com/erfeamor/cv-database/pull/9
depends_on: [T-070]
risk: normal
security_review: true
---

## Why

Counterpart of T-070: the host now reads the migration SQL from `s3://<backup bucket>/migrations/cv-database-sql.tgz`.

## Scope

- `migrate.yml` (and Jenkins stays untouched): after the gate is green on master, tar `sql/` and `aws s3 cp` it to that key with the existing OIDC role, then send `cv-redeploy-migrate`. Bucket name from a repo variable (output of cv-infra).
- Only on master and `workflow_dispatch`; never on PRs.
- Run it once (dispatch) so the object exists before T-068's host replacement.

## Acceptance criteria

- [ ] A master run uploads the tarball and the migration still succeeds; the object matches `git archive` of `sql/`.
- [ ] A PR run uploads nothing.

## DONE (2026-11-08)

cv-database#9 and #10 merged. #9's first master run uploaded the object, then failed on a `head-object` read-back (the role is write-only by design, T-070); #10 dropped the read-back. Live proof: `cv-redeploy migrate` on the app host printed `migration SQL: s3://cv-project-mysql-backup-dev/migrations/cv-database-sql.tgz` (no git fallback) and Flyway reported schema `cv` up to date. T-068 is unblocked.
