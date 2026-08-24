---
id: T-022
title: "The domain service is directly reachable on :8080, bypassing CloudFront — and leaks its OpenAPI spec"
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: fix/scope-domain-service-ingress
pr: https://github.com/erfeamor/cv-infra/pull/20
checkpoint:
  stage: done               # merged as da17414 (cv-infra#20), 2026-08-20
  applied: "2026-08-20. Plan was 0 to add, 1 to change, 0 to destroy — in-place SG modification, no instance replacement, so DoR §4 is answered and T-021's db_password precondition does not apply. A second apply reported No changes (idempotent)."
  dor_answers: |
    §1 Does anything legitimately call 8080 directly? NO — established by evidence, not assumption:
       - the DEPLOYED admin bundle (s3://cv-project-frontend-dev/admin/assets/index-C5mlE1U5.js)
         calls a RELATIVE "/api/v1/people", so it goes through CloudFront. It contains no raw
         IP and no :8080 endpoint (the two "8080" hits are inside the React version string
         18.3.1-next-f1338f8080). This was the real silent-outage risk and it is clear.
       - cv-observability is NOT deployed in AWS: observability.tf holds only CloudWatch log
         groups, and no prometheus/scrape/9090 reference exists in any .tf or template.
       - the BFF (T-014) will reach the domain service container-to-container on the cv docker
         network, never through this security group.
       - local dev is a different network entirely.
    §2 Prefix-list quota: the list held 46 entries on 2026-08-20 against a 60-rule inbound
       quota. ONE reference fits with 14 to spare. TWO DO NOT (46+46=92) — see the T-014 note.
    §3 Description left untouched (ForceNew, no create_before_destroy); a comment now says so
       and a test assertion pins the string.
    §4 In-place, confirmed in the plan. No instance replacement.
  verification: |
    By request from outside AWS, before and after.
    BEFORE:  :8080/v3/api-docs 200 (full springdoc doc) · /actuator/health 200 · /api/v1/people/1 401
    AFTER:   all three TIME OUT on :8080
    EDGE (unchanged, before and after): cf /api/v1/people/1 401 · cf /v3/api-docs 403 · cf /admin/ 200
    The 401 through CloudFront is the proof the origin is still reachable from the edge — an
    unreachable origin returns 502/504, not 401.
    NOT VERIFIED: the admin UI loading its people list with a real Cognito JWT. That needs an
    interactive login and is the one acceptance criterion still outstanding. The anonymous 401
    is strong evidence the path is intact but it is not the same check.
    CLOSURE PATH IDENTIFIED 2026-08-24 (no work needed here): T-014's stage-4 test plan
    section 5 already specifies this exact check -- "/api/v1/people/1 still 401s ... and the
    live admin UI still loads its people list with a real Cognito JWT" -- against the live
    system, with the interactive login this task could not perform. T-014 is a scheduled
    apply with QA budgeted, so the criterion gets satisfied by work already planned rather
    than by convening a session for one login. ACTION: when T-014's stage 4 runs, tick this
    criterion here and cite T-014's QA report. If T-014 is abandoned or descoped, this
    reverts to needing its own interactive check -- do not let the cross-reference become the
    reason it is never verified.
  gates: "terraform fmt -check -recursive clean · terraform validate Success · terraform test 4 passed, 0 failed. The new assertions were proven non-vacuous by temporarily re-adding cidr_blocks 0.0.0.0/0 and confirming the guard fails."
  security_review: |
    RUN 2026-08-20 (forced by adapter §5 — security_group ingress). ONE MEDIUM finding, no HIGH.
    Finding: com.amazonaws.global.cloudfront.origin-facing is shared by EVERY CloudFront
    customer, so the SG now authenticates "some distribution", not ours. An attacker can point
    their own distribution at 15.236.195.130:8080 and still read /v3/api-docs, because the 403
    on that path is a behaviour of OUR distribution, not of the origin. frontend.tf sends no
    shared-secret header and the origin validates nothing.
    Disposition: NOT fixed here. Both halves live in other repos or exceed these acceptance
    criteria (board rule 3), and this task's own body already said springdoc hardening belongs
    in its own task. Filed as T-025 (shared-secret origin header, cv-infra + cv-domain-service)
    and T-106 (stop serving the spec and metrics anonymously, cv-domain-service).
    This is a residual gap in the approach, NOT a regression: the change strictly narrows an
    exposure that was 0.0.0.0/0, and the direct-to-EIP path is genuinely closed.
depends_on: []
risk: normal
security_review: true
---

## Why this exists

Surfaced during **T-014's stage-0 refinement** (2026-08-14), while ruling on how the BFF's new port 3000 should be exposed. The neighbouring rule turned out to be the problem: `network.tf:40-45` opens **8080 to `0.0.0.0/0`**.

Filed separately on the human's instruction rather than folded into T-014 — a deployment task should not quietly re-scope a pre-existing exposure, and this needs its own review and its own verification.

## What is actually exposed — measured, not assumed

Probed directly against `http://15.236.195.130:8080` on 2026-08-14:

| Path | Direct on :8080 | Via CloudFront |
|---|---|---|
| `/api/v1/people/1` | `401` | `401` |
| `/actuator/health` | `200` | — |
| **`/v3/api-docs`** | **`200` — unauthenticated** | `403` |
| `/swagger-ui.html` | `401` | — |
| `/actuator`, `/actuator/env`, `/actuator/metrics` | `401` | — |

**Two findings, and the second is the one that makes this more than theoretical.**

### 1. The edge is not the only way in

CloudFront is designed as the entry point — `frontend.tf`'s own comment explains that `/api/*` is routed through the distribution so the browser stays on HTTPS and same-origin. But the origin answers the public internet directly on plain HTTP, so **anything the edge does is optional from an attacker's point of view**: any future WAF rule, header policy, rate limit, or behavior-level control is bypassed by talking to `15.236.195.130:8080`. The protection is real for well-behaved browsers and absent for everyone else.

### 2. The OpenAPI spec is served unauthenticated

`/v3/api-docs` returns **200 with the full springdoc document** — every path, method, operation id, and schema, plus `"servers":[{"url":"http://15.236.195.130:8080"}]`. It is small today (2 paths) precisely because M2 has not landed yet; **it grows automatically with every resource T-101…T-104 add**, and nothing will flag that.

Note it returns **403 through CloudFront** — the disclosure exists *only* via the direct-IP path. That is the whole point: this is not a routing gap at the edge, it is the origin being reachable at all.

## The fix, and why it is the same one T-014 already ratified

**Scope the 8080 ingress to CloudFront's own origin-facing ranges**, via the managed prefix list:

```hcl
data "aws_ec2_managed_prefix_list" "cloudfront_origin_facing" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}
```

referenced as `prefix_list_ids` on the ingress rule instead of `cidr_blocks = ["0.0.0.0/0"]`. This is **exactly** T-014 ruling 1's approach for port 3000, which is why the two should look identical when both have landed — and why doing this one *first* would let T-014 simply follow an established pattern rather than introduce one.

Once 8080 is prefix-list scoped, `/v3/api-docs` becomes unreachable from the internet without any change to the Java app, because the edge already 403s it. **Hardening springdoc itself is therefore defence in depth, not the fix** — and it lives in `cv-domain-service`, a different repo. If the reviewer wants it, split it into its own task at refinement rather than reaching across repos here.

## Definition of Ready — settle before code

1. **Does anything legitimately call 8080 directly?** Check before restricting: the admin UI goes through CloudFront, and `cv-observability` scrapes in-network — but confirm rather than assume, because the failure mode is a silent outage of whatever did depend on it. Note `docker-compose.dev.yml` and local dev are unaffected (different network entirely).
2. **Prefix-list rule size.** A managed prefix list consumes entries against the security group's rule quota (each prefix list counts as its `max_entries`, not as one rule). Confirm the group stays within quota — this is the usual way this change fails on the first apply.
3. **`aws_security_group.description` is ForceNew** and this group has no `create_before_destroy` (`network.tf:66-67` documents the trap). Touching the description replaces the group; leave it alone.
4. **Does this apply replace the instance?** It should not — a security-group rule change is in-place. Confirm in the plan, because if it *does*, the T-021 `db_password` precondition applies.

## Acceptance criteria

- [ ] `curl http://15.236.195.130:8080/v3/api-docs` from outside AWS **times out or is refused** — verified by real request, not by reading the plan.
- [ ] `curl http://15.236.195.130:8080/api/v1/people/1` likewise unreachable directly.
- [ ] **The same request through CloudFront still works** — `/api/*` still reaches Java, and the live admin UI still loads its people list with a real Cognito JWT. This is the check that catches an over-tight rule.
- [ ] `cv-observability`'s scraping still works, or its breakage is understood and handled.
- [ ] No port 22, no new EIP, no NAT gateway.
- [ ] `terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass, with an assertion pinning the ingress to the prefix list rather than a CIDR.

## Definition of done

PR open against `master` from `fix/scope-domain-service-ingress`, gates green, applied, and verified by request from outside AWS, merged.

## dev-loop notes

- **Developer:** `infrastructure-engineer`. **Reviewers:** `/code-review` + `infrastructure-engineer` + **`/security-review`** (forced by adapter §5 — this is a `security_group` ingress change).
- **`risk: normal`, not `high`.** It is an in-place SG change, not an instance replacement, and it is easily reverted. The blast radius is "the API becomes unreachable", which the acceptance criteria catch immediately.
- **Sequencing:** doing this **before** [T-014](T-014-deploy-bff-to-aws.md) is cheaper — T-014's ruling 1 then follows an existing pattern instead of inventing one, and the reviewer sees one consistent approach across both ports. It is not a hard dependency in either direction.
- **Do not fold this into T-014.** That was the explicit decision at T-014's refinement: a deployment task should not silently re-scope a pre-existing exposure it happened to notice.
- The exposure is **pre-existing and predates the BFF work** — it is not a regression introduced by any recent task. It stayed invisible for the same reason the BFF gap did: the admin works, so nobody looked at what else answered.

## Follow-ups filed from this task's security review (2026-08-20)

The forced `/security-review` returned one MEDIUM finding: **the CloudFront origin-facing prefix list is shared by all CloudFront customers**, so scoping to it proves a request came from CloudFront, not from *our* distribution. An attacker's own distribution still reaches this origin and still reads `/v3/api-docs`.

Neither remedy belongs in this PR — one is cross-repo, the other is in `cv-domain-service`, and this task's own scope section said so before the review existed:

- **[T-025](T-025-verify-requests-come-from-our-cloudfront.md)** — shared-secret `custom_header` on the origin, validated by the Java app. Closes the bypass *class*: every edge control, not just this one path.
- **[T-106](T-106-restrict-openapi-and-actuator-exposure.md)** — stop `permitAll`-ing `/v3/api-docs`, `/swagger-ui/**` and `/actuator/prometheus`. Closes *this* disclosure cheaply, and is the whole answer if T-025 is declined at its H1.

**What this task did and did not achieve, stated plainly:** the direct-to-EIP path is closed and proven closed. The claim *"`/v3/api-docs` becomes unreachable from the internet"* in the scope section above is **too strong** — it is unreachable *directly*. Reaching it now requires standing up a CloudFront distribution, which is a real cost increase for an attacker and no kind of guarantee.
