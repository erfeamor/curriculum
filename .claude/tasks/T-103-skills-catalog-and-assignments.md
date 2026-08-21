---
id: T-103
title: Skill catalog + person-skill assignments
repo: cv-domain-service
status: done
owner: backend-developer
branch: feat/skills-resource
pr: https://github.com/erfeamor/cv-domain-service/pull/7
depends_on: []
risk: high
security_review: false   # promoted 2026-08-20: already at checkpoint.security_review, missing at top level where the board and the driver read it. Value unchanged, not a new ruling.
checkpoint:
  stage: done
  stage1: |
    Implemented 2026-08-20 on feat/skills-resource, worktree cvdl-worktrees/T-103,
    commit 9662745. 13 files: skill/ (Skill, SkillController, SkillRepository) and
    personskill/ (PersonSkill, PersonSkillId, PersonSkillRepository,
    PersonSkillController, Proficiency), plus 4 test classes.
    A1 GREEN, run by the driver: checkstyle 0 violations, 102 tests / 0 failures
    (37 new), package OK.
  stage1_incident: |
    The developer agent DIED mid-run (API connection lost) BEFORE reporting and
    before committing. The tree was complete and A1-green on disk. The driver
    verified the work independently rather than trusting a report it never got,
    then committed the tree (pipeline: committing an already-written tree is
    driver work, not a spawn). Nothing was re-implemented; one spawn consumed.
  stage1_verified_by_driver: |
    Claims the dead agent could not make were checked empirically instead:
      - T-107 GUARD RED-FIRST: PROVEN, not believed. Guard commented out ->
        rejectsAClientSuppliedIdInsteadOfMergingOverAnExistingCatalogRow fails
        "expected:<400> but was:<201>" (the exact vulnerability signature, and the
        only failure in the class); guard restored -> 9/9 green. This is the check
        T-101 skipped, and its test asserts verify(never()).save(any()) as well as
        the status -- the half T-101's version lacked.
      - SC6 IS THE CATCH-PATH VERSION: save() stubbed to throw
        DataIntegrityViolationException with no pre-check stubbed; expects 409.
        Not a duplicate-POST test.
      - DoR 5/6 asymmetry: two distinct tests, sa4 (PUT unlinked -> 200 creates)
        and sa13 (DELETE unlinked -> 404 not idempotent 204).
      - Ordering: explicit @Query with CASE WHEN category IS NULL THEN 1 ELSE 0
        (NULLs last) and ps.id.skillId as tiebreaker.
      - @Transactional on the upsert and the delete.
      - SkillControllerTest declares NO PersonRepository mock, so adding a
        person-check to the global catalog fails context startup (DoR 7 enforced
        structurally rather than by review vigilance).
  a1: "GREEN 2026-08-20 (driver-run): checkstyle:check 0, test 102/0/0, package OK. Risk re-check: high stands; diff touches no adapter-listed security path (no auth/secrets/IAM/CI, SecurityConfig untouched) so /security-review is NOT forced -- matches security_review: false."
  stage_history: "H1 ratified 2026-08-04 (refinement + DoR + test plan). Claimed at stage 1 on 2026-08-20 by /dev-loop, entering at implementation per reset_note -- refinement deliberately NOT re-run."
  premises_moved_since_H1: |
    Three things changed this task's inputs AFTER its H1 was ratified on 2026-08-04.
    All three are already written into the body; listed here so the developer does not
    have to infer which parts of a 16-day-old DoR still hold:
      1. T-024 merged 2026-08-20 -- DoR ruling 1 is now CONTRACT TEXT in
         docs/api-contract.md Sec.Skills. Build from the contract; the ruling is only
         the record of where it came from. Rulings 1, 2, 5, 6 are all contract now.
      2. T-107 merged 2026-08-20 -- ClientSuppliedIds.reject() must be the first line
         of the catalog create(). See "Carry the T-107 guard". Confirm the test is RED
         before the guard goes in.
      3. T-006 added the ordering criterion 2026-08-13, after H1. Two ordered
         collections, nullable category sorting NULLs-last against MySQL's default,
         and the tiebreaker is skillId not id.
  reset_note: "Claim reset 2026-08-09: status was in_progress with owner backend-developer, but NO implementation existed — worktree sat at master's tip (d78ef27) with 0 changed files and no remote branch. The stale claim blocked re-pickup under board rule 1 ('if owner: is already set, pick another task'), parking three of the five wave-1 tasks behind a status that was not true. NOTE this is NOT a fresh todo: stage H1 is real — refinement and the DoR/test plan in this file were completed and ratified, so whoever picks it up starts at implementation, not refinement. The local worktree and branch still exist and are reusable."
  repo: cv-domain-service
  branch: feat/skills-resource
  worktree: /home/erfeamor/work/cvdl-worktrees/T-103
  pr:
  developer: backend-developer
  reviewers: [code-review, quality-assurance]
  risk: high
  security_review: false
  review_round: 1
  review_round_1: |
    Two reviewers, converged, 2026-08-20.
    /code-review (high effort): 1 MEDIUM + 1 LOW. It booted the FULL app context
    (no test in this repo does) and drove the real endpoints, and decompiled
    Hibernate 6.5.2 to settle two claims empirically rather than by argument.
      MEDIUM (ACCEPTED AS BLOCKING by PO): the upsert create branch is not
        race-safe and its javadoc asserts that it is. 500 under a lost race where
        the contract mandates 200. See the struck acceptance criterion above.
      LOW: Skill.name @Column omits length=100 -> Hibernate renders varchar(255)
        against V1's VARCHAR(100). Does NOT fail ddl-auto: validate (verified:
        AbstractSchemaValidator compares type names only, never calls
        hasMatchingLength), so nothing misbehaves today; the cost is entity-derived
        DDL silently widening the column.
    quality-assurance (coverage lens): NO HIGH findings, ready for stage 3.
      All 37 tests map 1:1 onto SC1-SC6 / SA1-SA14 / P1-P7 + both ordering cases.
      Explicitly cleared of the two historical false-green patterns: the T-101
      mock-fabricates-the-response shape (controller tests use willAnswer passthrough)
      and the T-102 C7 doesNotExist()-on-a-JSON-null shape (category asserted with
      value(nullValue())).
      LOW: DoR 8's check order has no executable test.
    PO ruling on scope: the contract-prose defect the implementer found (the
    ordering note prescribes SQL for a JPQL context) is filed as T-027, NOT fixed
    in this PR (board rule 3). T-104 is its next victim.
  stage4: |
    CLEAN, 2026-08-21, live MySQL 8.4 on slot 2. ~90 requests, ZERO 500s anywhere.
    Every plan bullet PASS; no defects; no bounce-back to the developer.
      - Native ENUM: all four values round-trip; raw column read via
        SELECT proficiency, proficiency+0 -> EXPERT / ordinal 4, no drift.
        Invalid value -> 400 against the real stack.
      - Duplicate name over HTTP -> 201 then 409, no flush caveat.
      - CONCURRENT duplicate POST stressed to 8-way (plan asked 2): exactly one
        201, seven 409s, no 500, one row. The catch path is wired in the running
        config, not just against a mock.
      - Upsert round trip PUT/GET/PUT/GET/DELETE/GET all as specified.
      - Cascade both directions against the real InnoDB FK, verified with two
        people sharing one skill; catalog row survives person delete.
      - DELETE of a never-linked pair -> 404, not 204 (DoR 6).
      - ORDERING with two category=NULL rows: Backend -> Frontend -> Infra ->
        (Aaa-NoCategory, Zzz-NoCategory). NULLs LAST despite MySQL sorting NULL
        lowest, with name ASC holding inside the null group.
      - Isolation: every catalog row traced to seed or to this session. No
        cross-slot leakage in the one resource that would show it.
      - NEW PROBE (not in the original plan, added because the race fix postdates
        it): 10 parallel PUTs x 6 rounds on unlinked pairs -> 60/60 200s, exactly
        one row per pair, 54 recovered Duplicate entry violations in the log,
        zero escaped 500s. Independently reproduces the developer's 54 EXACTLY
        rather than accepting the reported number.
    Build provenance CONFIRMED: GET /api/v1/skills answered 200 on bring-up, and
    that endpoint does not exist on master at all -- proving the QA stack built
    from the worktree, not the main checkout.
    Stack torn down, volumes removed; verified independently by the driver.
  stage4_env_trap: |
    docker-compose.dev.yml builds domain-service from ./cv-domain-service, the MAIN
    CHECKOUT, which sits on master. Every worktree-based task is therefore invisible
    to the documented QA bring-up command: the stack would have built master, every
    skills endpoint would have 404'd, and the run would have reported a false failure
    -- or passed against the wrong binary. Worked around with a third compose file,
    docker-compose.override.cvdl_t-103.build.yml, repointing the build context at the
    worktree. THIS IS AN ADAPTER GAP (section 6 isolates ports and volumes but assumes
    the code under test lives in the main checkout) and it will hit T-104 and T-151
    identically. Folded into the next board sync.
  review_note_worth_keeping: |
    SC6 turned out to be stronger than the test plan asked for, and structurally so:
    SkillRepository has no findByName method AT ALL, so a pre-check implementation
    would not merely be untested -- it would not compile. Likewise SkillControllerTest
    declares no PersonRepository mock, so adding a person-existence check to the global
    catalog (a DoR 7 violation) fails context startup. Two rulings enforced by
    construction rather than by reviewer vigilance, which is the durable form.
  commit: 83c59ce
  merged: "2026-08-21 as 2e54394 (squash, PR #7). H2 accepted by the human. Worktree removed, branch deleted local+origin. M2 is now THREE of eleven."
  pr_opened: "2026-08-20, PR #7, after review round 1 converged. Two commits: 9662745 (implementation) + 83c59ce (race-recovery fix, @Column length, DoR 8 verifies)."
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 2
  updated: 2026-08-20
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

