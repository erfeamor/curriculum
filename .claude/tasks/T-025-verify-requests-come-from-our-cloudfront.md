---
id: T-025
title: "The edge is not an authenticator: prove requests come from OUR CloudFront distribution"
repo: cv-infra + cv-domain-service
status: todo
owner:
branch: feat/origin-shared-secret-header
pr:
depends_on: [T-022]
risk: normal
security_review: true
---

## Why this exists

**Filed 2026-08-20 from [T-022](T-022-domain-service-origin-bypasses-cloudfront.md)'s forced `/security-review`** — the one MEDIUM finding it returned, dispositioned to its own task rather than folded into a PR whose acceptance criteria it exceeds (board rule 3, and T-022's own instruction not to reach across repos).

T-022 scoped port 8080 to `com.amazonaws.global.cloudfront.origin-facing`, which closed the direct-to-EIP path — verified by request. **But that prefix list is shared by every CloudFront customer.** It is the set of addresses CloudFront uses for origin fetches *globally*, not the addresses of distribution `E2AV0INGJW1UO2`. So the security group now authenticates *"some CloudFront distribution"*, not *"ours"*.

`frontend.tf`'s `domain-service-api` origin sends **no shared-secret header** (confirmed 2026-08-20: `custom_origin_config` carries only ports and protocol policy), and the origin validates nothing, so there is nothing downstream to catch the difference.

### The attack path, concretely

1. Attacker creates their own CloudFront distribution, origin `15.236.195.130`, `http_port = 8080`, `origin_protocol_policy = "http-only"`, caching off, all paths forwarded.
2. Requests through it leave from an origin-facing IP → **our security group allows them**.
3. `GET /v3/api-docs` returns **200 with the full springdoc document**, because the `403` on that path is a behaviour of *our* distribution, not a property of the origin.

The JWT-gated routes still return `401`, so this is information disclosure and edge-control bypass, **not** authenticated access. What it defeats is every control that lives at our edge: the `/v3/api-docs` 403, and any future WAF rule, header policy or behaviour-level restriction.

## Scope

**cv-infra** — add a `custom_header` to the `domain-service-api` origin in `frontend.tf`, value from SSM (`/cv-project/<env>/edge/origin-shared-secret`) per the repo's existing secrets flow. Never in a committed `.tf` or tfvars.

**cv-domain-service** — reject requests to non-public paths that lack the header. A servlet filter or the existing `SecurityConfig` chain, decided at refinement.

Two PRs, one per repo, and **the order matters**: ship the origin sending the header first, then enforce it. Enforcing first takes the live API down.

## Definition of Ready — settle before code

1. **What is "non-public" here?** The whole API is behind CloudFront today, so enforcing on everything is possible — but T-014 puts the BFF on this same box and it must keep reaching the domain service **container-to-container on the `cv` docker network**, which never traverses CloudFront. Decide whether the filter exempts in-network callers by source, by path, or by a second credential. **Getting this wrong breaks the BFF the day T-014 lands, and the failure is a 403 that looks like a bug in the BFF.**
2. **Rotation.** A shared secret that cannot be rotated is a secret that never will be. Say how a rotation happens without an outage — CloudFront supports multiple origins/headers, and the filter can accept two values during a window.
3. **Does this belong on port 3000 too?** Yes, and it is the same decision — see the T-014 note below. Decide whether this task covers both ports or only 8080, and say which.
4. **Is the header enough on its own?** It travels over **plain HTTP** edge-to-origin (`origin_protocol_policy = "http-only"`), so anyone who can observe that traffic can replay it. That is an accepted property of the current design, not something this task fixes — record it rather than discovering it in review.

## Acceptance criteria

- [ ] A request to `http://15.236.195.130:8080/v3/api-docs` **through a CloudFront distribution other than ours** is rejected — proven by actually standing one up, or by replaying the exact request without the header from an allowed source. Not by reading the config.
- [ ] The live admin UI still loads its people list with a real Cognito JWT.
- [ ] `/api/*` through our distribution is unaffected.
- [ ] The secret is in SSM, never in a committed file, and the rotation procedure is written down.
- [ ] `terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass, with an assertion that the origin carries the header.
- [ ] The Java side has tests for both branches: header present → served, header absent → rejected.

## Definition of done

Both PRs merged, in the order above, and the bypass demonstrated closed by request.

## dev-loop notes

- **Developers:** `infrastructure-engineer` (cv-infra half), `backend-developer` (cv-domain-service half). **Reviewers:** `/code-review` + `/security-review` (forced — this *is* an auth boundary).
- **Cheaper alternative worth pricing at H1:** [T-106](T-106-restrict-openapi-and-actuator-exposure.md) closes the *specific* disclosure for one property, with no shared secret and no cross-repo sequencing. It does **not** close the bypass class — every other edge control stays bypassable. If the demo's threat model only cares about the OpenAPI leak, T-106 alone may be the right answer and this task can be closed as "considered, declined, with reasons". Decide that at H1 rather than building both by default.
- **This is not a regression from T-022.** T-022 strictly narrowed an exposure that was `0.0.0.0/0`; this is the residual gap in the approach, which T-022's own body anticipated when it called springdoc hardening *"defence in depth, not the fix"*.
