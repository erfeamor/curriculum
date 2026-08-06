---
id: T-101
title: Experience resource in the domain API
repo: cv-domain-service
status: in_review
owner: backend-developer
branch: feat/experience-resource
pr: https://github.com/erfeamor/cv-domain-service/pull/3
depends_on: []
risk: normal
checkpoint:
  stage: pr
  repo: cv-domain-service
  branch: feat/experience-resource
  commit: 3b22793
  worktree: /home/erfeamor/work/cvdl-worktrees/T-101
  pr: https://github.com/erfeamor/cv-domain-service/pull/3
  developer: backend-developer
  reviewers: [code-review, quality-assurance]
  risk: normal            # re-validated at A1 against the actual diff
  security_review: false  # no adapter-listed security path in the diff
  a1: pass                # checkstyle + 28 tests + package, all green 2026-08-04
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 0
  updated: 2026-08-04
---

## Goal

Person-scoped CRUD for work experience per [docs/api-contract.md](../../docs/api-contract.md) § Experience.

## Pointers

- Follow the existing package-by-feature pattern: mirror `src/main/java/com/erfeamor/cvdomain/person/` in a new `experience/` package (entity, `JpaRepository`, `@RestController`).
- The `experience` table already exists (V1 migration): columns map to `company`, `role`, `location`, `startDate`, `endDate`, `description`, FK `person_id` with cascade delete. **No cv-database migration is needed** — do not touch the schema.
- `ddl-auto: validate` runs against the real schema — entity column names must match the migration exactly (`start_date`, `end_date`, `person_id`).
- Reuse the 404 style from `PersonController` (`EntityNotFoundException` + local `@ExceptionHandler`).
- **Do not touch `SecurityConfig`.** It is `anyRequest().authenticated()` with no per-path rules, so the new endpoints are covered automatically. Adding a matcher would be a security-surface change and is out of scope.
- `role` is a MySQL keyword-adjacent identifier; if Hibernate's naming strategy trips on it, quote the `@Column`, do not rename the column.

## Definition of Ready — scope decisions (PO, ratified against the contract at refinement)

These were ambiguous in the original task prose. They are now **acceptance criteria**, each grounded in contract text:

1. **DELETE of a nonexistent experience id → `404`** (not 204). Design rule 4: "unknown IDs return 404" is generic, not scoped to `personId`. The verb table's 204 covers the *success* path only.
2. **PUT/DELETE of an experience id that exists but belongs to a different person than `{personId}` → `404`.** Design rule 1: section resources are person-scoped, so the resource's identity is the `(personId, id)` pair. Look it up with a scoped repository method (`findByIdAndPersonId`), **not** `findById` plus a manual comparison in the controller — a forgotten comparison is an IDOR.
3. **GET of the collection for an existing person with zero experiences → `200 []`** (not 404). The verb table's GET is unconditional; rule 1's 404 trigger is a nonexistent *person*, not an empty section.
4. **`personId` existence is checked before the child lookup**, so C13/C14 return 404 even when both ids are unknown, and the 404 body does not vary in a way that discloses which id missed.
5. **Out of scope for v1** (contract is silent — do not invent): any `endDate >= startDate` ordering validation; a DTO layer separate from the entity (`person/` binds the entity directly — same accepted tech debt).

## Acceptance criteria

