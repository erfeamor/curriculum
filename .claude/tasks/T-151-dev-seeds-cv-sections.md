---
id: T-151
title: Dev seed data for experience, education, and projects
repo: cv-database
status: todo
owner:
branch: feat/dev-seeds-cv-sections
pr:
depends_on: []
---

## Goal

Extend the dev seed callback so the local stack has a *complete* demo CV — today only the person and skills are seeded, so the new section endpoints and frontends would render empty.

## Pointers

- Edit `sql/dev-seeds/afterMigrate__seed_dev.sql` only — **no new versioned migration**; the schema is untouched.
- The callback runs on **every** migrate: every statement must stay idempotent (`INSERT IGNORE` + natural-key lookups, matching the existing style).
- Seed against the existing `jane.doe@example.com` person.

## Acceptance criteria

- [ ] ≥2 `experience` rows (one with `end_date NULL` = current job), ≥1 `education` row, ≥2 `project` rows.
- [ ] Running migrate twice in a row produces no errors and no duplicate rows.
- [ ] Verified locally: `docker compose up -d && ./scripts/migrate.sh && ./scripts/migrate.sh`, then row counts checked.

## Definition of done

PR open against `master` from `feat/dev-seeds-cv-sections`, CI green, task updated.
