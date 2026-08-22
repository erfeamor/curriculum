---
id: T-151
title: Dev seed data for experience, education, and projects
repo: cv-database
status: done
owner: backend-developer
branch: feat/dev-seeds-cv-sections
pr: https://github.com/erfeamor/cv-database/pull/4
depends_on: []
risk: normal
checkpoint:
  stage: done                 # merged as 865784f 2026-08-22; H2 accepted by the human
  merged: 865784f
  commits: [16038dc, e431304]
  a1: pass                    # triple-migrate + reset.sh, re-run INDEPENDENTLY by the driver after each round. cv-database has no lint/test gate (adapter §3): the gate IS a flyway migrate against a throwaway 8.4.
  ci: pass                    # Jenkins PR-4/2 success 16:20:44Z. PR-4/1 FAILED 62s after a cold start (T-026, SIXTH occurrence, cold start VERIFIED via describe-instances LaunchTime) -- recorded there, not counted against this task. Note the DoD's own caveat: green CI proves nothing for this file, since Jenkinsfile:25 pins FLYWAY_LOCATIONS to the migrations path and dev-seeds is never executed in CI.
  review_round: 1
  review_status: CONVERGED
  review_trail: "/code-review high effort on 16038dc: NO blocking defects, and it verified by standing up its own MySQL 8.4 and running the real migrate three times rather than reading. Four low findings, PO ruled APPLY ALL FOUR (all inside the AC, which says '>=2 project rows', not exactly two). (1) Key-column edit through cv-admin-react makes the guard miss and resurrects the row -> TWO rows with end_date NULL, the exact invariant this task's AC pins down, broken silently while migrate exits 0. Inherent to insert-only seeding, NOT fixable without the out-of-scope unique constraint -> documented, not fixed. (2) Converse: editing a NON-key field in this file applies on a fresh volume and silently no-ops on an existing one -> documented. (3) Every row had a distinct start_date, so the contract's mandatory `id ASC` tiebreaker was never exercised locally -> added a 4th project sharing 2021-11-08. This is the exact counterpart of the H1 ruling: H1 added the undated row to exercise 'undated last', this closes the other sharp edge. (4) Content error rendering on the public demo site: 'seven independent repos' followed by a list of six, cv-observability missing -> list completed, count kept."
  qa_stage4: pass             # 2026-08-22, env slot 0, no defects
  qa_stage4_mount_pairing: "T-028's binding, and T-151 is the FIRST task it binds. BOTH halves obtained, because a bind mount leaves no trace after teardown: (a) .Mounts captured WHILE THE STACK WAS UP -- cvdl_t-151-flyway-1 bound Source=/home/erfeamor/work/cvdl-worktrees/T-151/sql -> /flyway/sql, i.e. the worktree, not the main checkout; (b) paired behavioural check -- experience=3, education=2, project=4 on the meta stack DB, counts that are IMPOSSIBLE unless the worktree's SQL executed, since master's seed file has no rows in those tables at all. The pairing is the sign-off; neither half alone is."
  qa_stage4_counts: "Triple-migrate + reset.sh on cv-database's own stack: 3/2/4/1 identical after runs 1, 2, 3 AND after reset.sh. Duplicate detectors on all three tables and orphan checks returned zero rows every time. Scope: exactly one file, sql/migrations/ empty."
  qa_stage4_ordering: "Verified THROUGH THE DOMAIN API (localhost:8090), not by re-running the ORDER BY in SQL: GET /api/v1/people/1/projects returned id1 (2024-02-05) -> id2 (2021-11-08) -> id3 (2021-11-08) -> id4 (NULL). The tied pair resolves id2 before id3, so the mandatory id-ASC tiebreak is distinguished from insertion-order-by-accident, and the undated row sorts last. Both sharp edges of the ordering contract now demonstrable end to end against T-104's real implementation."
  qa_stage4_failure_modes: "BOTH documented failure modes REPRODUCED and matching the comments exactly, which is what makes the comments a deliverable rather than a claim. (a) Non-key field edited in the seed file + migrate on an existing volume -> DB kept the old value, silent no-op. (b) UPDATE experience SET company='Acme Corporation' (simulating an admin-UI edit) + migrate -> guard missed, original row resurrected, TWO rows with end_date NULL. reset.sh restored the baseline in both cases, so the documented remedy is verified rather than asserted."
  qa_correction: "The '1062 warning' count stated in the task brief and both agent reports was TWO; on MySQL 8.4 it is ELEVEN (1 person + 5 skill + 5 person_skill). Not a defect -- same expected INSERT IGNORE noise -- but the figure never reached the committed file (grep for 1062/duplicate/warning returns nothing there), so this is a record correction only, no code change. Worth keeping because 'what does clean noise look like' is exactly the judgement this file's silent-failure mode depends on."
  qa_stage4_teardown: "Both stacks down -v; override file removed; 3306 and 3316 confirmed free; no cvdl_t-151 or cv-database containers remain."
  repo: cv-database
  branch: feat/dev-seeds-cv-sections
  worktree: none              # CLEARED at close-out 2026-08-22, per the convention T-028 made load-bearing. It WAS /home/erfeamor/work/cvdl-worktrees/T-151; `git worktree remove` run after the merge.
  pr:
  developer: backend-developer
  reviewers: ["/code-review", "quality-assurance (coverage lens)"]
  risk: normal
  security_review: false      # SQL data-only diff; no adapter §5 path. A1 re-checks against the real diff.
  env_slot: 0
  review_round: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-22
  h1_rulings:
    - "SEED ONE UNDATED PROJECT, AND FIX THE GUARD. Ratified by the human 2026-08-22 against the alternative of keeping every seeded project dated. Rationale: T-104 merged hours earlier and its 'undated projects last' ordering is the contract's sharp edge; an undated seed row is what exercises it end to end through the real stack, and it is also the row whose idempotency guard this task got wrong. Fixing and demonstrating in one move beats sidestepping."
    - "THIS TASK'S OWN PRESCRIBED NATURAL KEY IS BROKEN FOR project. It specifies `name + start_date`, but project.start_date is NULLABLE (V1, verified -- the only nullable date of the three). `pr.start_date = '...'` never matches NULL, so NOT EXISTS passes and an undated project is re-inserted ON EVERY MIGRATE -- exactly the duplicate-row bug this task exists to prevent, reproduced by the fix it prescribes. Use null-safe equality (`<=>`) or explicit IS NULL handling. The prose is struck and corrected in the body."
    - "T-028 HAS LANDED; the in-body blockquote telling the implementer to hand-build a build-context override is superseded. T-028 additionally names THIS TASK as the first it binds: stage-4 sign-off requires BOTH the .Mounts capture AND an independent behavioural check, because a bind mount leaves no trace after teardown (mount provenance is permanently weaker than build-label provenance)."
    - "PORT 3306 EXCLUSIVITY IS A PRECONDITION, not a nicety. scripts/migrate.sh runs --network host and flyway.conf hardcodes localhost:3306, while docker-compose.yml publishes 3306 with a FIXED container_name: cv-database. Any other stack holding 3306 -- the meta dev stack included -- silently receives this task's migrate. This is the same hazard T-016 encoded as depends_on rather than prose. Verify nothing owns 3306 before every verification run."
    - "JENKINS IS NOT A SIGNAL AND THAT IS VERIFIED, not assumed: Jenkinsfile:25 pins FLYWAY_LOCATIONS=filesystem:/flyway/sql/migrations and dev-seeds is not on that path. Green CI is required by the DoD but proves nothing about this file. The triple-migrate verification is the only check that will ever catch a seed regression, here or on any future edit."
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

