---
id: T-043
title: "The deployed BFF can't read the domain service: its public routes call it with no credentials and get 401 — give the BFF a Cognito service token"
repo: cv-infra   # narrowed at H1 2026-10-01: the BFF code is T-211
status: in_progress
owner: tech-product-owner
branch: feat/bff-service-token
pr:
depends_on: [T-014, T-211]
risk: high   # a new credential (client secret), a cross-repo change, and the public path's first live 200
security_review: true   # a new Cognito client + secret in SSM; the BFF holds a credential that can read the domain service — adapter §5 auth + secrets paths
checkpoint:
  stage: implement   # H1 decided 2026-10-01; T-211 merged; cv-infra developer running
  repo: cv-infra
  branch: feat/bff-service-token
  worktree: none   # main cv-infra checkout
  commit:
  pr:
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: high
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live app host
  updated: 2026-10-01T15:15:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage under ~40%
    checked: 2026-10-01T15:15:00+02:00
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

## H1 — decided by the human, 2026-10-01

Stage 0 facts: the pool is on the **Essentials** tier; its domain prefix is `cv-project-dev`, so the token endpoint is `https://cv-project-dev.auth.eu-west-3.amazoncognito.com/oauth2/token`. **Cognito charges $0.00225 per machine-token response, with no per-client charge** (pricing page, read 2026-10-01).

1. **Split:** [T-211](T-211-bff-service-token-provider.md) (cv-bff-node: the token provider, the header, upstream 401/403 → 502) first; **this task keeps the cv-infra half** plus the deploy and the live verification.
2. **Access-token validity: 24 hours** (`access_token_validity = 24`, `token_validity_units { access_token = "hours" }`): ~30 token requests a month, **~$0.07/month** (1 h would be ~730, ~$1.64/month).
3. **Write scoping is a follow-up:** [T-116](T-116-domain-service-scope-enforcement.md) makes the BFF's read-scoped token GET-only in the domain service. Not in this task.
4. **Budget:** `/usage` under ~40%: T-211 to merge, then this task through implementation and review; checkpoint before the apply unless there's clear room.

## Scope — split at H1 (2026-10-01): the BFF code is T-211; this task is items 1 and 3

1. **cv-infra:** an `aws_cognito_resource_server` (e.g. identifier `cv-domain`, scope `read`) and an `aws_cognito_user_pool_client` for the BFF with `generate_secret = true`, `allowed_oauth_flows = ["client_credentials"]`, and only that scope. The client id and secret go to SSM (`/cv-project/dev/bff/…`, SecureString for the secret). The BFF container gets them at boot (`param()` in `templates/domain-service-user-data.sh`, as the issuer is read), plus the token endpoint (the existing `aws_cognito_user_pool_domain`). Keep the user_data size guard green.
2. **cv-bff-node:** fetch a token from the Cognito token endpoint (client credentials, the scope above), **cache it until shortly before expiry**, and send `Authorization: Bearer …` on every upstream call (the public routes, and the protected ones if they don't already forward the caller's token — decide at stage 0 which wins). Fails closed: no token → the upstream call isn't made, 502. Unit tests with the token endpoint mocked: cache hit, refresh before expiry, token-endpoint failure → 502, the header is present on all five aggregate calls.
3. **Deploy:** push the new BFF image, apply (this replaces the app host again: user_data changes), verify.

## Acceptance criteria

- [ ] **(moved from T-014)** `GET /bff/api/v1/people/1` and `GET /bff/api/v1/people/1/cv` return **200 through the CloudFront domain**; `/cv` has all four sections in upstream order, and no `id`, `personId`, `skillId` or `email` in either payload.
- [ ] **(moved from T-014)** Memory measured under a burst on the **real** aggregate path (five upstream calls + MySQL per request): swap in/out, `/proc/pressure/memory`, `docker stats`. The numbers recorded here for [T-035](T-035-app-host-to-graviton.md).
- [ ] Protected BFF routes still answer 401 without a user token; the admin still works through `/api/*`.
- [ ] The client secret is only in SSM (never in a committed file, never printed); the Cognito client has **only** the client-credentials flow and the one read scope.
- [ ] The token is cached: one token request per expiry window, not per request (shown by test, and by the BFF's logs or metrics live).
- [x] The Cognito pricing for machine clients and token requests is checked and recorded at H1 *($0.00225 per token response, no per-client charge; 24 h validity → ~$0.07/month)*.
- [ ] Offline gates in both repos green; `/security-review` clean.

## Watch-outs

- **Don't change `db_password`** during the apply (T-021).
- The domain service accepts **any** token from the pool (issuer-only). That's what makes this cheap, and also means the BFF's token could call write endpoints. Use a read-only scope anyway, and record the issuer-only validation as a known limit (a domain-side scope check would be its own task).
- [T-025](T-025-verify-requests-come-from-our-cloudfront.md) is scheduled after this, and also covers the BFF's `/metrics` on origin port 3000.
