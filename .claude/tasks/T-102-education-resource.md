---
id: T-102
title: Education resource in the domain API
repo: cv-domain-service
status: done
owner: backend-developer
branch: feat/education-resource
pr: https://github.com/erfeamor/cv-domain-service/pull/5
depends_on: []
risk: normal
security_review: false   # promoted 2026-08-20: the value already existed at checkpoint.security_review and was missing at top level, where the board and the driver read it. Same shape as T-011's pr: bug. Value unchanged — this is not a new ruling.
checkpoint:
  stage: done               # merged as 42abe91 (cv-domain-service#5), 2026-08-20; implemented from the H1 checkpoint, as the reset_note directed
  a1: "mvn -B test 64 passed 0 failures (education adds 26) · mvn -B checkstyle:check 0 violations · mvn -B package -DskipTests clean"
  jenkins: "Three builds, all SUCCESS: #1 on the code commit (ac64985), #2 on the C7 tightening (b25ba628), #3 on the code-review fixes (cbe077f). Every commit on this branch was built green before merge."
  stage4: |
    RUN 2026-08-20 against live MySQL 8.4, slot 1 (ports +20: mysql 3326, domain-service 8100),
    per the task's own QA plan. 18 of 18 checks passed. Stack torn down with -v afterwards.
      - THE SERVICE BOOTED AT ALL, which is the headline: ddl-auto: validate against the real
        V1 schema means a field_of_study/fieldOfStudy mismatch would have failed startup.
      - real schema confirmed: id, person_id, institution, degree, field_of_study, start_date,
        end_date — exactly the plan's list
      - fieldOfStudy round-tripped over the wire AND read back from the physical column by SQL
      - ordering with two rows sharing a startDate: MIT,tied-a,tied-b,UNED == DESC then id ASC
      - cross-person PUT and DELETE both 404 with the victim row verifiably untouched (DoR 2)
      - unknown person 404, absent id DELETE 404 (DoR 1), missing institution 400
      - full CRUD round trip 201/200/200/204 with no leftover row
      - cascade delete against the real InnoDB FK: 4 rows -> 0
  stage4_finding: |
    Stage 4 found a defect in the UNIT TEST, not in the code — which is the argument for running
    it. C7 asserted jsonPath("$.fieldOfStudy").doesNotExist() for omitted optionals and passed.
    The live body is {"fieldOfStudy":null,...,"endDate":null} — the fields ARE present. jsonPath
    treats a JSON null as absent, so C7 was green for the wrong reason, and would have stayed
    green under @JsonInclude(NON_NULL), which WOULD break the contract's "absent optionals
    serialize as null". Tightened to assert key count plus a null value (commit b25ba628).
  code_review: |
    RUN 2026-08-20. One HIGH, two LOW. All three fixed in cbe077f rather than deferred.
    HIGH — the superseded item below was WRONG ABOUT ITS OWN IMPACT, which is why it had sat
    unfixed since refinement. A client-supplied id in a POST body is not an id override: it is an
    authenticated CROSS-PERSON WRITE. Jackson's INFER_PROPERTY_MUTATORS binds the private id
    despite there being no setter (verified empirically: getId() == 999), a non-null id makes
    save() take merge() instead of persist(), and create() has already set the owning person to
    the caller's — so the UPDATE reassigns another person's row to the caller and returns 201
    with the victim's id. Exactly the write findByIdAndPersonId scopes PUT and DELETE against,
    through the one verb with no row to scope to. Test confirmed RED (201 where 400 required)
    before the fix.
    LOW — no @Size(max = 150) against V1's VARCHAR(150): ddl-auto: validate does not check
    lengths and H2 builds varchar(255), so an over-long value passed every test and would fail on
    real MySQL with error 1406 as a 500, where design rule 4 requires 400. Fixed, tested at 151
    and at the 150 boundary.
    LOW — C8 asserted neither fieldOfStudy nor startDate, the two lines most easily dropped from
    the PUT copy block; the suite stayed green while PUT silently stopped replacing this
    aggregate's highest-risk field. Both now asserted.
  SUPERSEDED_flagged_not_fixed: "A client-supplied \"id\": 999 in a POST body is not rejected. PersonController.create and ExperienceController.create have the identical exposure — the test plan says flag, don't block, don't fix here. SUPERSEDED 2026-08-20 by the code review above: fixed here for education because the impact was understated; the person and experience instances are filed as T-107."

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
- ~~A client-supplied `"id": 999` in a POST body must not override the generated id. `PersonController.create` has the same exposure — flag, don't block, don't fix here.~~ **SUPERSEDED 2026-08-20** (the frontmatter has said so since the code review; the body bullet had not). The impact was understated: it is an authenticated cross-person write, not an id override. Fixed for education in this task; person and experience in [T-107](T-107-post-id-cross-person-write.md).

## Definition of done

All acceptance criteria checked · A1 green (`checkstyle:check`, `test`, `package -DskipTests`) · `/code-review` + QA coverage pass converged · PR open from `feat/education-resource`, **Jenkins CI green** · stage-4 QA clean on slot 1 · task `in_review` with the PR URL, `done` on merge.
