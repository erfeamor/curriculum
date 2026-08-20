---
id: T-106
title: "Stop serving the OpenAPI spec and Prometheus metrics to anonymous callers"
repo: cv-domain-service
status: todo
owner:
branch: fix/restrict-openapi-actuator
pr:
depends_on: []
risk: normal
security_review: true
---

## Why this exists

**Filed 2026-08-20** out of [T-022](T-022-domain-service-origin-bypasses-cloudfront.md)'s security review. T-022 predicted this task in its own body — *"hardening springdoc itself is defence in depth, not the fix... if the reviewer wants it, split it into its own task"* — and the reviewer wanted it.

`SecurityConfig.java:38-39` explicitly permits three path groups to anonymous callers:

```java
.requestMatchers("/actuator/health", "/actuator/prometheus",
        "/swagger-ui/**", "/v3/api-docs/**").permitAll()
```

That is why `/v3/api-docs` answered **200 with the full OpenAPI document** on the public IP while `/api/v1/**` answered 401. T-022 removed the *network* path to it; this task removes the *reason it was reachable at all*.

**Why it still matters after T-022.** Two independent reasons:

1. **The prefix list is shared by all CloudFront customers** ([T-025](T-025-verify-requests-come-from-our-cloudfront.md)), so an attacker's own distribution still reaches the origin and still gets the spec.
2. **T-014 is coming.** It publishes port 3000 for the BFF on this same instance. Every new port is another chance for this `permitAll` set to become internet-reachable again, and nothing in the Java app would flag it.

`/actuator/prometheus` is in the same list and was equally reachable — a metrics endpoint is a smaller leak than a full API map, but it is the same mistake and it is one line away.

## Scope

`cv-domain-service` only. **Do not** change network scoping here — that is T-022 (done) and T-025.

- Decide per path group: **disable in the deployed profile** (`springdoc.api-docs.enabled: false`, `springdoc.swagger-ui.enabled: false`) versus **keep enabled but require auth** (drop them from the `permitAll` matcher).
- `/actuator/health` must stay anonymous — it is a liveness probe.
- `/actuator/prometheus`: keep anonymous only if something actually scrapes it. **Nothing does today** — `observability.tf` contains only CloudWatch log groups and no Prometheus is deployed in AWS (verified 2026-08-20). So the honest default is to protect it and let whoever deploys the scraper decide how it authenticates.

## Definition of Ready — settle before code

1. **Disable, or authenticate?** Swagger UI is genuinely useful for a *demo* — the meta CLAUDE.md advertises `/swagger-ui.html` as a dev affordance. Disabling it in the deployed profile keeps local dev unchanged and costs the live demo a page. Requiring a JWT keeps the page but makes it useless to a casual viewer. **This is a demo-value decision, not a security one** — take it at H1 rather than assuming.
2. **Which profile is "deployed"?** Confirm the container actually runs with a profile that a `application-<profile>.yml` can target; if it runs with none, this becomes a property in the base file plus a dev override, which is the opposite default and easy to get backwards.

## Acceptance criteria

- [ ] `/v3/api-docs` and `/swagger-ui/**` are either disabled or 401 for an anonymous caller **in the deployed configuration** — proven against the running container, not from the yml.
- [ ] `/actuator/health` still answers 200 anonymously (the probe must not break).
- [ ] `/actuator/prometheus` decision implemented and its rationale recorded.
- [ ] Local dev is explicitly checked: whatever the demo relies on still works after the change, or the docs that advertise it are corrected in the same PR.
- [ ] Tests cover the anonymous case for each path group — this is exactly the kind of config that regresses silently.

## Definition of done

PR merged, verified against the deployed container by request, and the meta docs that advertise Swagger corrected if the answer was "disable".

## dev-loop notes

- **Developer:** `backend-developer`. **Reviewers:** `/code-review` + `/security-review` (auth matcher change — adapter §5).
- **Cheap and independent.** No dependency on T-025; if T-025 is declined at its H1, this task is the whole answer to the finding. If T-025 proceeds, they are complementary — this shrinks what leaks, T-025 stops the bypass.
- **Sequencing against [T-014](T-014-deploy-bff-to-aws.md):** worth landing *before* it. T-014 adds a second published port to this box, and doing that while the spec is still anonymous widens the same hole.
