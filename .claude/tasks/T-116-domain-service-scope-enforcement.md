---
id: T-116
title: "The domain service accepts any token from the pool for any method — make the BFF's read-only service token GET-only"
repo: cv-domain-service
status: in_progress
owner: tech-product-owner
branch: fix/read-scope-get-only
pr:
depends_on: [T-043]
risk: normal
security_review: true   # authorization rules — adapter §5
checkpoint:
  stage: implement   # H1 decided 2026-10-05
  repo: cv-domain-service
  branch: fix/read-scope-get-only
  worktree: none
  commit:
  pr:
  developer: backend-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live via cv-redeploy domain-service
  updated: 2026-10-05T11:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage under ~75%
    checked: 2026-10-05T11:30:00+02:00
---

## H1 — decided by the human, 2026-10-05

- **Stage-0 facts:** the admin sends a Cognito **user** access token (hosted-UI code flow; `scope` includes `openid email profile`). The BFF sends a **client-credentials** token whose scope is only `cv-domain/read`, and Cognito never grants `openid` to a client-credentials client. **Proven live on 2026-10-05:** the BFF's token could PUT (it was used for T-113's 409 test).
- **Rule (allowlist): POST/PUT/DELETE require the token's `scope` to contain `openid`; GET/HEAD/OPTIONS accept any pool token.** Every machine token (the BFF's, or any future client-credentials client) is therefore read-only by construction. A write without `openid` → **403**. `/actuator/health` stays anonymous. `AUTH_ENABLED=false` (local) is unchanged.
- **No infra change**: code only. Deploy: push the image, then `cv-redeploy domain-service` (T-044).
- **Live proof:** the BFF token → GET 200 and PUT **403**; the public CV still 200; the human confirms an admin edit still saves.

## Why

Filed 2026-10-01 at [T-043](T-043-bff-service-token-to-domain.md)'s H1 (the human's decision: a follow-up, not in T-043). The domain service's resource server validates **only the issuer** (`spring.security.oauth2.resourceserver.jwt.issuer-uri`; `SecurityConfig`: `anyRequest().authenticated()`). So once T-043 gives the BFF a client-credentials token with a read scope, that token can still call `POST`/`PUT`/`DELETE`. It only matters if the BFF itself is compromised, but then it's a write path into the database.

## Scope

- Requests whose token carries the BFF's read scope (or its `client_id`) are **GET-only**: any other method → 403. Admin (user) tokens are unaffected.
- Tests for both branches (read-scoped token: GET 200, PUT 403; user token: PUT still allowed).
- Deploy: **batched with [T-113](T-113-optimistic-locking-lost-update.md)** into one domain-service image, rolled with [T-044](T-044-app-host-bootstrap-s3-and-redeploy.md)'s `cv-redeploy domain-service` (board review 2026-10-04). Manual until T-112.

## Acceptance criteria

- [ ] A read-scoped service token gets 403 on every non-GET; a user token still writes.
- [ ] Verified live after deploy (the BFF's public routes still 200).
- [ ] `mvn -B checkstyle:check`, `mvn -B test` green; `/security-review` clean.
