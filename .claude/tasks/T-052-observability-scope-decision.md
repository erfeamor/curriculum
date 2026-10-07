---
id: T-052
title: "Decide the demo's observability scope: metrics are local-only today, and the structured-logging pipeline is still 'pending' on the roadmap"
repo: cv-project (meta)
status: done
owner: tech-product-owner
branch: docs/observability-scope
pr: none   # a decision; no code
depends_on: []
risk: low
security_review: false
---

## Decided by the human, 2026-10-07

**Production application logs go to CloudWatch, and metrics stay local-only by design.** That is options 1 and 2 combined:

- **Metrics:** Prometheus and Grafana stay in the local dev stack. Nothing scrapes the deployed services, and the edge keeps `/metrics` closed (403). Running metrics in AWS (option 3) is rejected: it needs memory the `t4g.micro` doesn't have spare, or a paid managed service, for a demo paid from credits.
- **Logs:** the app containers ship to the two CloudWatch groups that already exist. Filed as **[T-054](T-054-app-container-logs-to-cloudwatch.md)** (cv-infra). Measured 2026-10-07 on the app host: domain-service ~7 KB since its 09:15Z start, bff-node ~1.7 KB in ~19 h, mysql ~2.5 KB in ~2 days. At kilobytes a day the cost is ~$0. Stage 0 confirmed the two service groups exist with 14-day retention and **0 bytes stored**; the CI doorbell and reaper Lambdas are the only CloudWatch writers today.
- **Structured JSON logging in the apps** (the README's "MongoDB Atlas or CloudWatch" design) is **not** in scope. Atlas stays a design note. T-054 ships whatever the containers print today.
- **Docs:** [T-502](T-502-final-docs-architecture-diagram.md) describes this decision and now waits for T-054, so the docs describe logs as live.

## Why

Filed by the 2026-10-06 board review. The README roadmap ticks "Configure observability (metrics; structured-logging pipeline pending)", and `docs/architecture.md` describes Prometheus/Grafana metrics and a separate logs pipeline (MongoDB Atlas or CloudWatch). In reality Prometheus and Grafana run **only in the local dev stack**; nothing scrapes the deployed services, and no logs pipeline exists (the app containers have no log driver; the `bff_node`/domain log groups are unused).

## Options (decide at H1; minutes)

1. **Record "metrics are local-only by design"** and descope the logs pipeline. Adjust the README and architecture wording (done in [T-502](T-502-final-docs-architecture-diagram.md)). Cheapest and honest.
2. **CloudWatch logs only:** the `awslogs` driver on the app containers into the existing log groups (+ a `logs:*` grant scoped to them): a small cv-infra task, ~cents/month.
3. **Cloud metrics** (Grafana/Prometheus in AWS): real monthly cost; likely not worth it for a demo.

## Acceptance criteria

- [x] A recorded decision; follow-up tasks filed per repo if option 2 or 3.
