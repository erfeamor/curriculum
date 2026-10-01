---
id: T-211
title: "BFF: call the domain service with a Cognito service token (client credentials, cached, fail-closed when configured)"
repo: cv-bff-node
status: in_progress
owner: tech-product-owner
branch: feat/service-token
pr:
depends_on: []
risk: normal
security_review: true   # handles a client secret and an upstream credential — adapter §5 auth + secrets paths
checkpoint:
  stage: implement   # split out of T-043 at its H1, 2026-10-01
  repo: cv-bff-node
  branch: feat/service-token
  worktree: none   # main cv-bff-node checkout
  commit:
  pr:
  developer: fullstack-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live verification happens in T-043
  updated: 2026-10-01T15:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
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

## Acceptance criteria

- [ ] Unit tests (the token endpoint and the domain service mocked): first call fetches; second reuses the cache; refresh shortly before expiry; concurrent first calls share one fetch; token-endpoint failure → 502 and no upstream call; the header is on the person call and all five aggregate calls; not configured → no token and no token-endpoint call; upstream 401/403 → 502.
- [ ] No log line, error body or metric contains the client secret or the token (a test asserts it on the failure path).
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` green; GitHub Actions green on the PR.
- [ ] `/security-review` clean.
