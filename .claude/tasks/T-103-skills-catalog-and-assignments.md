---
id: T-103
title: Skill catalog + person-skill assignments
repo: cv-domain-service
status: todo
owner:
branch: feat/skills-resource
pr:
depends_on: []
risk: high
checkpoint:
  stage: H1
  reset_note: "Claim reset 2026-08-09: status was in_progress with owner backend-developer, but NO implementation existed — worktree sat at master's tip (d78ef27) with 0 changed files and no remote branch. The stale claim blocked re-pickup under board rule 1 ('if owner: is already set, pick another task'), parking three of the five wave-1 tasks behind a status that was not true. NOTE this is NOT a fresh todo: stage H1 is real — refinement and the DoR/test plan in this file were completed and ratified, so whoever picks it up starts at implementation, not refinement. The local worktree and branch still exist and are reusable."
  repo: cv-domain-service
  branch: feat/skills-resource
  worktree: /home/erfeamor/work/cvdl-worktrees/T-103
  pr:
  developer: backend-developer
  reviewers: [code-review, quality-assurance]
  risk: high
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 2
  updated: 2026-08-04
---

## Goal

Global skill catalog and person-scoped skill assignments per [docs/api-contract.md](../../docs/api-contract.md) § Skills. This is the one resource that is *not* purely nested.

**Highest-risk task in the wave** — composite key, upsert PUT, a 409 path, and two surfaces in one PR. Treat catalog and assignments as separate resources with separate 404 semantics; do not let "skills" as one mental model blur them. `/code-review` runs at raised effort here.

## Pointers

- Tables exist in V1 (**no migration needed**):
  - `skill (id, name VARCHAR(100) NOT NULL UNIQUE, category VARCHAR(100) NULL)`
  - `person_skill (person_id, skill_id, proficiency ENUM('BEGINNER','INTERMEDIATE','ADVANCED','EXPERT') NOT NULL DEFAULT 'INTERMEDIATE', PRIMARY KEY (person_id, skill_id))`, both FKs `ON DELETE CASCADE`.
- Composite key needs `@EmbeddedId` (or `@IdClass`); proficiency as a Java `enum` with `@Enumerated(EnumType.STRING)`.
- Duplicate catalog name → 409 by **catching `DataIntegrityViolationException`**, not by pre-checking — the requirement is race safety, and the test below is designed to tell the two apart.
- **Do not touch `SecurityConfig`.**

## Definition of Ready — scope decisions (PO-ratified at refinement)

1. **PUT on an assignment responds with the full joined shape** `{skillId, name, category, proficiency}` — the same shape GET returns, **not** a bare `{"proficiency": ...}` echo. The contract's Returns cell (`200, body { "proficiency": "ADVANCED" } — upsert`) is the only one in the document that shows a request body inline, and every other PUT in the contract returns "200, updated entity". A GET and a PUT on the identical resource returning different shapes would be an inconsistency no contract text asks for. **A follow-up docs PR clarifies this wording in `docs/api-contract.md`; it does not block this task.**
2. **PUT returns `200` on BOTH the create and the update branch.** The verb table lists a single status and no 201 variant (unlike POST, which is explicitly 201). These must be **two distinct test methods** — a single "PUT succeeds" test that exercises one branch is insufficient.
3. **Catalog required fields: `name` required (400 if missing/blank), `category` optional.** § Skills is the only section with no explicit "Required:" line; this is inferred from the migration's `NOT NULL`/nullable split.
4. **Unknown `skillId` on PUT/DELETE → 404** (Design rule 4, "unknown IDs return 404" — `skillId` is an id like any other).
5. **PUT where person and skill exist but no assignment links them → 200, creates the row.** That absence is exactly what "upsert" is for.
6. **DELETE where person and skill exist but no assignment links them → 404, not 204.** Design rule 4's 204 covers removing an *existing* resource; there is none at that pair. Mirrors T-101's ruling that DELETE of a nonexistent id is 404. **PUT and DELETE deliberately diverge on "absent" — this is the most likely place for an accidentally-idempotent DELETE.**
7. **The catalog is global — no person-scoping, no 404-on-person anywhere on `/api/v1/skills`** (Design rule 2). Its only failure modes are 400 and 409. A person-existence check on a catalog endpoint is a contract violation, not a missing case.
8. **Check order on assignments:** person existence → skill existence → (DELETE only) assignment existence. When more than one is absent, the person check wins, and the 404 body must not disclose which id missed.
9. **No `DELETE /api/v1/skills/{id}`** — the contract defines no catalog delete. Adding one is scope creep.