1. **PUT on an assignment responds with the full joined shape** `{skillId, name, category, proficiency}` — the same shape GET returns, **not** a bare `{"proficiency": ...}` echo. The contract's Returns cell (`200, body { "proficiency": "ADVANCED" } — upsert`) is the only one in the document that shows a request body inline, and every other PUT in the contract returns "200, updated entity". A GET and a PUT on the identical resource returning different shapes would be an inconsistency no contract text asks for. ~~**A follow-up docs PR clarifies this wording in `docs/api-contract.md`; it does not block this task.**~~ **DONE — [T-024](T-024-contract-skill-assignment-put-shape.md) landed 2026-08-20, so build from the contract, not from this ruling.** `docs/api-contract.md` § Skills now splits the assignment PUT's request body from its response in the table itself and states the semantics below it: response = the GET element shape `{ skillId, name, category, proficiency }`, `200` on both upsert branches with no `201`, and the deliberate PUT/DELETE divergence on an absent link. Rulings 1, 2, 5 and 6 of this DoR are now contract text. Where they and the contract ever disagree, **the contract wins** (board rule 4) — this ruling is kept only as the record of where the reasoning came from.
2. **PUT returns `200` on BOTH the create and the update branch.** The verb table lists a single status and no 201 variant (unlike POST, which is explicitly 201). These must be **two distinct test methods** — a single "PUT succeeds" test that exercises one branch is insufficient.
3. **Catalog required fields: `name` required (400 if missing/blank), `category` optional.** § Skills is the only section with no explicit "Required:" line; this is inferred from the migration's `NOT NULL`/nullable split.
4. **Unknown `skillId` on PUT/DELETE → 404** (Design rule 4, "unknown IDs return 404" — `skillId` is an id like any other).
5. **PUT where person and skill exist but no assignment links them → 200, creates the row.** That absence is exactly what "upsert" is for.
6. **DELETE where person and skill exist but no assignment links them → 404, not 204.** Design rule 4's 204 covers removing an *existing* resource; there is none at that pair. Mirrors T-101's ruling that DELETE of a nonexistent id is 404. **PUT and DELETE deliberately diverge on "absent" — this is the most likely place for an accidentally-idempotent DELETE.**
7. **The catalog is global — no person-scoping, no 404-on-person anywhere on `/api/v1/skills`** (Design rule 2). Its only failure modes are 400 and 409. A person-existence check on a catalog endpoint is a contract violation, not a missing case.
8. **Check order on assignments:** person existence → skill existence → (DELETE only) assignment existence. When more than one is absent, the person check wins, and the 404 body must not disclose which id missed.
9. **No `DELETE /api/v1/skills/{id}`** — the contract defines no catalog delete. Adding one is scope creep.

