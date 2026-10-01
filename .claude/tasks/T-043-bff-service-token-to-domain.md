---
id: T-043
title: "The deployed BFF can't read the domain service: its public routes call it with no credentials and get 401 — give the BFF a Cognito service token"
repo: cv-infra + cv-bff-node
status: todo
owner:
branch: feat/bff-service-token
pr:
depends_on: [T-014]
risk: high   # a new credential (client secret), a cross-repo change, and the public path's first live 200
security_review: true   # a new Cognito client + secret in SSM; the BFF holds a credential that can read the domain service — adapter §5 auth + secrets paths
---

## Why this exists

Found 2026-10-01 in [T-014](T-014-deploy-bff-to-aws.md)'s stage 4, against the live account. T-014 deployed the BFF correctly (the edge, its own SG, the container, the BFF's own auth all verified), but the contract's two **public** routes fail:

| Request (through CloudFront) | Result |
|---|---|
| `GET /bff/api/v1/people/1` | **401** `{"error":"upstream error"}` |
| `GET /bff/api/v1/people/1/cv` | **502** `{"error":"upstream error"}` |

The domain service in AWS runs `AUTH_ENABLED=true` and permits only `/actuator/health` anonymously (`SecurityConfig`, T-106). The BFF's public routes (`src/routes/people.ts`, `src/routes/cv.ts`) call it **with no `Authorization` header**. The contract (T-013) made the routes public *at the BFF* and never said how the BFF authenticates *upstream*; locally it works only because the dev stack runs the domain service with auth off.

## Decided by the human, 2026-10-01 (at T-014's H2)

**A Cognito service token (client credentials).** Rejected: trusting the docker subnet in the domain service (IP-based trust, fragile, NAT/proxy quirks); making domain GETs anonymous (they carry `email` and ids, which the contract bans from public payloads).

The domain service validates **only the issuer** (`spring.security.oauth2.resourceserver.jwt.issuer-uri`; no audience or client check), so a client-credentials token from the same pool is accepted **with no domain-service change**.

## Scope — split at stage 0 into dependency-ordered single-repo tasks (adapter §2)

1. **cv-infra:** an `aws_cognito_resource_server` (e.g. identifier `cv-domain`, scope `read`) and an `aws_cognito_user_pool_client` for the BFF with `generate_secret = true`, `allowed_oauth_flows = ["client_credentials"]`, and only that scope. The client id and secret go to SSM (`/cv-project/dev/bff/…`, SecureString for the secret). The BFF container gets them at boot (`param()` in `templates/domain-service-user-data.sh`, as the issuer is read), plus the token endpoint (the existing `aws_cognito_user_pool_domain`). Keep the user_data size guard green.
2. **cv-bff-node:** fetch a token from the Cognito token endpoint (client credentials, the scope above), **cache it until shortly before expiry**, and send `Authorization: Bearer …` on every upstream call (the public routes, and the protected ones if they don't already forward the caller's token — decide at stage 0 which wins). Fails closed: no token → the upstream call isn't made, 502. Unit tests with the token endpoint mocked: cache hit, refresh before expiry, token-endpoint failure → 502, the header is present on all five aggregate calls.
3. **Deploy:** push the new BFF image, apply (this replaces the app host again: user_data changes), verify.

## Acceptance criteria

- [ ] **(moved from T-014)** `GET /bff/api/v1/people/1` and `GET /bff/api/v1/people/1/cv` return **200 through the CloudFront domain**; `/cv` has all four sections in upstream order, and no `id`, `personId`, `skillId` or `email` in either payload.
- [ ] **(moved from T-014)** Memory measured under a burst on the **real** aggregate path (five upstream calls + MySQL per request): swap in/out, `/proc/pressure/memory`, `docker stats`. The numbers recorded here for [T-035](T-035-app-host-to-graviton.md).
- [ ] Protected BFF routes still answer 401 without a user token; the admin still works through `/api/*`.
- [ ] The client secret is only in SSM (never in a committed file, never printed); the Cognito client has **only** the client-credentials flow and the one read scope.
- [ ] The token is cached: one token request per expiry window, not per request (shown by test, and by the BFF's logs or metrics live).
- [ ] The Cognito pricing for machine clients and token requests is checked and recorded at H1 (expected: ~720 token requests a month with hourly caching).
- [ ] Offline gates in both repos green; `/security-review` clean.

## Watch-outs

- **Don't change `db_password`** during the apply (T-021).
- The domain service accepts **any** token from the pool (issuer-only). That's what makes this cheap, and also means the BFF's token could call write endpoints. Use a read-only scope anyway, and record the issuer-only validation as a known limit (a domain-side scope check would be its own task).
- [T-025](T-025-verify-requests-come-from-our-cloudfront.md) is scheduled after this, and also covers the BFF's `/metrics` on origin port 3000.