## Acceptance criteria

- [ ] `GET/POST /api/v1/skills`; POST duplicate name → **409 via the exception catch path**.
- [ ] `GET /api/v1/people/{personId}/skills` → 200, array of `{skillId, name, category, proficiency}` — no `id`, no `personId`, no nested skill object.
- [ ] `PUT /api/v1/people/{personId}/skills/{skillId}` upserts with body `{"proficiency": ...}`; 200 on both branches; invalid enum → 400; missing `proficiency` → 400.
- [ ] `DELETE` assignment → 204; unknown person or skill → 404; unlinked pair → 404.
- [ ] The upsert read-then-write is inside a single `@Transactional` boundary.
- [ ] DoR rulings 1–9 each covered by a test or verified at review.
- [ ] `@WebMvcTest(addFilters = false)` + `@DataJpaTest` coverage including the upsert path and the 409.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Test plan (QA-authored at refinement; QA executes it verbatim at stage 4)

### `@WebMvcTest(addFilters = false)` — catalog (mocked `SkillRepository`)

| # | Verb | Path | Precondition | Expected |
|---|---|---|---|---|
| SC1 | GET | `/api/v1/skills` | repo returns 3 | 200, array size 3, shape exactly `{id,name,category}` |
| SC2 | GET | `/api/v1/skills` | repo returns `[]` | 200, `[]` |
| SC3 | POST | `/api/v1/skills` | valid `{name,category}` | 201, `$.id` present |
| SC4 | POST | `/api/v1/skills` | missing `name` | 400 |
| SC5 | POST | `/api/v1/skills` | `category` omitted | 201, `$.category` null |
| **SC6** | POST | `/api/v1/skills` | **any pre-existence check reports "not found", and `save()` itself throws `DataIntegrityViolationException`** | **409** — see "the discriminating test" below |

### `@WebMvcTest(addFilters = false)` — assignments (mocked `Person`/`Skill`/`PersonSkill` repositories)

| # | Verb | Path | Precondition | Expected |
|---|---|---|---|---|
| SA1 | GET | `/1/skills` | person 1 exists, repo returns 2 | 200, shape exactly `{skillId,name,category,proficiency}` |
| SA2 | GET | `/1/skills` | zero assignments | 200, `[]` |
| SA3 | GET | `/999/skills` | person absent | 404 |
| SA4 | PUT | `/1/skills/5` | person + skill exist, **no existing assignment** | **200** (create branch, DoR 2/5), response = joined shape |
| SA5 | PUT | `/1/skills/5` | assignment exists as `BEGINNER`, body `ADVANCED` | **200** (update branch), `proficiency == ADVANCED`; asserts save is called with the *existing* composite id, not a second insert |
| SA6 | PUT | `/1/skills/5` | body `{"proficiency":"NOT_A_LEVEL"}` | 400 |
| SA7 | PUT | `/1/skills/5` | body missing `proficiency` | 400 |
| SA8 | PUT | `/999/skills/5` | person absent | 404 |
| SA9 | PUT | `/1/skills/999` | skill not in catalog | 404 (DoR 4) |
| SA10 | DELETE | `/1/skills/5` | assignment exists | 204, empty body |
| SA11 | DELETE | `/999/skills/5` | person absent | 404 |
| SA12 | DELETE | `/1/skills/999` | skill not in catalog | 404 |
| SA13 | DELETE | `/1/skills/5` | both exist, **no linking row** | **404** (DoR 6 — not 204) |
| SA14 | any | — | full response object, PUT and GET | field-for-field match; catches a leaked `personId` or nested skill object |

### The discriminating test (SC6) — the single highest-value test in this task

A naive "POST the same name twice" test passes **equally well** whether the implementation pre-checks or catches, because in a single-threaded test the pre-check also sees the duplicate. It therefore proves nothing about race safety.

SC6 instead reproduces what a real race looks like: the pre-check reports *not found* (leave `findByName` unstubbed or return `Optional.empty()`), and `save()` throws `DataIntegrityViolationException`. Only an implementation with a real `try/catch` around the write returns 409; a pre-check-only implementation lets the exception propagate as a 500. **Do not accept a simpler duplicate-POST test as a substitute.**

### `@DataJpaTest`

