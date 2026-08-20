---
id: T-151
title: Dev seed data for experience, education, and projects
repo: cv-database
status: todo
owner:
branch: feat/dev-seeds-cv-sections
pr:
depends_on: []
risk: normal
security_review: false   # added 2026-08-20 (hygiene): the key was missing entirely while `risk` was set. Value per adapter §5 — the diff touches none of its security paths; A1 forces /security-review anyway if the real diff disagrees, so this is a stage-0 default, not a ruling.
---

## Goal

Extend the dev seed callback so the local stack has a *complete* demo CV — today only the person and skills are seeded, so the new section endpoints and frontends would render empty.

## The constraint that defines this task: no duplicate rows, ever

The callback runs on **every** migrate, so every statement must be idempotent. The original prose said to use `INSERT IGNORE` "matching the existing style". **That does not work for these three tables**, verified against `V1__init_schema.sql`:

| Table | Constraint beyond PK `id` | `INSERT IGNORE` dedupes? |
|---|---|---|
| `person` | `email` UNIQUE | Yes — existing seed line is safe |
| `skill` | `name` UNIQUE | Yes — existing seed line is safe |
| `person_skill` | composite PK `(person_id, skill_id)` | Yes — existing seed line is safe |
| **`experience`** | **none** — only autoincrement `id` | **No** |
| **`education`** | **none** — only autoincrement `id` | **No** |
| **`project`** | **none** — only autoincrement `id` | **No** |

`INSERT IGNORE` suppresses a row only when a unique or primary-key violation fires. An autoincrement `id` never collides, so every migrate appends another copy — and `migrate.sh` still exits 0 while it happens.

**Use `INSERT … SELECT … WHERE NOT EXISTS (…)`, keyed on a natural-key tuple**, which also resolves `person_id` by email in the same statement:

```sql
INSERT INTO experience (person_id, company, role, location, start_date, end_date, description)
SELECT p.id, 'Acme Corp', 'Senior Engineer', 'Remote', '2022-01-01', NULL, '...'
FROM person p
WHERE p.email = 'jane.doe@example.com'
  AND NOT EXISTS (
    SELECT 1 FROM experience e
    WHERE e.person_id = p.id
      AND e.company = 'Acme Corp'
      AND e.role = 'Senior Engineer'
      AND e.start_date = '2022-01-01'
  );
```

Natural keys: `experience` → company + role + start_date · `education` → institution + degree + start_date · `project` → name + start_date. Pick keys that actually distinguish the rows being seeded — too coarse a key and the `NOT EXISTS` guard suppresses a legitimately distinct second row.

**Adding a unique constraint to make `INSERT IGNORE` work is out of scope** — that is a schema change, i.e. a versioned migration, in a task whose premise is that the schema is untouched. If it turns out to be wanted, it is a separate `T-15x`.

## Pointers

- Edit `sql/dev-seeds/afterMigrate__seed_dev.sql` **only** — no new versioned migration, no edit to `V1__init_schema.sql` (Flyway checksums reject edited history).
- Resolve `person_id` by email every time. Never hardcode a numeric id: it may pass in a fresh DB and break after a `reset.sh` cycle.
- **Jenkins CI is not a signal here.** `Jenkinsfile` pins `FLYWAY_LOCATIONS` to `filesystem:/flyway/sql/migrations`; `dev-seeds` is not on that path, so a syntax error, an FK violation, or the duplicate-row bug above all pass CI green with no output. The verification below is the only check that will ever catch a seed regression — here or on any future edit to this file.

## Acceptance criteria

- [ ] ≥2 `experience` rows, **exactly one** with `end_date NULL` (the current job), and that row has the latest `start_date` of the set.
- [ ] ≥1 `education` row; ≥2 `project` rows.
- [ ] Every insert uses `INSERT … SELECT … WHERE NOT EXISTS` (or an equivalent guard on a real natural key). **A bare `INSERT IGNORE` into `experience`, `education`, or `project` is a blocking defect.**
- [ ] Every row resolves `person_id` via `SELECT id FROM person WHERE email = 'jane.doe@example.com'` — no literal numeric id in the file.
- [ ] Migrating **three times** leaves row counts identical after each run, with no duplicates.
- [ ] Only `sql/dev-seeds/afterMigrate__seed_dev.sql` is touched.

## Verification (QA runs this at stage 4; the developer runs it before opening the PR)

```bash
docker compose down -v && docker compose up -d && sleep 5
./scripts/migrate.sh    # run 1 → capture counts
./scripts/migrate.sh    # run 2 → must equal run 1
./scripts/migrate.sh    # run 3 → must still equal run 1
```

Counts, after every run:
```sql
SELECT COUNT(*) FROM experience e JOIN person p ON e.person_id=p.id WHERE p.email='jane.doe@example.com';
SELECT COUNT(*) FROM education ed JOIN person p ON ed.person_id=p.id WHERE p.email='jane.doe@example.com';
SELECT COUNT(*) FROM project pr JOIN person p ON pr.person_id=p.id WHERE p.email='jane.doe@example.com';
SELECT COUNT(*) FROM experience e JOIN person p ON e.person_id=p.id
  WHERE p.email='jane.doe@example.com' AND e.end_date IS NULL;   -- must be exactly 1
```

Duplicate detector, after runs 2 and 3 — catches exact-row duplication directly:
```sql
SELECT company, role, start_date, COUNT(*) c FROM experience GROUP BY 1,2,3 HAVING c > 1;
SELECT institution, degree, start_date, COUNT(*) c FROM education GROUP BY 1,2,3 HAVING c > 1;
SELECT name, start_date, COUNT(*) c FROM project GROUP BY 1,2 HAVING c > 1;
```

Orphan check — expect 0 for all three:
```sql
SELECT COUNT(*) FROM experience WHERE person_id NOT IN (SELECT id FROM person WHERE email='jane.doe@example.com');
-- repeat for education, project
```

Scope check:
```bash
git diff --stat master...HEAD              # exactly one file
git diff master...HEAD -- sql/migrations/  # must be empty
```

**Pass:** all counts identical across runs 1/2/3, current-job count exactly 1 every time, duplicate detector and orphan checks return zero rows.

**What failure looks like:** `migrate.sh` still exits 0 and Flyway logs "Successfully applied 0 migrations" with no error — **the absence of an error is not evidence of success.** The signature is only in the data: counts double after run 2 and triple after run 3, the current-job count becomes 2 then 3, and the detector returns rows.

Also confirm `./scripts/reset.sh` (volume wipe + re-migrate) lands on the same counts — idempotency across a full teardown, not just repeated migrates on a live volume.

## Definition of done

PR open against `master` from `feat/dev-seeds-cv-sections`, triple-migrate verification clean with zero duplicates, scope boundary verified, CI green (noting that green CI proves nothing for this file), task updated to `in_review` with the PR URL.
