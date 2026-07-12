---
id: T-104
title: Project resource in the domain API
repo: cv-domain-service
status: todo
owner:
branch: feat/project-resource
pr:
depends_on: []
---

## Goal

Person-scoped CRUD for portfolio projects per [docs/api-contract.md](../../docs/api-contract.md) § Projects.

## Pointers

- Same pattern as T-101 (`project/` package mirroring `person/`).
- The `project` table exists in V1: `name`, `description`, `repo_url` → `repoUrl`, `start_date`, `end_date`, FK `person_id`.
- Only `name` is required; everything else nullable.

## Acceptance criteria

- [ ] `GET/POST /api/v1/people/{personId}/projects`, `PUT/DELETE .../{id}` per contract.
- [ ] Unknown person → 404; missing `name` → 400.
- [ ] `@WebMvcTest` + `@DataJpaTest` coverage in the established styles.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Definition of done

PR open against `master` from `feat/project-resource`, CI green, task updated.
