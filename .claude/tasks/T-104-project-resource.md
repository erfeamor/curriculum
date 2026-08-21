---
id: T-104
title: Project resource in the domain API
repo: cv-domain-service
status: todo
owner:
branch: feat/project-resource
pr:
depends_on: []
risk: normal
security_review: false   # promoted 2026-08-20: the value already existed at checkpoint.security_review and was missing at top level, where the board and the driver read it. Same shape as T-011's pr: bug. Value unchanged — this is not a new ruling.
checkpoint:
  stage: H1
  reset_note: "Claim reset 2026-08-09: status was in_progress with owner backend-developer, but NO implementation existed — worktree sat at master's tip (d78ef27) with 0 changed files and no remote branch. The stale claim blocked re-pickup under board rule 1 ('if owner: is already set, pick another task'), parking three of the five wave-1 tasks behind a status that was not true. NOTE this is NOT a fresh todo: stage H1 is real — refinement and the DoR/test plan in this file were completed and ratified, so whoever picks it up starts at implementation, not refinement. The local worktree and branch still exist and are reusable."
  repo: cv-domain-service
  branch: feat/project-resource
  worktree: /home/erfeamor/work/cvdl-worktrees/T-104
  pr:
  developer: backend-developer
  reviewers: [code-review, quality-assurance]
  risk: normal
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 3
  updated: 2026-08-04
---

## Goal

Person-scoped CRUD for portfolio projects per [docs/api-contract.md](../../docs/api-contract.md) § Projects.

Path `/api/v1/people/{personId}/projects`. **Required: `name` only** — `description`, `repoUrl`, `startDate`, `endDate` are all nullable. Payload: `id, name, description, repoUrl, startDate, endDate`.

## Pointers

- `project/` package mirroring `person/`. Structural twin of T-101 — **but see the required-field warning below; it is not a pure copy.**
- The `project` table exists in V1: `name`, `description`, `repo_url`, `start_date`, `end_date`, FK `person_id` cascade. **No migration needed.**
- **Do not touch `SecurityConfig`.**

## Definition of Ready — scope decisions

T-101's four ratified rulings apply **unchanged** (QA confirmed required-field count is orthogonal to identity/lookup semantics):

1. DELETE of a nonexistent project id → **404** (not 204).
2. PUT/DELETE of an id belonging to a different person → **404**, via a scoped `findByIdAndPersonId`.
3. GET collection for an existing person with zero rows → **200 `[]`**.
4. `personId` existence checked **before** the child lookup.

Two resource-specific rulings, ratified against contract text:

5. **`repoUrl` gets NO format validation.** § Projects states only "Required: `name`"; no format constraint appears anywhere in the contract, and § Non-goals doesn't reserve one. A `@URL`/`@Pattern` on `repoUrl` would silently narrow the contract — it is an unrequested-scope finding at review, not a nice-to-have. C15 makes this executable: an arbitrary non-URL string is accepted with 201.
6. **POST with only `name` is a legitimate request shape.** Projects is the only one of the three resources where `startDate`/`endDate` are *also* nullable at the schema level, so this has no T-101/T-102 analogue. Covered by C5 and P2.

Out of scope as with the twins: date-ordering validation, a separate DTO layer.

## Carry the T-107 guard — added 2026-08-20, do not skip

`ClientSuppliedIds.reject(entity.getId())` must be the **first line** of this resource's `create()`, as it now is in person, experience and education ([T-107](T-107-post-id-cross-person-write.md), [cv-domain-service#6](https://github.com/erfeamor/cv-domain-service/pull/6)).

Without it, a POST body carrying an `id` makes Spring Data's `save()` take `merge()` instead of `persist()` and **overwrites that row**, reassigning it to the caller and answering `201` with the victim's id. Proven against live MySQL, not theorised. `id` looks un-bindable — private field, no setter — and Jackson binds it anyway.

T-107 chose a called guard over a structural `@JsonProperty(access = READ_ONLY)` deliberately, and this note is the price of that choice: the protection does not arrive by itself. **Include a test, and confirm it fails before the guard goes in** — the version of this that shipped in T-101 was a test asserting the *permissive* behaviour, which passed because it mocked `save()`.


> **Before stage-4 QA: the generated stack builds `master`, not your worktree** — see [T-028](T-028-qa-env-generator-worktree-build-context.md). Until that lands, add a build-context override pointing at your worktree, and *prove* which tree you built rather than assuming it.

## Acceptance criteria