## Carry the T-107 guard — added 2026-08-20, do not skip

`ClientSuppliedIds.reject(entity.getId())` must be the **first line** of this resource's `create()`, as it now is in person, experience and education ([T-107](T-107-post-id-cross-person-write.md), [cv-domain-service#6](https://github.com/erfeamor/cv-domain-service/pull/6)).

Without it, a POST body carrying an `id` makes Spring Data's `save()` take `merge()` instead of `persist()` and **overwrites that row**, reassigning it to the caller and answering `201` with the victim's id. Proven against live MySQL, not theorised. `id` looks un-bindable — private field, no setter — and Jackson binds it anyway.

T-107 chose a called guard over a structural `@JsonProperty(access = READ_ONLY)` deliberately, and this note is the price of that choice: the protection does not arrive by itself. **Include a test, and confirm it fails before the guard goes in** — the version of this that shipped in T-101 was a test asserting the *permissive* behaviour, which passed because it mocked `save()`.

## Acceptance criteria

- [ ] `GET/POST /api/v1/skills`; POST duplicate name → **409 via the exception catch path**.
- [ ] `GET /api/v1/people/{personId}/skills` → 200, array of `{skillId, name, category, proficiency}` — no `id`, no `personId`, no nested skill object.
- [ ] `PUT /api/v1/people/{personId}/skills/{skillId}` upserts with body `{"proficiency": ...}`; 200 on both branches; invalid enum → 400; missing `proficiency` → 400.
- [ ] `DELETE` assignment → 204; unknown person or skill → 404; unlinked pair → 404.
- [ ] ~~The upsert read-then-write is inside a single `@Transactional` boundary.~~ **This criterion is NECESSARY BUT NOT SUFFICIENT, and stating it this way was a mistake — corrected 2026-08-20 at review round 1.** A single transaction does **not** serialize insert-if-absent: two concurrent PUTs on the same unlinked pair both read empty, both insert, and the loser dies on the composite PK. Because the id is pre-populated in the constructor, `save()` takes `merge()`, so the INSERT defers to **commit — after the handler returns** — and the `DataIntegrityViolationException` escapes as a **500** where the contract mandates 200 on both branches. The criterion is now: **the transaction is present AND the create branch recovers from a lost race** (catch + re-read), matching what `SkillController.create` already does for the identical hazard. The implementation satisfied the criterion as written while carrying the defect the criterion was meant to prevent — which is why it is struck rather than ticked.
- [ ] DoR rulings 1–9 each covered by a test or verified at review.
- [ ] **Ordering (added 2026-08-13 by T-006, after this task's H1):** both collections are ordered in their repository queries — the catalog `GET /api/v1/skills` by `name` ASC then `id` ASC (derived method is fine; `skill.name` is `NOT NULL UNIQUE`). The person assignments `GET .../people/{personId}/skills` by `category` ASC with **uncategorized last**, then `name` ASC, then **`skillId` ASC**. Two traps here, both found in T-006's review:
  - `skill.category` is **nullable**, and MySQL sorts NULL lowest — so the natural query puts uncategorized skills *first*, the opposite of the contract. Needs an explicit `@Query` (`ORDER BY category IS NULL, category ASC, name ASC, skill_id ASC`); a derived method name cannot express it.
  - The tiebreaker is **`skillId`, not `id`**. `person_skill` has a composite PK `(person_id, skill_id)` and no `id` column — `OrderBy…IdAsc` has nothing to bind to here.

  This is the one task with **two** ordered collections and no date to sort on; a test per collection asserting the full key sequence, and the assignments test must include a `category = NULL` row or it proves nothing.
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
