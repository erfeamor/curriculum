---
id: T-201
title: "BFF: aggregated public CV endpoint"
repo: cv-bff-node
status: todo
owner:
branch: feat/cv-aggregate-endpoint
pr:
depends_on: [T-101, T-102, T-103, T-104, T-006]
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