| # | Case | How it detects a wrong implementation |
|---|---|---|
| P1 | Composite key equals/hashCode | Save, `flush()` + `clear()`, then `findById(new PersonSkillId(1L, 5L))` with a **freshly constructed** id instance. If equals/hashCode is missing or identity-based, this returns empty despite the row existing — the classic silent failure. |
| P2 | Enum round-trip | Save one row per proficiency value; reload each and assert enum identity. **Also read the raw column** via native query and assert the string matches exactly — guards against `EnumType.ORDINAL` or renamed constants, which can pass on H2 but break on MySQL's real `ENUM`. |
| P3 | `skill.name` unique | Save "Java", `flush()`; save "Java" again, `flush()` → expect `DataIntegrityViolationException`. The explicit `flush()` is required or H2 may defer the check and produce a false pass. |
| P4 | Cascade on person delete | person_skill rows for that person gone; the **catalog skill row survives**. |
| P5 | Cascade on skill delete | person_skill rows for that skill gone across all people; the **people survive**. (No API deletes a skill — exercises the FK at the repository layer.) |
| P6 | Upsert updates in place | Two variants, **both required**: (a) load managed entity, mutate, save; (b) **construct a brand-new `PersonSkill` with the same composite id** and a different proficiency, call `save()` directly. Both assert row count for `(personId, skillId)` stays 1. (b) is what controller upsert code actually looks like — do not skip it in favor of (a). |
| P7 | Null proficiency | The DB has `DEFAULT 'INTERMEDIATE'`, but Hibernate sends an explicit value including `null` on insert and will **not** fall back to it. Assert this throws unless the entity itself defaults the field; record which layer is responsible. |

### Transaction boundary

`@WebMvcTest` mocks the repository, so it cannot observe transactionality — a missing `@Transactional` will not fail a mocked test even though the repo's review guidance names it. Coverage is therefore split:

- **Review lens (blocking):** the upsert is a check-then-act (read existing → conditional insert/update). Confirm it sits inside a single `@Transactional` boundary; two bare repository calls in the controller with no `@Transactional` in the chain is a blocking finding.
- **`@DataJpaTest` proxy:** P6(b) with an explicit `flush()` between find and save proves the sequential semantics.
- **Accepted gap:** true concurrent-upsert atomicity is not unit-testable. The live concurrent-POST probe below is the closest empirical signal, and it is not a guarantee. Logged as a known gap, not silently assumed away.

### Exploratory QA at stage 4 — live MySQL 8.4, **env slot 2**

`python3 scripts/qa-env-override.py --task T-103 --slot 2`

- **Real native `ENUM` column**, which H2 has no equivalent for and can mask: PUT all four proficiency values through the live API and read them back; confirm an invalid value is 400 against the real stack, not just the mock.
- **Real unique-constraint 409:** POST the same skill name twice over HTTP → 201 then 409, with no `flush()` caveat.
- **Concurrent duplicate POST — the race the catch-path design exists for:** fire two POSTs with the same new name in parallel. Assert **exactly one 201 and exactly one 409** — two 201s means the unique constraint isn't enforced; a 500 on the loser means the catch path isn't actually wired in the running config even though SC6 passed against a mock.
- Full assignment upsert round trip: PUT (create) → GET → PUT (update) → GET → DELETE → GET → 200/200/200/200/204/200, with no leftover row.
- Cascade delete against the real InnoDB FK in **both** directions (person → assignments; skill → assignments across all people).
- DELETE of an unlinked pair → 404 end-to-end (DoR 6).
- **Isolation sanity:** confirm this slot-2 stack's catalog is seed-only and not polluted by a wave sibling — a global, non-person-scoped resource is exactly what an isolation bug would leak across slots.

### Coverage risks flagged up front

- **SC6 is the highest-value test here.** A pre-check implementation passes everything else in this plan.
- **DoR 5 vs 6 (PUT creates, DELETE 404s on an absent link)** is easy to implement symmetrically by accident. Two distinct tests, not one inferred from the other.
- `category` optionality (DoR 3) is inferred from the migration, not stated in contract prose — it is a PO ruling, flagged as such.
- No concurrent-PUT-upsert probe is planned (only the catalog's concurrent POST). If stage 4 has room, add the analogous parallel-PUT probe; otherwise it stays a logged gap.

## Definition of done

All acceptance criteria checked · A1 green · `/code-review` at **raised effort** + QA coverage pass converged · PR open from `feat/skills-resource`, **Jenkins CI green** · stage-4 QA clean on slot 2 · task `in_review` with the PR URL, `done` on merge.
