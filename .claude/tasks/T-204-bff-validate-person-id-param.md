---
id: T-204
title: "BFF: validate the person id before interpolating it into the upstream URL"
repo: cv-bff-node
status: todo
owner:
branch: fix/validate-person-id-param
pr:
depends_on: [T-202]
risk: normal
security_review: true
---

## Why this exists

Found by the forced security review on **T-202** (2026-08-13). The bug is **pre-existing on `master`** and T-202 did not introduce it — but T-202 changes who can reach it, which is why it is filed now rather than left in a review comment.

`src/routes/people.ts:36` interpolates the route param straight into the upstream URL:

```ts
const response = await fetch(`${DOMAIN_SERVICE_URL}/api/v1/people/${req.params.id}`);
```

`req.params.id` is unvalidated and **percent-decoded by Express before it lands there**. A caller can therefore put path syntax into the upstream request — `id = ".."` traverses, `id = "1%2Fsomething"` decodes to a literal `/` inside the segment — and steer the BFF's call to a different upstream path than the one intended.

### What actually changed, and why that is the whole point

| | before T-202 | after T-202 |
|---|---|---|
| Path | `/api/v1/people/:id` | `/bff/api/v1/people/:id` |
| Reachable with `AUTH_ENABLED=true` | only with a valid Cognito JWT | **anonymously — it is on the public allowlist** |

The defect is identical; the population that can reach it is not. This route is now one of exactly two the contract makes public, so it goes on the internet with no token in front of it the moment T-014 deploys the BFF.

**Why it was not a T-202 blocker.** `normalize()` (`src/routes/people.ts:25-32`) is a strict four-key allowlist — `name`, `headline`, `location`, `summary` — so arbitrary upstream JSON is not echoed back to the caller, which bounds the practical blast radius to what an attacker can infer from status codes and those four fields. Fixing it inside T-202 would also have violated board rule 3 (acceptance criteria are the scope). It is a real finding, correctly deferred, not waved away.

## Scope

`cv-bff-node` only. `src/routes/people.ts`, and the same treatment for any sibling route that interpolates a param into an upstream URL.

- Validate `id` before use. It is a domain-service `BIGINT` primary key, so the accepting shape is a positive integer — reject anything else with **400** rather than passing it upstream.
- Do not rely on `encodeURIComponent` alone. It stops the traversal but still forwards nonsense to the domain service and turns a client error into a confusing upstream 404; validate first, then encode.
- Decide and record whether the same guard belongs in a shared helper — T-201's aggregate route will interpolate the identical param, and this should not have to be found twice.

## Acceptance criteria

- [ ] A non-numeric `id` returns **400** from the BFF and makes **no upstream call** (assert `fetch` was not called — a test that only checks the status would pass against a fixed-but-still-calling implementation).
- [ ] Traversal and encoded-separator inputs are covered explicitly by tests: at minimum `..`, `1%2Fadmin`, and a negative number.
- [ ] A valid numeric id behaves exactly as today — existing `people.test.ts` assertions unchanged.
- [ ] The public/gated auth matrix from T-202 (`test/auth-matrix.test.ts`) still passes untouched.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass; GitHub Actions green.

## Definition of done

PR open against `master` from `fix/validate-person-id-param`, CI green, merged.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2). **Reviewers:** `/code-review` + `infrastructure-engineer` for the security lens.
- **`security_review: true`** — it is an input-validation fix on an internet-facing, pre-auth route.
- **Sequencing:** `depends_on: [T-202]`, which moves the route and puts it on the public allowlist. It does **not** block T-014 — the deployment can proceed without it — but it *should* land before the BFF is genuinely public-facing for long. If T-014 is imminent, do this first; the fix is small and the window is the entire time the route is anonymous and unvalidated.