Natural keys: `experience` → company + role + start_date · `education` → institution + degree + start_date · ~~`project` → name + start_date~~ **`project` → name + start_date, compared with `<=>`** (see below). Pick keys that actually distinguish the rows being seeded — too coarse a key and the `NOT EXISTS` guard suppresses a legitimately distinct second row.

> ### THIS TASK'S OWN GUARD IS BROKEN FOR `project` — found and corrected at H1, 2026-08-22
>
> `project.start_date` is **nullable** — verified in `V1__init_schema.sql`, and it is the only nullable date of the three tables. In MySQL, `pr.start_date = '2024-01-01'` is never true when the stored value is NULL, and neither is `pr.start_date = NULL`. So for an **undated** project the `NOT EXISTS` subquery finds nothing, the guard passes, and **the row is inserted again on every single migrate** — precisely the duplicate-row bug this task exists to prevent, reproduced by the fix it prescribes.
>
> **Use the null-safe equality operator `<=>`** (or an explicit `(pr.start_date = X OR (pr.start_date IS NULL AND X IS NULL))`) on `project.start_date`. `experience.start_date` and `education.start_date` are `NOT NULL`, so plain `=` is correct there and null-safe handling would be dead code implying a nullability the schema does not have.
>
> **H1 ratified seeding one undated project deliberately**, rather than avoiding the case: [T-104](T-104-project-resource.md) merged hours before this task started and its *"undated projects last"* ordering is the contract's sharp edge, so the undated row is what exercises it end to end. The row that demonstrates the feature is the same row that breaks the guard — which is why sidestepping it would have left the trap for whoever next edits this file.
>
> **Note the shape**, because it is this board's third specification defect in three days and the second found before implementation: the task correctly diagnosed that `INSERT IGNORE` cannot dedupe these tables, correctly prescribed `NOT EXISTS`, and then wrote a key that silently fails on the one nullable column involved. Being right about the mechanism is not the same as being right about the instance.

