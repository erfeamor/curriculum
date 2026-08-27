---
id: T-201
title: "BFF: aggregated public CV endpoint"
repo: cv-bff-node
status: in_progress
owner: fullstack-developer
branch: feat/cv-aggregate-endpoint
pr:
depends_on: [T-101, T-102, T-103, T-104, T-006]
risk: normal              # set at stage-0 refinement 2026-08-27; this task shipped without the key (board-check's UNREFINED_EXEMPT set)
security_review: true     # NOT an adapter §5 path match — see ruling 2. Set deliberately: an ANONYMOUS route that fans one caller-supplied path segment out into FIVE upstream URLs.
checkpoint:
  stage: review            # H1 RATIFIED, implemented, A1 green, PR open, repo CI green. Review round 1 in flight.
  repo: cv-bff-node
  branch: feat/cv-aggregate-endpoint
  worktree: none
  commit: 5a749d4
  pr: https://github.com/erfeamor/cv-bff-node/pull/5
  developer: fullstack-developer
  reviewers: ["/code-review", "fullstack-developer", "/security-review"]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
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
    so the >150-line/>5-file revocation rule does not apply. No §5 security path is touched
    -- security_review: true here is the H1 judgement (ruling 2), NOT a path match, and the
    task file says so rather than letting a later reader infer a rule that did not fire.
  ci: |
    GREEN 2026-08-27. Verified via the check-runs API, NOT `gh pr checks` -- run 33019874921
    on feat/cv-aggregate-endpoint: `test` completed/success, `docker` completed/success.
    (The statuses endpoint is empty for this repo: GitHub Actions reports check-runs, not
    commit statuses. The standing board caution is written against Jenkins' status-API
    behaviour and does not transfer verbatim to an Actions repo -- worth knowing before
    someone reads an empty statuses list here as "no CI ran".)
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
  budget: |
    Probed at claim time 2026-08-27: turns 217/400 (54%), tokens 28.7M/150M (19%), spawns 0,
    status OK. This session had already driven T-026 to merge plus three board syncs before
    claiming this, so the turn budget is HALF SPENT before stage 1 starts. The adapter prices
    a normal single-repo task at "2-3 spawns and well under half the turn ceiling" — that
    fits what remains, but with little slack for a second review round. If it goes SOFT,
    checkpoint at the round boundary rather than pushing through.
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

## Stage-0 refinement — 2026-08-27, rulings PENDING H1

This task was one of the five deliberately unrefined items (`board-check.py`'s `UNREFINED_EXEMPT`). Its body already carries the hard decisions — the edge path, the T-204 interaction, the struck parallelism criterion — so refinement settles what is genuinely open rather than restating them.

### Ruling 1 — new `src/routes/cv.ts`, not an addition to `people.ts`

The body offers both. **Take the sibling file.** `people.ts` is 47 lines with one upstream call and one normalizer; the aggregate adds five upstream calls, four section normalizers and four payload interfaces. Mounting is unchanged either way — `app.ts:30` already does `app.use(API_BASE_PATH, peopleRouter)` and a second `app.use(API_BASE_PATH, cvRouter)` sits beside it.

**This changes nothing about auth**, and that is worth stating because it looks like it might: the allowlist at `src/middleware/auth.ts:53` matches on the *URL* (`^${API_BASE_PATH}/people/[^/]+/cv/?$`), not on which router file serves it. `/cv` is already public regardless of this ruling.

### Ruling 2 — `security_review: true`, and it is NOT a path match

Adapter §5's forced paths are auth/identity, secrets/env, IAM/network, CI config. **This diff touches none of them** — it is a new route file and tests. So the honest position is that A1 will *not* force `/security-review` here, and it is being set at refinement instead, deliberately:

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

Upstreams `T-101`…`T-104` and `T-006` are all `done`; the contract section is ratified and amended (T-013, T-006, T-024); the repo is at `b63eae2` with T-202's mount in place; every open design question above is ruled on. **Pending H1 ratification of rulings 1–5, and of the `security_review: true` classification in particular, since it is a judgement rather than a rule match.**

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
