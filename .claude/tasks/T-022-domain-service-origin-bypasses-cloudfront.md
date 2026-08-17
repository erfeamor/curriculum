---
id: T-022
title: "The domain service is directly reachable on :8080, bypassing CloudFront — and leaks its OpenAPI spec"
repo: cv-infra
status: todo
owner:
branch: fix/scope-domain-service-ingress
pr:
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