**Adding a unique constraint to make `INSERT IGNORE` work is out of scope** — that is a schema change, i.e. a versioned migration, in a task whose premise is that the schema is untouched. If it turns out to be wanted, it is a separate `T-15x`.

## Pointers

- Edit `sql/dev-seeds/afterMigrate__seed_dev.sql` **only** — no new versioned migration, no edit to `V1__init_schema.sql` (Flyway checksums reject edited history).
- Resolve `person_id` by email every time. Never hardcode a numeric id: it may pass in a fresh DB and break after a `reset.sh` cycle.
- **Jenkins CI is not a signal here.** `Jenkinsfile` pins `FLYWAY_LOCATIONS` to `filesystem:/flyway/sql/migrations`; `dev-seeds` is not on that path, so a syntax error, an FK violation, or the duplicate-row bug above all pass CI green with no output. The verification below is the only check that will ever catch a seed regression — here or on any future edit to this file.


> ~~**Before stage-4 QA: the generated stack builds `master`, not your worktree** — see [T-028](T-028-qa-env-generator-worktree-build-context.md). Until that lands, add a build-context override pointing at your worktree, and *prove* which tree you built rather than assuming it.~~
>
> **SUPERSEDED 2026-08-22 — [T-028](T-028-qa-env-generator-worktree-build-context.md) landed (`74be2c8`).** `scripts/qa-env-override.py` now repoints **bind mounts** as well as build contexts, which is the half that matters here: the meta stack bind-mounts `./cv-database/sql` into its `flyway` service, so before T-028 this task would have seeded from **master's SQL** while the generator printed *"no service repointed: task repo 'cv-database' is not built by docker-compose.dev.yml"* — output that reads as "nothing to do here". Do not hand-build an override.
>
> **T-028 names this task as the first it binds.** Mount provenance is permanently weaker than build-label provenance: a build label is an image property and survives teardown, while a bind mount leaves no trace beyond `docker inspect .Mounts`, which exists **only while the stack is up**. Stage-4 sign-off therefore requires **both** the `.Mounts` capture **and** an independent behavioural check. The pairing is the proof.

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
