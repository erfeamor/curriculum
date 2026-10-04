---
id: T-116
title: "The domain service accepts any token from the pool for any method — make the BFF's read-only service token GET-only"
repo: cv-domain-service
status: todo
owner:
branch: fix/read-scope-get-only
pr:
depends_on: [T-043]
risk: normal
security_review: true   # authorization rules — adapter §5
---

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
