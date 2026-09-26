---
id: T-113
title: "Two concurrent PUTs to the same section row silently lose one write — no `@Version`, no 409"
repo: cv-domain-service
status: todo
owner:
branch: fix/optimistic-locking-sections
pr:
depends_on: [T-108, T-014]   # T-108 puts the read and write in one transaction first; T-014 lifts the migration freeze (production Flyway is still 10 until then, and the board allows no new cv-database migration before it)
risk: normal
security_review: false
---

## Goal

Close **failure mode 2** of [T-108](T-108-untransacted-update-read-modify-write.md), which T-108 declined in writing at H1 (2026-09-26): two concurrent `PUT`s to the same experience, education or project row both return `200`, and the second silently overwrites the first. No client learns the other's write was lost.

## Why it was split off T-108

1. **It needs a migration.** `@Version` adds a `version` column to `experience`, `education` and `project`. The board forbids a new `cv-database` migration until [T-014](T-014-deploy-bff-to-aws.md) lands (production Flyway stays on 10 until then). That makes this a cross-repo change: a `cv-database` migration first, then this.
2. **A 409 on a section PUT is new contract surface.** `docs/api-contract.md` design rule 4 lists 400/404/204. A 409 appears only in § Skills, for duplicate catalog names. Board rule 4 requires a contract PR first, sequenced ahead.
3. **The exposure is latent.** Today the only credentials are the owner's, so this needs one user racing themselves. It becomes real with [T-301](T-301-admin-cv-sections-crud.md)'s admin logins.

## Scope (to refine at stage 0)

Split at refinement into: the contract PR (409 on section PUT, and how a client supplies the version — body field vs `If-Match`), the `cv-database` migration, and the `cv-domain-service` change. `PersonSkill` is checked as T-108 checked it.

## Acceptance criteria

- [ ] A stale concurrent `PUT` gets a `409`, with the response shape the contract PR defines; the fresh one gets `200`.
- [ ] The test demonstrates the lost update on `master` before the fix.
- [ ] The migration is additive and backfills existing rows.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Provenance

Filed by the driver, 2026-09-26, at T-108's H1. The human chose "decline, file a follow-up" over adding `@Version` inside T-108.

## Added 2026-09-26, at T-108's merge

A related gap, found by T-108's developer and left open there: a PUT whose body **equals** the stored values makes Hibernate issue no UPDATE. So a DELETE committed in that window still gets a `200` echoing the deleted row. Nothing is re-inserted, but the client is told the row exists. A version column closes this too, because a version bump forces the UPDATE. Include it in this task's tests.
