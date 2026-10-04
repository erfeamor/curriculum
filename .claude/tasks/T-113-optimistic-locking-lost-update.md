---
id: T-113
title: "Two concurrent PUTs to the same section row silently lose one write — no `@Version`, no 409"
repo: cv-domain-service
status: done
owner: tech-product-owner
branch: fix/optimistic-locking-sections
pr: https://github.com/erfeamor/cv-domain-service/pull/15
depends_on: [T-108, T-014, T-046, T-157]   # T-108 puts the read and write in one transaction first; T-014 lifts the migration freeze (production Flyway is still 10 until then, and the board allows no new cv-database migration before it)
risk: normal
security_review: false
---

> **Board review 2026-10-04 — ship with T-116 as one domain-service deploy.** [T-116](T-116-domain-service-scope-enforcement.md) also changes cv-domain-service and also needs a deploy. Merge both, then build and push **one** image, and deploy it with [T-044](T-044-app-host-bootstrap-s3-and-redeploy.md)'s `cv-redeploy domain-service` (no host replacement). If T-044 hasn't landed, the deploy waits for it rather than replacing the host again.

> **Board review 2026-09-28**: was missing from the lane. It is now scheduled **right after [T-014](T-014-deploy-bff-to-aws.md)** (session 4), when the migration freeze lifts. Its contract PR (the 409 shape) can be drafted earlier.

## H1 — decided by the human, 2026-10-04

1. **`version` is optional on PUT:** present and stale → **409**; absent → the write wins as today. The admin always sends it ([T-303](T-303-admin-send-version-handle-409.md)).
2. **Scope: person + experience, education and project.** Person-skill assignments stay as T-108 left them.
3. **Split (adapter §2):** [T-046](T-046-contract-section-version-409.md) contract (driver) → [T-157](T-157-migration-version-columns.md) V2 migration → **this task: the domain service** (`@Version`, the 409 handler, `version` in responses) → T-303 admin.
4. **Deploy:** batched with [T-116](T-116-domain-service-scope-enforcement.md) into one image, after T-157's migration has run, via [T-044](T-044-app-host-bootstrap-s3-and-redeploy.md)'s `cv-redeploy` (which gains a `migrate` step). Hibernate validates the schema, so the image must not start before V2.

## ✅ H2 — 2026-10-04: merged 28b948d (cv-domain-service#15); NOT YET DEPLOYED

- **Merged.** The image built from master now **requires cv-database V2** (`ddl-auto: validate`). Images are pushed by hand, so nothing deploys automatically. **Deploy with T-116 via [T-044](T-044-app-host-bootstrap-s3-and-redeploy.md):** `cv-redeploy migrate` (V2) → `cv-redeploy domain-service`. **Never push this image to ECR `:latest` before V2 is live**: a host replacement would pull it and the domain service would fail to start.
- **Contract nuance resolved by amendment** (the human's choice): rule 8 now says an omitted version can still get 409 on a genuine concurrent write (curriculum#108, 0fcfc70).

## Implement + review — 2026-10-04 (d366a1c, cv-domain-service#15)

- Developer (fresh backend-developer, ~114k tokens): `@Version` on Person/Experience/Education/Project; an explicit `StaleVersionException.requireCurrent` before any field copy, inside T-108's transaction → 409 `ProblemDetail`, nothing written; an in-flight race (`ObjectOptimisticLockingFailureException`) → 409, or 404 if deleted (existence re-checked in a fresh transaction); **every successful PUT bumps the version**, no-op bodies included (`PESSIMISTIC_FORCE_INCREMENT`), which also closes T-108's no-op-PUT-vs-DELETE leftover (now 404); POST discards a client version.
- **Bug fixed along the way:** Person's PUT wasn't transactional, so a person deleted mid-update was **re-inserted with 200** (T-108 had fixed only the sections). Now 404.
- `OptimisticConcurrencyTest`, 40 cases, red first on master (the lost update: B's 200 overwrote A). Driver-verified: checkstyle exit 0, **227/227**; **Jenkins green**.
- **Review round 1: clean.** Open for H2: **contract nuance**: a PUT *omitting* `version` that loses a genuine millisecond race gets 409, not last-write-wins as rule 8's wording says.
- **Not deployed:** needs V2 live first (`ddl-auto: validate`); ships with T-116 via T-044.

## Goal

Close **failure mode 2** of [T-108](T-108-untransacted-update-read-modify-write.md), which T-108 declined in writing at H1 (2026-09-26): two concurrent `PUT`s to the same experience, education or project row both return `200`, and the second silently overwrites the first. No client learns the other's write was lost.

## Why it was split off T-108

1. **It needs a migration.** `@Version` adds a `version` column to `experience`, `education` and `project`. The board forbids a new `cv-database` migration until [T-014](T-014-deploy-bff-to-aws.md) lands (production Flyway stays on 10 until then). That makes this a cross-repo change: a `cv-database` migration first, then this.
2. **A 409 on a section PUT is new contract surface.** `docs/api-contract.md` design rule 4 lists 400/404/204. A 409 appears only in § Skills, for duplicate catalog names. Board rule 4 requires a contract PR first, sequenced ahead.
3. **The exposure is latent.** Today the only credentials are the owner's, so this needs one user racing themselves. It becomes real with [T-301](T-301-admin-cv-sections-crud.md)'s admin logins.

## Scope (to refine at stage 0)

Split at refinement into: the contract PR (409 on section PUT, and how a client supplies the version — body field vs `If-Match`), the `cv-database` migration, and the `cv-domain-service` change. `PersonSkill` is checked as T-108 checked it.

## Acceptance criteria

- [x] A stale concurrent `PUT` gets a `409`, with the response shape the contract PR defines; the fresh one gets `200`.
- [x] The test demonstrates the lost update on `master` before the fix.
- [ ] The migration is additive and backfills existing rows.
- [x] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Provenance

Filed by the driver, 2026-09-26, at T-108's H1. The human chose "decline, file a follow-up" over adding `@Version` inside T-108.

## Added 2026-09-26, at T-108's merge

A related gap, found by T-108's developer and left open there: a PUT whose body **equals** the stored values makes Hibernate issue no UPDATE. So a DELETE committed in that window still gets a `200` echoing the deleted row. Nothing is re-inserted, but the client is told the row exists. A version column closes this too, because a version bump forces the UPDATE. Include it in this task's tests.
