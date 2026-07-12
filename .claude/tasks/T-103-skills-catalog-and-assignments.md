---
id: T-103
title: Skill catalog + person-skill assignments
repo: cv-domain-service
status: todo
owner:
branch: feat/skills-resource
pr:
depends_on: []
---

## Goal

Global skill catalog and person-scoped skill assignments per [docs/api-contract.md](../../docs/api-contract.md) § Skills. This is the one resource that is *not* purely nested — read the contract carefully.

## Pointers

- Tables exist in V1: `skill` (unique `name`) and join table `person_skill` (composite PK `person_id + skill_id`, `proficiency` enum).
- The composite key needs an `@EmbeddedId` (or `@IdClass`) on the assignment entity — this is the fiddly part; keep the proficiency enum as a Java `enum` mapped with `@Enumerated(EnumType.STRING)`.
- Duplicate catalog name → 409: catch `DataIntegrityViolationException` rather than pre-checking (race-safe).
- `PUT` on an assignment is an **upsert** (create if absent, update proficiency if present).

## Acceptance criteria

- [ ] `GET/POST /api/v1/skills` (POST duplicate name → 409).
- [ ] `GET /api/v1/people/{personId}/skills` returns joined shape `{ skillId, name, category, proficiency }`.
- [ ] `PUT /api/v1/people/{personId}/skills/{skillId}` upserts with body `{ "proficiency": ... }`; invalid enum value → 400.
- [ ] `DELETE` assignment → 204; unknown person or skill → 404.
- [ ] `@WebMvcTest` + `@DataJpaTest` coverage including the upsert path and the 409.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Definition of done

PR open against `master` from `feat/skills-resource`, CI green, task updated.
