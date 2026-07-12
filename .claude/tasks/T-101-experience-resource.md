---
id: T-101
title: Experience resource in the domain API
repo: cv-domain-service
status: todo
owner:
branch: feat/experience-resource
pr:
depends_on: []
---

## Goal

Person-scoped CRUD for work experience per [docs/api-contract.md](../../docs/api-contract.md) § Experience.

## Pointers

- Follow the existing package-by-feature pattern: mirror `src/main/java/com/erfeamor/cvdomain/person/` in a new `experience/` package (entity, `JpaRepository`, `@RestController`).
- The `experience` table already exists (V1 migration): columns map to `company`, `role`, `location`, `startDate`, `endDate`, `description`, FK `person_id` with cascade delete.
- `ddl-auto: validate` runs against the real schema — entity column names must match the migration exactly.
- Reuse the 404 style from `PersonController` (`EntityNotFoundException` + handler).

## Acceptance criteria

- [ ] `GET/POST /api/v1/people/{personId}/experiences`, `PUT/DELETE .../{id}` with the status codes from the contract.
- [ ] `personId` is validated: unknown person → 404 on every verb.
- [ ] Bean validation: `company`, `role`, `startDate` required → 400 when missing.
- [ ] Tests in the established styles: `@WebMvcTest` controller tests (mocked repo) + `@DataJpaTest` persistence test.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Definition of done

PR open against `master` from `feat/experience-resource`, CI green, task file updated to `in_review` with the PR URL.
