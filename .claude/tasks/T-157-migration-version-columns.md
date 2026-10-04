---
id: T-157
title: "cv-database: V2 migration — an additive `version` column on person, experience, education and project, backfilled"
repo: cv-database
status: in_review
owner: tech-product-owner
branch: feat/v2-version-columns
pr: https://github.com/erfeamor/cv-database/pull/7
depends_on: [T-046]
risk: normal   # the first migration since V1; applied to production by Flyway 13.7.0
security_review: false
---

## Why

Split out of [T-113](T-113-optimistic-locking-lost-update.md) at its H1 (2026-10-04): `@Version` needs a column. The migration freeze lifted with T-014 (production Flyway 13.7.0).

## Scope

- `V2__…sql`: `version BIGINT NOT NULL DEFAULT 0` (or the type T-113's entity uses) on `person`, `experience`, `education`, `project`. **Additive only**; existing rows backfill via the default. No change to dev seeds needed beyond what validates.
- The Jenkins migration gate (MySQL 8.4 + Flyway 13.7.0) runs it green.

## Deploy order (important)

Hibernate runs `ddl-auto=validate`: a domain image expecting `version` **won't start** until V2 has run, while the current image tolerates the extra column. So V2 reaches production **before** T-113's image, via [T-044](T-044-app-host-bootstrap-s3-and-redeploy.md)'s `cv-redeploy migrate` (or a host boot).

## Implement + review — 2026-10-04 (5a8ceb9, cv-database#7)

- Developer (fresh backend-developer, ~28k tokens): `V2__add_version_columns.sql`, four additive `ADD COLUMN version BIGINT NOT NULL DEFAULT 0` (person, experience, education, project). Verified locally on mysql:8.4 + Flyway 13.7.0: a fresh DB migrates to v2; **the upgrade path V1 (rows present) → V2 backfills `version = 0`**; the dev-seed callback still runs.
- Driver-verified: the file read. **Jenkins migration gate: success** on the PR.
- **Review round 1: clean.** Note: once merged, the **next app-host boot applies V2 to production** (the bootstrap clones cv-database master and runs Flyway); the current domain image tolerates the extra column (Hibernate `validate`).

## Acceptance criteria

- [x] V2 is additive; existing rows get `version = 0`; Jenkins' migration gate green.
- [ ] Applied to production before T-113's image, and the live `flyway_schema_history` shows V2 success.
