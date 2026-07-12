---
id: T-102
title: Education resource in the domain API
repo: cv-domain-service
status: todo
owner:
branch: feat/education-resource
pr:
depends_on: []
---

## Goal

Person-scoped CRUD for education history per [docs/api-contract.md](../../docs/api-contract.md) § Education.

## Pointers

- Same pattern as T-101 (`education/` package mirroring `person/`); if T-101 merged first, follow its shape for consistency — otherwise both follow `person/` and reviewers reconcile.
- The `education` table exists in V1: `institution`, `degree`, `field_of_study`, `start_date`, `end_date`, FK `person_id`.
- Endpoint path is `/educations` (contract choice — keep it even though the plural is awkward).

## Acceptance criteria

- [ ] `GET/POST /api/v1/people/{personId}/educations`, `PUT/DELETE .../{id}` per contract.
- [ ] Unknown person → 404; missing `institution`/`degree`/`startDate` → 400.
- [ ] `@WebMvcTest` + `@DataJpaTest` coverage in the established styles.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Definition of done

PR open against `master` from `feat/education-resource`, CI green, task updated.
