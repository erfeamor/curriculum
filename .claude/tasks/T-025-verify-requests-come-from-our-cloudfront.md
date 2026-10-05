---
id: T-025
title: "The edge is not an authenticator: prove requests come from OUR CloudFront distribution"
repo: cv-infra + cv-domain-service
status: done
owner: tech-product-owner
branch: feat/origin-shared-secret-header
pr: none                  # closed 2026-10-05 at H1 as DOCUMENTED ACCEPTED RISK (the human's decision) — a decision task with no code; same sentinel as T-010/T-012/T-030
depends_on: [T-022, T-043]   # T-043 added 2026-10-01: scheduled after the BFF's service token, per T-014's H2
risk: normal
security_review: true
---

## ✅ CLOSED 2026-10-05 at H1 — documented accepted risk (the human's decision)

**The exposure, measured live on 2026-10-05** (on the app host; the same requests a foreign CloudFront distribution can make, since the origin-facing prefix list is shared by every CloudFront customer):

| Path, reached through a foreign distribution | Answer | Disclosure |
|---|---|---|
| domain `/v3/api-docs`, `/actuator/prometheus` (**the leak this task was filed for**) | **401** | none; closed since T-106 deployed (2026-10-01, T-014) |
| domain `/actuator/health` | 200 | `{"status":"UP"}`, by design |
| every other domain path | 401 / 403 | none without a token; writes need a user token (T-116) |
| BFF `/bff/api/v1/people/:id`, `/cv` | 200 | the public CV, public by design (no ids/emails/versions) |
| BFF `/health` | 200 | `{"status":"ok"}` |
| BFF `/metrics` | 200 | Prometheus counters: per-route request counts and latencies (labels bucketed, T-208), Node event-loop and memory. **No data, no secrets, no identifiers.** |

**Why accepting is defensible:** the only residual is mild operational information disclosure from the BFF's `/metrics`. No authenticated path is bypassable (the JWT checks live in the services, not at the edge), and **our edge carries no controls a bypass could skip** (no WAF, no rate limiting, no edge auth). The shared-secret header would cost three repos with a strict send-then-enforce ordering plus a rotation procedure, to protect counters.

**Re-open this task if any of these becomes true:**
1. Anything non-public becomes reachable **anonymously** on origin port 8080 or 3000 (a new unauthenticated route, an actuator endpoint opened, a debug flag).
2. A **WAF, rate limit or other edge control** is added to our distribution: the bypass would then defeat it.
3. The BFF's `/metrics` starts carrying anything beyond counters (e.g. labels with user input or identifiers).

The design notes below are kept as the record of the shared-secret option, if it's ever needed.

> **Board review 2026-10-04 — the premise moved; decide at H1 whether to close.** The leak this task was filed for (`/v3/api-docs` answering through any CloudFront distribution) is **closed live**: T-106's fix has been deployed since 2026-10-01 (T-014 put current domain-service master on the host). What's still reachable through a foreign distribution: the domain service's `/actuator/health` (anonymous by design), the BFF's two public routes (public by design), and the **BFF's `/metrics`** (Prometheus counters, route labels bucketed since T-208, no data). This task's own recommendation (below) was already *documented accepted risk*. Options at H1: close as accepted risk; or close plus a one-line BFF change that stops serving `/metrics` outside dev; or implement the shared-secret header as scoped.

> **T-014's H2, 2026-10-01: kept as its own task, after [T-043](T-043-bff-service-token-to-domain.md).** The BFF is now live on origin port **3000**, behind the same shared CloudFront prefix list as 8080, so this task now covers both ports. Concretely, the BFF's `/metrics` (Prometheus counters, route labels bucketed since T-208) is readable through any CloudFront distribution; its non-public routes still need a JWT.

## Why this exists

**Filed 2026-08-20 from [T-022](T-022-domain-service-origin-bypasses-cloudfront.md)'s forced `/security-review`** — the one MEDIUM finding it returned, dispositioned to its own task rather than folded into a PR whose acceptance criteria it exceeds (board rule 3, and T-022's own instruction not to reach across repos).

T-022 scoped port 8080 to `com.amazonaws.global.cloudfront.origin-facing`, which closed the direct-to-EIP path — verified by request. **But that prefix list is shared by every CloudFront customer.** It is the set of addresses CloudFront uses for origin fetches *globally*, not the addresses of distribution `E2AV0INGJW1UO2`. So the security group now authenticates *"some CloudFront distribution"*, not *"ours"*.