- [ ] `GET/POST /api/v1/people/{personId}/experiences`, `PUT/DELETE .../{id}` with the status codes from the contract.
- [ ] `personId` is validated: unknown person → 404 on every verb.
- [ ] Bean validation: `company`, `role`, `startDate` required → 400 when missing (Spring's default problem body, no custom error DTO).
- [ ] Response payload matches the contract shape exactly: `id, company, role, location, startDate, endDate, description` — no extra or missing fields; `endDate: null` serializes as JSON `null`.
- [ ] DoR decisions 1–4 above each covered by a test.
- [ ] Tests in the established styles: `@WebMvcTest(addFilters = false)` controller tests (mocked repo) + `@DataJpaTest` persistence test. Both are required per aggregate.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Test plan (authored by Quality Assurance at refinement — QA executes this verbatim at stage 4)

### `@WebMvcTest(addFilters = false)` — mocked `ExperienceRepository` + `PersonRepository`

| # | Verb | Path | Precondition | Expected |
|---|---|---|---|---|
| C1 | GET | `/1/experiences` | person 1 exists, repo returns 2 | 200, array size 2 |
| C2 | GET | `/1/experiences` | person 1 exists, repo returns `[]` | 200, empty array |
| C3 | POST | `/1/experiences` | valid body, `endDate: null` | 201, `$.id` present, `$.endDate` null |
| C4 | POST | `/1/experiences` | body missing `company` | 400 |
| C5 | POST | `/1/experiences` | body missing `role` | 400 |
| C6 | POST | `/1/experiences` | body missing `startDate` | 400 |
| C7 | POST | `/1/experiences` | optional `endDate`/`location`/`description` omitted | 201, absent optionals serialize as `null` |
| C8 | PUT | `/1/experiences/5` | exp 5 belongs to person 1, valid body | 200, `$.id == 5`, fields updated |
| C9 | PUT | `/1/experiences/5` | body missing a required field | 400 |
| C10 | DELETE | `/1/experiences/5` | exp 5 belongs to person 1 | 204, empty body |
| C11 | GET | `/999/experiences` | person 999 absent | 404 |
| C12 | POST | `/999/experiences` | person 999 absent | 404 |
| C13 | PUT | `/999/experiences/5` | person 999 absent | 404 |
| C14 | DELETE | `/999/experiences/5` | person 999 absent | 404 |
| C15 | DELETE | `/1/experiences/9999` | person 1 exists, exp 9999 absent | 404 (DoR 1) |
| C16 | PUT/DELETE | `/1/experiences/5` | exp 5 belongs to person **2** | 404, and person 2's row is untouched (DoR 2) |
| C17 | any | — | full response object | matches contract shape exactly |

### `@DataJpaTest` — persistence

| # | Case | Assertion |
|---|---|---|
| P1 | Save all fields, reload by id | round-trips; `startDate`/`endDate` map to `start_date`/`end_date` |
| P2 | Save with `endDate` null | reloads null — "current" is plain SQL NULL, no sentinel |
| P3 | FK populated | `person_id` matches the persisted `Person` |
| P4 | Cascade delete | delete the person → experience rows gone |
| P5 | Scoped lookup | two people's rows; `findByPersonId` returns only the requested person's |
| P6 | Required columns | null `company`/`role`/`startDate` rejected; note which layer catches it |

### Exploratory QA at stage 4 — live isolated stack (real MySQL 8.4, **not** H2)

Bring up with `python3 scripts/qa-env-override.py --task T-101 --slot 0`.

- Real-schema validation: `experience` columns exactly `id, person_id, company, role, location, start_date, end_date, description`, FK `fk_experience_person ON DELETE CASCADE` — catches an entity mapping that passes H2 but fails `ddl-auto: validate` on MySQL.
- Full CRUD round trip against the seeded person: POST → GET → PUT → GET → DELETE → GET; 201/200/200/200/204/200, no leftover row.
- Date serialization over the wire: `"endDate": null` stays JSON `null`, not `"null"`, not omitted.
- Cascade delete against the real InnoDB FK (H2's emulation can diverge from P4).
- Unknown `personId` → 404 against the real repo-backed check, not just the mock.
- Cross-person id (DoR 2) → 404, and the victim row is verifiably untouched afterward.
- Validation 400 returns Spring's default problem body — no custom error DTO snuck in.

### Coverage risks flagged to the developer up front

- Use a scoped repository method for DoR 2; a `findById` + manual check is the IDOR failure mode. This is a **review lens**, not just a test — `person/` has no analogous ownership check to copy.
- Check `personId` existence **before** the child lookup (C13/C14).
- Confirm a client-supplied `"id": 999` in a POST body cannot override the generated id. `PersonController.create` has the same exposure today — flag it, do not block on it, and do not fix it here.

## Definition of done

- All acceptance criteria checked.
- A1 green: `mvn -B checkstyle:check`, `mvn -B test`, `mvn -B package -DskipTests` from `cv-domain-service/`.
- `/code-review` + QA coverage pass converged (no blocking findings).
- PR open against `master` from `feat/experience-resource`, **Jenkins CI green**.
- Stage-4 exploratory QA clean against the isolated MySQL 8.4 stack.
- Task file `in_review` with the PR URL; `done` on merge.

## Review trail — round 1 (2026-08-04) · CONVERGED, 0 blocking

Two read-only passes on commit `3b22793`: a general correctness pass and QA's coverage pass. Both returned **0 blocking findings**, so no developer reconciliation and no PO sign-off on a rejected blocker was required. Non-blocking findings are logged here, not gating.

**Verified in the lookup path, not merely by green tests:** `requireExperience` calls only `findByIdAndPersonId`; the controller never calls `findById`; `requirePerson` precedes every child lookup. QA confirmed `verify(never()).findById(any())` is load-bearing — Mockito returns `Optional.empty()` for unstubbed calls, so an IDOR-vulnerable rewrite using `findById` would still 404 by accident and *only* that negative assertion catches it.

**Both PO calls resolved as "keep":**
- `@ManyToOne … @OnDelete @JsonIgnore Person` — inert under `ddl-auto: validate` (Hibernate validates tables/columns/types, never FKs), and it is what makes P4 non-vacuous. `LAZY` and `@JsonIgnore` are **load-bearing together** given `open-in-view: false`; dropping either yields N+1 or a `LazyInitializationException` 500. `@JsonIgnore` holds in both directions, so a `"person"` key in a request body is discarded, not bound.
- Uniform `"Experience not found"` — the uniformity *is* the security property for the cross-person case; a differentiated message would confirm the id exists under some other person.

**Non-blocking findings carried forward:**

1. **`description` is `TEXT` in V1 but Hibernate infers `VARCHAR(255)`.** The unit suite runs `create-drop`, never `validate`, so a JDBC type mismatch cannot surface here. **This is the most likely stage-4 failure** — probe column *types*, not just names, when the MySQL 8.4 stack is up.
2. **The detached-entity path is untested.** `open-in-view: false` means PUT/DELETE operate on a detached entity holding an uninitialized `Person` proxy; `@DataJpaTest` never detaches and `@WebMvcTest` mocks the repo. Stage 4 must exercise **PUT and DELETE**, not just POST/GET.
3. **P4 proves H2's generated FK, not MySQL's** — `@OnDelete` is DDL-export-only. The real-InnoDB cascade check at stage 4 is the one that counts.
4. `findByPersonId` returns **unordered** rows → the BFF aggregate would render experiences in undefined order. Contract is silent; DoR 5 forbids inventing. **Needs a contract PR (`ORDER BY start_date DESC`), not a code change here** — affects T-201, T-401, T-402.
5. 400 tests assert status only, not Spring's default problem-body shape; a custom error DTO added later would not fail the suite.
6. `@Valid` runs before the person check, so a malformed body against an unknown person yields 400 rather than 404. No disclosure (400 either way); contract does not order the two.
7. `requirePerson` in PUT/DELETE is behaviorally redundant given the uniform 404 (one extra SELECT per write) but is mandated by DoR 4 and asserted by C13/C14 — **do not remove**. Noted so nobody mistakes the pre-check for the guarantee; the scoped lookup is.
8. `person` exclusion is tested for serialization but not deserialization; the javadoc at `ExperienceController.java:29-33` overclaims (person existence stays observable via `GET /api/v1/people/{id}`).
