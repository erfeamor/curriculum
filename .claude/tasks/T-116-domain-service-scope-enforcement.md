---
id: T-116
title: "The domain service accepts any token from the pool for any method — make the BFF's read-only service token GET-only"
repo: cv-domain-service
status: in_review
owner: tech-product-owner
branch: fix/read-scope-get-only
pr: https://github.com/erfeamor/cv-domain-service/pull/16
depends_on: [T-043]
risk: normal
security_review: true   # authorization rules — adapter §5
checkpoint:
  stage: h2   # branch image live via cv-redeploy; machine token read-only proven; awaiting the human's admin-edit check + H2
  repo: cv-domain-service
  branch: fix/read-scope-get-only
  worktree: none
  commit: 9c989b0
  pr: https://github.com/erfeamor/cv-domain-service/pull/16
  developer: backend-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live via cv-redeploy domain-service
  updated: 2026-10-05T11:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 47142
    spawns: 1   # backend-developer (fresh)
    status: ok   # human-reported /usage under ~75%
    checked: 2026-10-05T11:30:00+02:00
---

## H1 — decided by the human, 2026-10-05

- **Stage-0 facts:** the admin sends a Cognito **user** access token (hosted-UI code flow; `scope` includes `openid email profile`). The BFF sends a **client-credentials** token whose scope is only `cv-domain/read`, and Cognito never grants `openid` to a client-credentials client. **Proven live on 2026-10-05:** the BFF's token could PUT (it was used for T-113's 409 test).
- **Rule (allowlist): POST/PUT/DELETE require the token's `scope` to contain `openid`; GET/HEAD/OPTIONS accept any pool token.** Every machine token (the BFF's, or any future client-credentials client) is therefore read-only by construction. A write without `openid` → **403**. `/actuator/health` stays anonymous. `AUTH_ENABLED=false` (local) is unchanged.
- **No infra change**: code only. Deploy: push the image, then `cv-redeploy domain-service` (T-044).
- **Live proof:** the BFF token → GET 200 and PUT **403**; the public CV still 200; the human confirms an admin edit still saves.

## Implement, review and live — 2026-10-05 (9c989b0, cv-domain-service#16)

- Developer (fresh backend-developer, ~47k tokens): POST/PUT/PATCH/DELETE → `hasAuthority("SCOPE_openid")`; other requests authenticated; health anonymous. **CSRF disabled** in the auth branch (unrequested; accepted at review: a stateless bearer API, and the resource server already skipped CSRF for bearer requests; the only effect was token-less writes getting 403 instead of 401). `WriteScopeEnforcementTest` (10) uses real Bearer headers with only `JwtDecoder` mocked, so the production converter decides. Red: machine-token writes got 201/200/204; no-token PUT got 403.
- Driver-verified: checkstyle 0, **237/237**; **Jenkins green**. **Review round 1 (code + security): clean.**
- **Live:** the T-113 image saved as a rollback (`domain-service-28b948d.tar.gz`); the branch image pushed and `cv-redeploy domain-service` (only that container). **With the BFF's token:** GET person and experiences 200; **PUT person (correct version) 403; POST project 403**; no-token PUT **401**; nothing written (version 1, person identical, projects 0). The public CV, `/` and `/admin/` are 200.
- Pending: the human confirms an admin edit still saves (a user token with `openid`).

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
