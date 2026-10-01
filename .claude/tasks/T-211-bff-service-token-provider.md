---
id: T-211
title: "BFF: call the domain service with a Cognito service token (client credentials, cached, fail-closed when configured)"
repo: cv-bff-node
status: in_review
owner: tech-product-owner
branch: feat/service-token
pr: https://github.com/erfeamor/cv-bff-node/pull/12
depends_on: []
risk: normal
security_review: true   # handles a client secret and an upstream credential — adapter §5 auth + secrets paths
checkpoint:
  stage: h2   # review round 1 clean; GitHub Actions green (test, docker); live proof is T-043's stage 4
  repo: cv-bff-node
  branch: feat/service-token
  worktree: none   # main cv-bff-node checkout
  commit: 2bad6bf
  pr: https://github.com/erfeamor/cv-bff-node/pull/12
  developer: fullstack-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live verification happens in T-043
  updated: 2026-10-01T15:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 58997
    spawns: 1   # fullstack-developer (fresh)
    status: ok   # human-reported /usage under ~40%
    checked: 2026-10-01T15:30:00+02:00
---

## Why

Split out of [T-043](T-043-bff-service-token-to-domain.md) at its H1 (2026-10-01). The deployed BFF's public routes answer 401/502 because `src/routes/people.ts` and `src/routes/cv.ts` call the domain service with no credentials, while the domain service in AWS requires a JWT (issuer-only validation). This task is the BFF code; T-043 provisions the Cognito client and deploys.

## H1 — decided by the human, 2026-10-01 (at T-043's H1)

1. **Client credentials against the pool's token endpoint** (`https://cv-project-dev.auth.eu-west-3.amazoncognito.com/oauth2/token`, HTTP Basic with the client id and secret, `grant_type=client_credentials`, the read scope). Configured by env: `COGNITO_TOKEN_URL`, `SERVICE_CLIENT_ID`, `SERVICE_CLIENT_SECRET`, `SERVICE_TOKEN_SCOPE` (final names at implementation; T-043 wires them).
2. **Cached until shortly before expiry** (Cognito returns `expires_in`; T-043 sets **24 h**, so ~30 token requests a month at $0.00225 each). One in-flight refresh at a time; concurrent callers share it.
3. **When configured, fail closed:** a token fetch failure → the upstream call isn't made → **502**. **When not configured** (the local dev stack, where the domain service runs with auth off): call without a token, exactly as today.
4. **`Authorization: Bearer <token>` on every upstream call** (the person route and all five aggregate calls).
5. **An upstream 401/403 becomes 502**, never passed through: with a service token, an upstream 401 means *our* credential failed, not the visitor's.
6. **The secret is never logged** (not in errors, not in metrics labels).

## Implement + review — 2026-10-01 (2bad6bf, cv-bff-node#12)

- Developer (fresh fullstack-developer, ~59k tokens): `src/service-token.ts` (factory + env config; cache with min(5 min, 10%) margin; one in-flight fetch; fixed-string `ServiceTokenError`), router factories injected via `createApp({ serviceToken })`, 401/403 → 502. 27 new tests, red first.
- Driver-verified: diff read; lint, typecheck, 117 tests, build green; **GitHub Actions green** (`test`, `docker`).
- **Review round 1 (driver, code + security): clean.** Non-blocking note: neither the token fetch nor the existing upstream fetches have a timeout (pre-existing; the endpoint is Cognito).
- Env var names for T-043 to wire: `COGNITO_TOKEN_URL`, `SERVICE_CLIENT_ID`, `SERVICE_CLIENT_SECRET`, `SERVICE_TOKEN_SCOPE`.

## Acceptance criteria

- [x] Unit tests (the token endpoint and the domain service mocked): first call fetches; second reuses the cache; refresh shortly before expiry; concurrent first calls share one fetch; token-endpoint failure → 502 and no upstream call; the header is on the person call and all five aggregate calls; not configured → no token and no token-endpoint call; upstream 401/403 → 502.
- [x] No log line, error body or metric contains the client secret or the token (a test asserts it on the failure path).
- [x] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` green; GitHub Actions green on the PR.
- [x] `/security-review` clean.
