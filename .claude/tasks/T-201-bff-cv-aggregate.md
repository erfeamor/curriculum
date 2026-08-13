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

## Pointers

- **cv-bff-node is now TypeScript** (strict, compiled to CommonJS via ts-jest/tsc) — write the route and tests in `.ts` and type the aggregate payload (extend the `DomainPerson`/`PublicPerson` pattern in `src/routes/people.ts` with per-section shapes).
- New route in `src/routes/people.ts` (or a sibling `cv.ts` mounted in `src/app.ts`).
- Fetch person + 4 section endpoints with `Promise.all` — no sequential awaits.
- Normalization strips `id`/`personId`/`skillId`/`email`; keep the existing `normalize()` for the person head and add per-section normalizers.
- Error mapping per contract: person 404 → 404, any section failure → 502.

## Acceptance criteria

- [ ] Response shape matches the contract example field-for-field (Jest asserts full body with mocked upstreams).
- [ ] No internal ids or email anywhere in the payload (explicit test).
- [ ] 404 and 502 paths covered by tests.
- [ ] Upstream calls verifiably parallel (e.g. assert `fetch` call count, not ordering).
- [ ] `npm test`, `npm run typecheck`, and `npm run lint` pass.

## Definition of done

PR open against `master` from `feat/cv-aggregate-endpoint`, CI green, task updated.
