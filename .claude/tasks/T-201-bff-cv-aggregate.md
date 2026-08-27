---
id: T-201
title: "BFF: aggregated public CV endpoint"
repo: cv-bff-node
status: in_review
owner: fullstack-developer
branch: feat/cv-aggregate-endpoint
pr: https://github.com/erfeamor/cv-bff-node/pull/5
depends_on: [T-101, T-102, T-103, T-104, T-006]
risk: normal              # set at stage-0 refinement 2026-08-27; this task shipped without the key (board-check's UNREFINED_EXEMPT set)
security_review: true     # NOT an adapter §5 path match — see ruling 2. Set deliberately: an ANONYMOUS route that fans one caller-supplied path segment out into FIVE upstream URLs.
checkpoint:
  stage: H2                # Review round 1 closed (8/8 resolved) and exploratory QA PASSED. Awaiting the H2 human gate, then merge cv-bff-node#5.
  repo: cv-bff-node
  branch: feat/cv-aggregate-endpoint
  worktree: none
  commit: 759fb50          # 5a749d4 = initial, 759fb50 = review-round-1 fix (the Promise.all race)
  pr: https://github.com/erfeamor/cv-bff-node/pull/5
  developer: fullstack-developer
  reviewers: ["/code-review", "fullstack-developer", "/security-review"]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0          # 8 raised, 8 resolved in round 1
  qa_bounces: 0
  fix_attempts: 1
  env_slot: 0              # cvdl_t-201 -- BFF 3010, domain-service 8090, MySQL 3316
  updated: 2026-08-27
  h1: |
    RATIFIED 2026-08-27 by the account owner. All four questions took the recommended
    option: security_review stays true (ruling 2), the non-404 person failure is ruled 502
    here WITHOUT a contract PR (ruling 4), the id guard goes in a SHARED module with T-204
    left open (ruling 3), and the loop proceeds with a checkpoint if the budget goes SOFT.
  a1: |
    GREEN, run by the driver in cv-bff-node/: npm run lint clean, npm run typecheck clean,
    npm test 30/30 passed, npm run build clean. Diff is 5 files, +499/-5.
    Risk re-check per adapter §5: stays `normal`. The trivial fast-path was never claimed,
    so the >150-line/>5-file revocation rule does not apply.
    CORRECTED after review round 1: this block first recorded "No §5 security path is
    touched" as an executed re-check. That was ASSERTED, not checked -- the diff adds a
    file under src/middleware/ and edits test/auth-matrix.test.ts, and §5's auth bullet
    says "anything under auth filters/guards". The reading still stands (a path-parameter
    validator is not an auth filter; a test file is not a guard), but it is a judgement.
    Immaterial to the outcome: security_review: true either way, by ruling 2.
  ci: |
    GREEN 2026-08-27. Verified via the check-runs API, NOT `gh pr checks` -- run 33019874921
    on feat/cv-aggregate-endpoint: `test` completed/success, `docker` completed/success.
    (The statuses endpoint is empty for this repo: GitHub Actions reports check-runs, not
    commit statuses. The standing board caution is written against Jenkins' status-API
    behaviour and does not transfer verbatim to an Actions repo -- worth knowing before
    someone reads an empty statuses list here as "no CI ran".)
  code_review_result: |
    RAN 2026-08-27, /code-review at effort `high`. EIGHT findings, ALL RESOLVED. One is a
    real defect in the shipped code; the rest are board hygiene the driver introduced.

    SCOPING MISTAKE BY THE DRIVER, recorded because it nearly cost the finding: /code-review
    was invoked from the META repo, so it reviewed the BOARD diff (meta #73) and not the
    cv-bff-node code. It found the code bug anyway, by verifying the board's own file/line
    citations against the sibling repos. The right invocation targets the repo under review.

    F1 -- HIGH, A REAL BUG, fixed in 759fb50. `Promise.all` made the contract's
      "person 404 -> 404" a RACE. An unknown person id 404s ALL FIVE upstreams, because
      every section controller calls requirePerson() as the first line of findAll
      (ExperienceController:47 + three siblings -- verified). Promise.all rejects with
      whichever settles FIRST, so over a real network a section's 404 (mapped 502) could
      beat the person's and the route would answer 502 where the contract says 404.
      MY OWN TEST COULD NOT CATCH IT: synchronous mocks resolve in array order, so the
      person always won and the race was invisible -- the "green check that measures
      nothing" shape, in the very task whose parallelism criterion was struck for being
      unfalsifiable. Fixed with Promise.allSettled plus explicit precedence; new regression
      test forces the section 404s to land first and is PROVEN FALSIFIABLE (fails
      "Expected: 404, Received: 502" against the old code).
    F2 -- MEDIUM. status stayed `in_progress` with an empty `pr:` while the checkpoint
      recorded an open PR. Board rule 6 breach. board-check.py did NOT catch it: its
      missing-pr rule only fires on in_review/done. Fixed; worth a look at T-032.
    F3 -- MEDIUM. The deployment-chain prose still called T-201 `todo` and "claimable now".
      THIRD time that paragraph has gone stale about this task, and its own closing sentence
      warns about exactly this. Struck and corrected.
    F4 -- MEDIUM. Ruling 3's shared guard had NO board edge making T-204 land after it, so
      the duplicate implementation it exists to prevent was still reachable. T-201 added to
      T-204's depends_on, with a pointer section in that file and its board rows updated.
    F5 -- LOW/MED. TASKS.md row said "at H1" in the same commit that recorded review round 1.
    F6 -- LOW. Body read "PENDING H1" after the gate ran, and "four questions" did not
      account for five rulings. Now records that 2/3/4 were answered explicitly and 1/5 were
      ratified uncontested.
    F7 -- LOW. Ruling 2's "touches none of §5's paths" was asserted, not checked -- the diff
      adds a file under src/middleware/ and edits test/auth-matrix.test.ts. Reading still
      stands (a param validator is not an auth filter) but it is a judgement; corrected in
      both places. Immaterial to the outcome.
    F8 -- LOW. T-112's depends_on [T-110] may dangle if T-110 is absorbed into T-111 under
      its own recommended H1 option. Caveat added.
  ci_after_fix: |
    GREEN on 759fb50, verified via check-runs: `test` and `docker` both completed/success.
  security_review_result: |
    RAN 2026-08-27. NO HIGH OR MEDIUM FINDINGS. Run INLINE by the driver rather than fanned
    out to sub-tasks (budget guide: do not spawn for work the driver can do inline; 5-file
    diff, full context loaded, session at 70% of the turn ceiling). Same call as T-026's.
    Cleared, each by execution rather than assertion:
      - the id guard: /^[0-9]+$/ tested against 1\n, 1\r\n, " 1", +1, 1e3, 1%0a and
        Arabic-Indic digits -- all rejected. The trailing-newline bypass that would sink
        this in Python or Ruby does NOT apply: JS `$` without /m matches only end-of-input.
        Express decodes ..%2F..%2Fadmin AFTER segment matching, so traversal hits :id as one
        segment and is rejected. Both covered by tests that assert fetch was never called.
      - SSRF: host and scheme come from DOMAIN_SERVICE_URL (env, trusted); the param reaches
        the path only, and only as digits.
      - auth: mounting cvRouter adds NO public surface -- PUBLIC_ROUTES already listed the
        /cv regex (T-013/T-202) and matches on URL, not router.
      - person head: normalizePerson rebuilds field-by-field, so id and email cannot survive.
    RECORDED, NOT RAISED, and now FILED as T-205 on the human's instruction: the four
    SECTION normalizers are denylists (`...rest`) where every other normalizer in this repo
    is an allowlist. Not exploitable today (cv-domain-service @JsonIgnores the person
    relation), which is why it missed the >80%-exploitability bar -- but it makes that
    service's ENTITY SHAPE the BFF's public anonymous payload, enforced nowhere, and
    T-201's own no-leak test cannot catch it because it asserts against mocks built from
    the declared interface.
  qa_result: |
    PASSED 2026-08-27. Exploratory QA against the isolated stack (cvdl_t-201: BFF 3010,
    domain-service 8090, MySQL 3316), spawned read-only per the engine's "the writer writes"
    invariant -- which mattered here, since review round 1 had already proved the driver had
    a blind spot in this code. Stack torn down with `down -v` and confirmed gone.
    NO BLOCKING DEFECTS. What was actually exercised, so coverage is on the record:
      - THE T-205 QUESTION ANSWERED: key-set diff of /cv against the RAW domain-service
        responses on :8090, per section. Only `id` removed from experience/education/project,
        only `skillId` from skills; recursive scan of the whole payload for id/personId/
        skillId/email -> ZERO matches, on real Flyway-seeded data. NOT CURRENTLY LEAKING.
        Root cause established rather than assumed: every domain entity @JsonIgnores its
        person/identity fields, so the upstream JSON already equals the declared TS shape.
        T-205's exposure is therefore LATENT (a future domain-service field would pass
        straight through), not active -- which is what decides its urgency.
      - Contract shape field-for-field, including both naming traps (`education` singular
        against `/educations`; skills strip `skillId` not `id`).
      - Ordering compared programmatically against the same arrays fetched direct from
        :8090 -- identical in every section, undated "Dotfiles" project last.
      - THE F1 REGRESSION, under real concurrency: 15 sequential + 20 concurrent + 40-way
        parallel requests to an unknown person -> 75/75 returned 404, zero 502s. A race
        deserves more than one green run, and this is what that standard looks like.
      - The id guard: 1abc, 1;DROP, ..%2F..%2Fadmin, 1%20 -> all 400, and the NO-UPSTREAM-
        CALL property verified against the domain service's own logs rather than inferred.
        Empty segment -> 404 from Express's router before the handler. `01` -> 200, person 1.
      - A person created with no rows -> all four sections 200 [] (not 404), matching the
        controllers' "an existing person with no rows is an empty collection".
    ONE NEW FINDING, low severity, FILED AS T-206 and NOT fixed here (board rule 3): an
    over-long digit run passes /^[0-9]+$/, overflows Java Long upstream, and yields 502
    after five real upstream calls. QA's own classification -- not a T-201 defect, since the
    contract makes no promise there and the mapping is compliant. Filed because the guard's
    DOC COMMENT promises "must never reach an upstream URL" and five do; and because T-204
    adopts this exact guard.
    EXPLICITLY NOT COVERED, recorded rather than left implied:
      - auth (AUTH_ENABLED=false in the dev stack; covered by unit tests, and live only by
        T-014's stage-4).
      - a genuine mid-flight section 502 with the person succeeding -- needs fault injection,
        out of scope for a read-only pass. That path was read, not exercised.
      - the test assertions themselves; this was deliberately black-box.
  budget: |
    SOFT and DEEPENING. Probed 2026-08-27 after QA returned: turns 368/400 (92%), tokens
    73.7M/150M (49%), subagent_tokens 176,136, spawns 2 (/code-review, quality-assurance).
    Earlier probe, after review round 1: turns 338/400 (84.5%), tokens 63.1M, spawns 1.
    QA WAS RUN ON THE HUMAN'S EXPLICIT INSTRUCTION after the SOFT reading was reported --
    the guard's ask-before-a-new-stage step worked as designed rather than being skipped.
    NOTE WHICH CEILING BINDS: turns, at 92%, while tokens sit under half. That is why both
    remaining passes were SPAWNED rather than run inline -- a background agent costs the
    driver ~2 turns against ~20 for the same work inline, so spawning is the turn-efficient
    choice here, the opposite of the usual advice. Recorded because the budget guide's
    "do not spawn for what the driver can do" assumes tokens bind, and here they do not.
    Per references/budget.md a SOFT reading means FINISH THE STAGE, CHECKPOINT, then ASK
    before starting another. The stage is finished -- review round 1 is closed with zero
    open findings, the code fix is pushed and CI is green on it. The next stage (exploratory
    QA against a live compose stack) was deliberately NOT started.
    Spend history: this session drove T-026 to merge (apply + 4-step live verification),
    filed T-110/T-111/T-112/T-205, and ran four board syncs BEFORE claiming this task -- so
    T-201 inherited a budget already half spent. The one spawn was /code-review; the
    security review and the implementation were both run inline by the driver, per the
    budget guide's rule not to spawn for work the driver can do itself.
    STANDING CAVEAT: consumption against a SELF-IMPOSED ceiling, NOT a reading of remaining
    plan quota, which is not observable from inside a session. The adapter's second
    calibration point says ceiling_turns:400 trips roughly 20 points before real usage.
---

## Goal

`GET /bff/api/v1/people/:id/cv` returning the full normalized CV in one call, per [docs/api-contract.md](../../docs/api-contract.md) § BFF.

> **Path corrected 2026-08-13 by T-013.** This task originally specified `GET /api/v1/people/:id/cv`. T-013 moved the BFF's entire public surface behind the `/bff` edge prefix, because the BFF and the domain service would otherwise both claim `GET /api/v1/people/:id` at one CloudFront distribution. The BFF now mounts its routers at `/bff/api/v1` and the prefix is **not** stripped at the edge, so this is the real path in local dev as well as in AWS. T-202 makes the mount change; this task builds on top of it. Nothing else here changes — same payload, same error mapping, same parallel fetch.

> Unit-test development can start immediately against the contract (mock `global.fetch` exactly like `test/people.test.ts` does); only the final integration check needs T-101…T-104 merged.

> **This task now precedes [T-014](T-014-deploy-bff-to-aws.md) — added 2026-08-24 on the human's instruction.** T-014's `depends_on` gained this task, so **T-014 will not apply until this merges**. The reason is a step that was off the milestone's path: T-014's ruling 7 planned to deploy a BFF image that 404s `/cv`, and the task that would rebuild and roll the replacement container — [T-203](T-203-bff-ci-deploy-stage.md) — is **downstream of T-014** and **absent from [T-501](T-501-e2e-cv-milestone.md)'s `depends_on`** (the board calls it *"off the critical path"*). Landing this first means the first deployed image already serves the aggregate, and T-014's stage-4 verifies `/cv` live inside an apply it was already paying for.
>
> **What this asks of this task:** nothing extra in scope — but it is now **on the critical path of the deployment chain**, so a stall here stalls T-014, T-403, T-404 and T-501. All four of its upstreams (T-101…T-104) and T-006 are `done`, so it is claimable today.
>
> **No infra work belongs here.** The `/cv` path is already allowlisted at `src/middleware/auth.ts:53` and the edge behavior is path-prefix based, so this task ships route + tests only. If a live `/cv` returns **401** rather than 404 after T-014 applies, that is an allowlist-regex defect and T-014's problem, not a missing route here.

## Stage-0 refinement — 2026-08-27, rulings RATIFIED AT H1 the same day

This task was one of the five deliberately unrefined items (`board-check.py`'s `UNREFINED_EXEMPT`). Its body already carries the hard decisions — the edge path, the T-204 interaction, the struck parallelism criterion — so refinement settles what is genuinely open rather than restating them.

### Ruling 1 — new `src/routes/cv.ts`, not an addition to `people.ts`

The body offers both. **Take the sibling file.** `people.ts` is 47 lines with one upstream call and one normalizer; the aggregate adds five upstream calls, four section normalizers and four payload interfaces. Mounting is unchanged either way — `app.ts:30` already does `app.use(API_BASE_PATH, peopleRouter)` and a second `app.use(API_BASE_PATH, cvRouter)` sits beside it.

**This changes nothing about auth**, and that is worth stating because it looks like it might: the allowlist at `src/middleware/auth.ts:53` matches on the *URL* (`^${API_BASE_PATH}/people/[^/]+/cv/?$`), not on which router file serves it. `/cv` is already public regardless of this ruling.

### Ruling 2 — `security_review: true`, and it is NOT a path match

Adapter §5's forced paths are auth/identity, secrets/env, IAM/network, CI config. **This diff arguably touches none of them**, though the call is closer than first written — a review round pointed out that the delivered diff adds a file under `src/middleware/` and edits `test/auth-matrix.test.ts`, and §5's auth bullet reads *"anything under auth filters/guards"*. The guard is a path-parameter validator rather than an auth filter, and a test file is not a guard, so the reading here is that A1 does **not** fire — but it is a judgement, not the clean negative originally claimed. **The outcome is unaffected either way**, which is why this is recorded rather than re-litigated: `security_review: true` is set, deliberately, because:

- the route is **anonymous by contract** (T-013 ratified it; there is no token check in front of it),
- it takes one caller-supplied path segment and interpolates it into **five** upstream URLs,
- and the guard that should stop that ([T-204](T-204-bff-validate-person-id-param.md)) **has not merged** — confirmed against `cv-bff-node` HEAD `b63eae2` on 2026-08-27.

That is the SSRF/path-injection shape, on the one route with no authentication in front of it. Cheap to review, expensive to miss.

### Ruling 3 — validate the id in a SHARED helper, so T-204 adopts it rather than writing a second one

The body already rules that this task validates locally rather than waiting for T-204. Refinement adds *where*: a small shared module (e.g. `src/middleware/validate-person-id.ts`), not a private function inside `cv.ts`.

**Reason:** T-204 must apply the identical guard to `GET /people/:id`, and a private helper guarantees two implementations of one rule — which is how the defect got two instances in the first place. A shared helper leaves T-204 a one-line adoption. **This does not absorb T-204** (board rule 3): `/people/:id` stays unguarded when this merges, and T-204 stays open and still owns fixing it.

**Shape:** ids are `number` in the domain payloads (`DomainPerson.id`), and every contract path spells them `{id}`/`{personId}`. Reject anything not `/^[0-9]+$/` with **400**, **before any upstream call is made** — not after, or the fan-out has already happened.

### Ruling 4 — the contract is SILENT on a person fetch that fails with something other than 404; rule it 502

§ BFF Aggregate says *"Person 404 upstream → 404. Any section fetch failing → 502."* It does not say what a person fetch returning **500**, or timing out, should produce. The existing `/people/:id` route passes the upstream status straight through (`people.ts:38`), so copying it would leak a 500.

**Ruling: any person-fetch failure other than 404 → 502**, matching the sections and the contract's own stated reason — *"the public site treats the CV as one unit."* 404 stays 404.

**This is filling a silence, not overriding the contract**, so it does not trip board rule 4 and does not block. But it is a real gap: if H1 wants it written into `docs/api-contract.md`, that is a separate one-paragraph PR against § BFF, and this task should then cite it. **H1 decides whether to raise it; the implementation is the same either way.**

### Ruling 5 — the four upstream paths, resolved against the contract

Named here so they are not re-derived from memory mid-implementation. All are `${DOMAIN_SERVICE_URL}/api/v1/...` — the **domain service's** paths, which never carried the `/bff` prefix:

| Aggregate key | Upstream | Strip |
|---|---|---|
| `experiences` | `/people/{id}/experiences` | `id` |
| `education` | `/people/{id}/educations` | `id` |
| `skills` | `/people/{id}/skills` | `skillId` |
| `projects` | `/people/{id}/projects` | `id` |

**Two traps in that table.** The aggregate key is `education` (singular) while the upstream path is `/educations` (plural) — the contract spells both, differently, and a copy-paste that matches them will 404. And `skills` strips `skillId`, not `id`, because the assignments GET returns `{ skillId, name, category, proficiency }`.

## Definition of Ready — met

Upstreams `T-101`…`T-104` and `T-006` are all `done`; the contract section is ratified and amended (T-013, T-006, T-024); the repo is at `b63eae2` with T-202's mount in place; every open design question above is ruled on. ~~**Pending H1 ratification of rulings 1–5**~~ — **RATIFIED 2026-08-27.** Recorded precisely, because a review round caught this section still reading "pending" after the gate had run:

- **Rulings 2, 3 and 4 were put to the human as explicit questions** and all three took the recommended option.
- **Rulings 1 and 5 were presented in this refinement and not contested** — they are ratified by the gate passing, not by an individual answer. Ruling 1 (route file) and ruling 5 (the upstream path table) are both low-stakes and neither was flagged. Saying so beats letting a later reader count three answers against five rulings and wonder which two are still open.

## Pointers

- **cv-bff-node is now TypeScript** (strict, compiled to CommonJS via ts-jest/tsc) — write the route and tests in `.ts` and type the aggregate payload (extend the `DomainPerson`/`PublicPerson` pattern in `src/routes/people.ts` with per-section shapes).
- New route in `src/routes/people.ts` (or a sibling `cv.ts` mounted in `src/app.ts`).
- Fetch person + 4 section endpoints with `Promise.all` — no sequential awaits.
- Normalization strips `id`/`personId`/`skillId`/`email`; keep the existing `normalize()` for the person head and add per-section normalizers.
- Error mapping per contract: person 404 → 404, any section failure → 502.
- 🚨 **Validate `req.params.id` before interpolating it into any upstream URL — see [T-204](T-204-bff-validate-person-id-param.md) (added 2026-08-24).** T-204 predicted this task in its own body: *"T-201's aggregate route will interpolate the identical param — this should not have to be found twice."* That prediction lived only in T-204's file, so this task would have shipped the second instance of the defect before the first was fixed. This route makes it worse than the existing one, not better: it fans a single unvalidated param out into **five** upstream calls, and T-013 ratified it as **anonymous**, so there is no token check standing in front of it. If T-204 has merged by the time this is claimed, use its guard; if not, validate here and cross-reference — do **not** wait for it, and do **not** assume the framework normalizes the value for you.

## Acceptance criteria

- [ ] Response shape matches the contract example field-for-field (Jest asserts full body with mocked upstreams).
- [ ] No internal ids or email anywhere in the payload (explicit test).
- [ ] 404 and 502 paths covered by tests.
- [ ] ~~Upstream calls verifiably parallel (e.g. assert `fetch` call count, not ordering).~~ **WRONG — struck 2026-08-24. The suggested assertion cannot fail.** `fetch` is called five times whether the implementation uses `Promise.all` or five sequential `await`s; call count is identical under both, so this criterion is satisfiable by the very implementation the Pointers section forbids. It is the same shape as the four specification defects this board has already catalogued ([T-103](T-103-skills-catalog-and-assignments.md)'s `@Transactional` boundary, [T-104](T-104-project-resource.md)'s inherited "flag, don't block", [T-028](T-028-qa-env-generator-worktree-build-context.md)'s AC1, [T-152](T-152-mysql-84-parity-cv-database.md)'s `docker exec`) — a green check that measures nothing. **Replacement: prove the calls overlap in time.** Give each mocked upstream a manually-resolved promise, assert **all five fetches have been initiated before any of them resolves**, then resolve them. Sequential code fails this at the second fetch; `Promise.all` passes. A timing/duration assertion is *not* an acceptable substitute — it is flaky under CI load and passes for the wrong reason on a fast machine.
- [ ] **Order is passed through, not imposed (added 2026-08-13 by T-006):** every section array appears in the aggregate in exactly the order the domain service returned it. No `.sort()`, `.reverse()`, or re-keying anywhere in this route — ordering is settled in the contract's § Ordering and owned upstream, so sorting here creates a second answer. A test must feed deliberately out-of-natural-order mocked upstream arrays and assert the output order is byte-identical to the input.
- [ ] `npm test`, `npm run typecheck`, and `npm run lint` pass.

## Definition of done

PR open against `master` from `feat/cv-aggregate-endpoint`, CI green, task updated.
