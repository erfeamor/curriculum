---
id: T-102
title: Education resource in the domain API
repo: cv-domain-service
status: todo
owner:
branch: feat/education-resource
pr:
depends_on: []
risk: normal
checkpoint:
  stage: H1
  reset_note: "Claim reset 2026-08-09: status was in_progress with owner backend-developer, but NO implementation existed — worktree sat at master's tip (d78ef27) with 0 changed files and no remote branch. The stale claim blocked re-pickup under board rule 1 ('if owner: is already set, pick another task'), parking three of the five wave-1 tasks behind a status that was not true. NOTE this is NOT a fresh todo: stage H1 is real — refinement and the DoR/test plan in this file were completed and ratified, so whoever picks it up starts at implementation, not refinement. The local worktree and branch still exist and are reusable."
  repo: cv-domain-service
  branch: feat/education-resource
  worktree: /home/erfeamor/work/cvdl-worktrees/T-102
  pr:
  developer: backend-developer
  reviewers: [code-review, quality-assurance]
  risk: normal
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 1
  updated: 2026-08-04
---

## Goal

Person-scoped CRUD for education history per [docs/api-contract.md](../../docs/api-contract.md) § Education.

Path `/api/v1/people/{personId}/educations` — keep the awkward plural, it is the contract's choice. Required: `institution`, `degree`, `startDate`. Payload: `id, institution, degree, fieldOfStudy, startDate, endDate`.

## Pointers

- `education/` package mirroring `person/` (entity + `JpaRepository` + `@RestController`). Structural twin of T-101 — if T-101 has merged, follow its shape; otherwise both follow `person/` and reviewers reconcile.
- The `education` table exists in V1: `institution`, `degree`, `field_of_study`, `start_date`, `end_date`, FK `person_id` cascade. **No migration needed.**
- **Do not touch `SecurityConfig`** (`anyRequest().authenticated()` already covers the new endpoints).

## Definition of Ready — scope decisions

T-101's four ratified rulings apply **unchanged**; QA confirmed no contract basis to diverge. All three CRUD resources must behave identically:

1. DELETE of a nonexistent education id → **404** (not 204). Design rule 4.
2. PUT/DELETE of an id belonging to a different person → **404**, via a scoped `findByIdAndPersonId`. Not `findById` + a manual comparison — that is the IDOR failure mode.
3. GET collection for an existing person with zero rows → **200 `[]`**.
4. `personId` existence checked **before** the child lookup.
5. Out of scope (contract silence): `endDate`/`startDate` ordering validation; a DTO layer separate from the entity.

## Acceptance criteria

- [ ] `GET/POST /api/v1/people/{personId}/educations`, `PUT/DELETE .../{id}` per contract.
- [ ] Unknown person → 404 on every verb; missing `institution`/`degree`/`startDate` → 400 (Spring's default problem body).
- [ ] Payload matches the contract shape exactly; `endDate: null` serializes as JSON `null`.
- [ ] DoR rulings 1–4 each covered by a test.
- [ ] **Ordering (added 2026-08-13 by T-006, after this task's H1):** `GET` returns `startDate` **DESC**, tiebroken by `id` **ASC**, enforced in the repository query — not in the service, not in the controller. A test must assert the tiebreaker with two rows sharing a `startDate`; asserting only the date order passes on unordered data by luck.
- [ ] `@WebMvcTest(addFilters = false)` + `@DataJpaTest` coverage, both required.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Test plan (QA-authored at refinement; QA executes it verbatim at stage 4)

### `@WebMvcTest(addFilters = false)` — mocked `EducationRepository` + `PersonRepository`

| # | Verb | Path | Precondition | Expected |
|---|---|---|---|---|
| C1 | GET | `/1/educations` | person 1 exists, repo returns 2 | 200, array size 2 |
| C2 | GET | `/1/educations` | repo returns `[]` | 200, empty array |
| C3 | POST | `/1/educations` | valid body, `endDate: null` | 201, `$.id` present, `$.endDate` null |
| C4 | POST | `/1/educations` | missing `institution` | 400 |
| C5 | POST | `/1/educations` | missing `degree` | 400 |
| C6 | POST | `/1/educations` | missing `startDate` | 400 |
| C7 | POST | `/1/educations` | optional `fieldOfStudy`/`endDate` omitted | 201, absent optionals serialize as `null` |
| C8 | PUT | `/1/educations/5` | edu 5 belongs to person 1 | 200, `$.id == 5`, fields updated |
| C9 | PUT | `/1/educations/5` | missing a required field | 400 |
| C10 | DELETE | `/1/educations/5` | edu 5 belongs to person 1 | 204, empty body |
| C11–C14 | GET/POST/PUT/DELETE | `/999/educations[/5]` | person 999 absent | 404 |
| C15 | DELETE | `/1/educations/9999` | person exists, edu absent | 404 (DoR 1) |
| C16 | PUT/DELETE | `/1/educations/5` | edu 5 belongs to person **2** | 404, person 2's row untouched (DoR 2) |
| C17 | any | — | full response object | matches contract shape exactly |

### `@DataJpaTest`

| # | Case | Assertion |
|---|---|---|
| P1 | Save all fields, reload | round-trips; **`fieldOfStudy` maps to `field_of_study`**, `startDate`/`endDate` to `start_date`/`end_date` |
| P2 | `endDate` null | reloads null — plain SQL NULL, no sentinel |
| P3 | FK populated | `person_id` matches the persisted `Person` |
| P4 | Cascade delete | delete the person → education rows gone |
| P5 | Scoped lookup | two people's rows; `findByPersonId` returns only the requested person's |
| P6 | Required columns | null `institution`/`degree`/`startDate` rejected; note which layer catches it |

### Exploratory QA at stage 4 — live MySQL 8.4, **env slot 1**

`python3 scripts/qa-env-override.py --task T-102 --slot 1`

- Real-schema check: `education` columns exactly `id, person_id, institution, degree, field_of_study, start_date, end_date`; FK `fk_education_person ON DELETE CASCADE`.
- **`fieldOfStudy` round-trip over the wire against real MySQL** — POST with it set, GET it back; catches a naming-strategy mismatch H2 can mask.
- Full CRUD round trip: 201/200/200/200/204/200, no leftover row.
- `endDate: null` stays JSON `null`; cascade delete against the real InnoDB FK; unknown `personId` → 404 repo-backed; cross-person id → 404 with the victim row verifiably untouched; 400 returns Spring's default problem body.

### Coverage risks flagged up front

- `field_of_study` → `fieldOfStudy` is this resource's highest-risk naming-strategy spot — must be exercised by **both** P1 and the live-MySQL check.
- Scoped repository method for DoR 2; `person/` has no analogous ownership check to copy.
- A client-supplied `"id": 999` in a POST body must not override the generated id. `PersonController.create` has the same exposure — flag, don't block, don't fix here.

## Definition of done

All acceptance criteria checked · A1 green (`checkstyle:check`, `test`, `package -DskipTests`) · `/code-review` + QA coverage pass converged · PR open from `feat/education-resource`, **Jenkins CI green** · stage-4 QA clean on slot 1 · task `in_review` with the PR URL, `done` on merge.
