---
id: T-071
title: "cv-database migrate workflow publishes sql/ to S3 before the redeploy"
repo: cv-database
status: in_review
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