- [ ] `GET/POST /api/v1/people/{personId}/projects`, `PUT/DELETE .../{id}` per contract.
- [ ] Unknown person → 404 on every verb; missing `name` → 400 (Spring's default problem body).
- [ ] **Only `name` is required** — no validation annotation on any other field.
- [ ] Payload matches the contract shape exactly; `endDate: null` serializes as JSON `null`.
- [ ] DoR rulings 1–6 each covered by a test.
- [ ] **Ordering (added 2026-08-13 by T-006, after this task's H1):** `GET` returns `startDate` **DESC** with **undated projects last**, tiebroken by `id` **ASC**, enforced in the repository query. This resource owns the contract's sharp edge — `start_date` is the only nullable one of the three date columns, so write the NULL placement explicitly (`ORDER BY start_date IS NULL, start_date DESC, id ASC`) rather than relying on MySQL sorting NULL lowest, **which disagrees with this rule**: NULL sorts lowest, so undated projects would come back *first*. This requires an `@Query` — Spring Data's derived method names cannot express an `IS NULL` sort key, so the `findByPersonIdOrderBy…` idiom the other section tasks use would compile, look correct, and order NULLs wrongly. Tests must cover a NULL-`startDate` row **and** a same-date tiebreak; a test with only dated rows would pass against either NULL convention and prove nothing.
- [ ] `@WebMvcTest(addFilters = false)` + `@DataJpaTest` coverage, both required.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Test plan (QA-authored at refinement; QA executes it verbatim at stage 4)

### `@WebMvcTest(addFilters = false)` — mocked `ProjectRepository` + `PersonRepository`

| # | Verb | Path | Precondition | Expected |
|---|---|---|---|---|
| C1 | GET | `/1/projects` | person 1 exists, repo returns 2 | 200, array size 2 |
| C2 | GET | `/1/projects` | repo returns `[]` | 200, empty array |
| C3 | POST | `/1/projects` | full valid body, `endDate: null` | 201, `$.id` present, `$.endDate` null |
| C4 | POST | `/1/projects` | missing `name` | 400 |
| C5 | POST | `/1/projects` | **only `name`** — other four omitted | 201, all four optionals serialize as `null` (DoR 6) |
| C6 | PUT | `/1/projects/5` | project 5 belongs to person 1 | 200, `$.id == 5`, fields updated |
| C7 | PUT | `/1/projects/5` | missing `name` | 400 |
| C8 | DELETE | `/1/projects/5` | project 5 belongs to person 1 | 204, empty body |
| C9–C12 | GET/POST/PUT/DELETE | `/999/projects[/5]` | person 999 absent | 404 |
| C13 | DELETE | `/1/projects/9999` | person exists, project absent | 404 (DoR 1) |
| C14 | PUT/DELETE | `/1/projects/5` | project 5 belongs to person **2** | 404, person 2's row untouched (DoR 2) |
| C15 | POST | `/1/projects` | `repoUrl: "not-a-url"` | **201** — confirms no format validation (DoR 5) |
| C16 | any | — | full response object | matches contract shape exactly |

### `@DataJpaTest`

| # | Case | Assertion |
|---|---|---|
| P1 | Save all fields, reload | round-trips; **`repoUrl` maps to `repo_url`** |
| P2 | Save with only `name` | other four reload as null; confirms `start_date`/`end_date` really are nullable here (unlike Experience/Education) |
| P3 | FK populated | `person_id` matches the persisted `Person` |
| P4 | Cascade delete | delete the person → project rows gone |
| P5 | Scoped lookup | `findByPersonId` returns only the requested person's rows |
| P6 | Required columns | null `name` rejected; **null `startDate` is NOT rejected** (contrast with T-101/T-102) |

### Exploratory QA at stage 4 — live MySQL 8.4, **env slot 3**

`python3 scripts/qa-env-override.py --task T-104 --slot 3`

- Real-schema check: `project` columns exactly `id, person_id, name, description, repo_url, start_date, end_date`; FK cascade; confirm `start_date`/`end_date` nullable in the **live** schema, not just assumed from the migration file.
- `repoUrl` round-trip over the wire (same naming-strategy risk class as T-102's `fieldOfStudy`).
- Name-only POST against the real DB: genuine SQL NULLs land, not empty strings, and no 500 from a NOT NULL the entity got wrong.
- `repoUrl: "not-a-url"` → 201 end-to-end, not just against the mock.
- Full CRUD round trip; `endDate: null` stays JSON `null`; cascade delete on the real InnoDB FK; unknown `personId` → 404; cross-person id → 404 with the victim row untouched; 400 returns Spring's default problem body.

### Coverage risks flagged up front

- **Primary risk:** copying T-101/T-102 too literally and adding `@NotNull`/`@NotBlank` to `startDate` or `description`. Projects genuinely has a more permissive required-field set — C5, C7 and P6 must be run, not waved through as "same as before".
- `repo_url` → `repoUrl` naming-strategy check.
- Scoped repository method for DoR 2.
- Watch for unrequested `repoUrl` format validation at review — it would narrow the contract without a contract change.
- ~~Client-supplied `"id": 999` in a POST body: flag, don't block, don't fix here.~~ **STRUCK 2026-08-20 — this instruction is wrong and it is the one that cost three weeks.** It is not an id override, it is an authenticated cross-person write, proven against live MySQL in [T-107](T-107-post-id-cross-person-write.md). **Block on it**: see §"Carry the T-107 guard" above, which is this file's binding instruction. Kept struck rather than deleted because the sentence itself is the artefact — it was believed by every reader of T-101 and T-102, including the one implementing against it.

## Definition of done

All acceptance criteria checked · A1 green · `/code-review` + QA coverage pass converged · PR open from `feat/project-resource`, **Jenkins CI green** · stage-4 QA clean on slot 3 · task `in_review` with the PR URL, `done` on merge.