`frontend.tf`'s `domain-service-api` origin sends **no shared-secret header** (confirmed 2026-08-20: `custom_origin_config` carries only ports and protocol policy), and the origin validates nothing, so there is nothing downstream to catch the difference.

### The attack path, concretely

1. Attacker creates their own CloudFront distribution, origin `15.236.195.130`, `http_port = 8080`, `origin_protocol_policy = "http-only"`, caching off, all paths forwarded.
2. Requests through it leave from an origin-facing IP → **our security group allows them**.
3. `GET /v3/api-docs` returns **200 with the full springdoc document**, because the `403` on that path is a behaviour of *our* distribution, not a property of the origin.

The JWT-gated routes still return `401`, so this is information disclosure and edge-control bypass, **not** authenticated access. What it defeats is every control that lives at our edge: the `/v3/api-docs` 403, and any future WAF rule, header policy or behaviour-level restriction.

## Recommended: take this decision AT T-014's H2, and expect "documented accepted risk" (2026-08-24, on the human's instruction)

**Decide it cheaply, and decide it in the right room.** Two things make this task's *decision* worth more than its implementation right now:

**1. The leak it was filed for is already closed.** [T-106](T-106-restrict-openapi-and-actuator-exposure.md) merged — `/v3/api-docs` and `/swagger-ui/**` no longer answer anonymously. The concrete attack path in §"The attack path, concretely" step 3 (*"returns 200 with the full springdoc document"*) **no longer reproduces**. What remains is the bypass *class*: a foreign CloudFront distribution can still reach the origin, and would still meet whatever edge controls exist **later**. There is currently nothing behind that door worth walking through — JWT-gated routes still 401.

**2. The right moment is [T-014](T-014-deploy-bff-to-aws.md)'s H2, not a separate gate.** Three of this task's own DoR items point at T-014 rather than at itself:
- DoR **1** — the filter must not break the BFF's container-to-container path, and *"getting this wrong breaks the BFF the day T-014 lands"*.
- DoR **3** — *"Does this belong on port 3000 too? **Yes**"*. So deciding **after** T-014 means retrofitting both ports; deciding **at** T-014 means one decision covering both.
- T-014's own ruling-1 note already sends the reader here before deciding how much to carry.

At T-014's H2 the human is weighing this exact surface — a second port behind the same "some CloudFront distribution" proof — with the live system in front of them. Convening a separate gate to re-derive the same trade-off is the expensive path.

**Why "accepted risk" is the likely and defensible answer:**
- Two cross-repo PRs with a **mandatory ordering** (send the header, *then* enforce it — enforcing first takes the live API down), plus a rotation procedure, to protect against an attacker who currently gains **nothing** by bypassing.
- DoR **4** already concedes the header travels **edge-to-origin over plain HTTP** (`origin_protocol_policy = "http-only"`), so anyone positioned to observe it can replay it. The control is real but not strong, which lowers what deferring it costs. *(If TLS to the origin is ever taken up, see [T-033](T-033-ci-host-tls.md) — different host, same underlying "plaintext in transit" theme.)*
- The single-user demo has one credential set, and [T-012](T-012-aws-endgame-decision.md) time-boxes the whole thing.

**If accepted, the decision must name its own expiry** — the same requirement put on [T-155](T-155-flyway-version-supports-mysql-84.md): revisit **the moment an edge control worth bypassing exists** (a WAF rule, a behaviour-level restriction, a header policy, or a second user). Without that trigger this becomes another premise nobody re-checks, which is the failure mode this board exists to catch. Record it on this task and cross-reference it from T-014's H2 note.

**This is a recommendation, not a decision taken here** — it is a security posture call and belongs to the human. If they choose to implement, everything below stands unchanged.

## Scope

> **Cross-repo (board note 2026-09-25):** this file spans two repos. If H1 decides to implement, stage 0 splits it into two dependency-ordered single-repo tasks (cv-infra sends the header, then cv-domain-service enforces it), per adapter §2. If the decision is "accepted risk", it closes as one task.

**cv-infra** — add a `custom_header` to the `domain-service-api` origin in `frontend.tf`, value from SSM (`/cv-project/<env>/edge/origin-shared-secret`) per the repo's existing secrets flow. Never in a committed `.tf` or tfvars.

**cv-domain-service** — reject requests to non-public paths that lack the header. A servlet filter or the existing `SecurityConfig` chain, decided at refinement.

Two PRs, one per repo, and **the order matters**: ship the origin sending the header first, then enforce it. Enforcing first takes the live API down.

## Definition of Ready — settle before code

1. **What is "non-public" here?** The whole API is behind CloudFront today, so enforcing on everything is possible — but T-014 puts the BFF on this same box and it must keep reaching the domain service **container-to-container on the `cv` docker network**, which never traverses CloudFront. Decide whether the filter exempts in-network callers by source, by path, or by a second credential. **Getting this wrong breaks the BFF the day T-014 lands, and the failure is a 403 that looks like a bug in the BFF.**
2. **Rotation.** A shared secret that cannot be rotated is a secret that never will be. Say how a rotation happens without an outage — CloudFront supports multiple origins/headers, and the filter can accept two values during a window.
3. **Does this belong on port 3000 too?** Yes, and it is the same decision — see the T-014 note below. Decide whether this task covers both ports or only 8080, and say which.
4. **Is the header enough on its own?** It travels over **plain HTTP** edge-to-origin (`origin_protocol_policy = "http-only"`), so anyone who can observe that traffic can replay it. That is an accepted property of the current design, not something this task fixes — record it rather than discovering it in review.

## Acceptance criteria

- [ ] ~~A request to `http://15.236.195.130:8080/v3/api-docs` **through a CloudFront distribution other than ours** is rejected — proven by actually standing one up, or by replaying the exact request without the header from an allowed source. Not by reading the config.~~ *(N/A — closed as accepted risk, 2026-10-05)*
- [ ] ~~The live admin UI still loads its people list with a real Cognito JWT.~~ *(N/A — closed as accepted risk, 2026-10-05)*
- [ ] ~~`/api/*` through our distribution is unaffected.~~ *(N/A — closed as accepted risk, 2026-10-05)*
- [ ] ~~The secret is in SSM, never in a committed file, and the rotation procedure is written down.~~ *(N/A — closed as accepted risk, 2026-10-05)*
- [ ] ~~`terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass, with an assertion that the origin carries the header.~~ *(N/A — closed as accepted risk, 2026-10-05)*
- [ ] ~~The Java side has tests for both branches: header present → served, header absent → rejected.~~ *(N/A — closed as accepted risk, 2026-10-05)*

## Definition of done

Both PRs merged, in the order above, and the bypass demonstrated closed by request.

## dev-loop notes

- **Developers:** `infrastructure-engineer` (cv-infra half), `backend-developer` (cv-domain-service half). **Reviewers:** `/code-review` + `/security-review` (forced — this *is* an auth boundary).
- ~~**Cheaper alternative worth pricing at H1:** [T-106](T-106-restrict-openapi-and-actuator-exposure.md) closes the *specific* disclosure for one property… Decide that at H1 rather than building both by default.~~ **OVERTAKEN BY EVENTS 2026-08-20 — [T-106](T-106-restrict-openapi-and-actuator-exposure.md) is `done` and merged ([cv-domain-service#4](https://github.com/erfeamor/cv-domain-service/pull/4)).** The cheaper half is no longer an option to price; it has shipped, and the OpenAPI/actuator disclosure that motivated this task is already closed. **H1 therefore decides a different and narrower question:** with nothing currently leaking through the bypass, is the *residual bypass class* — any CloudFront customer's distribution reaching our origin and meeting whatever edge controls exist later — worth a shared secret and cross-repo sequencing **now**, or is it a documented accepted risk revisited when an edge control worth bypassing actually exists? Note the argument does not vanish with T-106: the prefix list still proves "a CloudFront distribution", not "ours", and [T-014](T-014-deploy-bff-to-aws.md) is about to put a second port behind the same weak proof. Price it against that, not against the leak.
- **This is not a regression from T-022.** T-022 strictly narrowed an exposure that was `0.0.0.0/0`; this is the residual gap in the approach, which T-022's own body anticipated when it called springdoc hardening *"defence in depth, not the fix"*.
