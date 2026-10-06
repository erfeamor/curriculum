---
id: T-052
title: "Decide the demo's observability scope: metrics are local-only today, and the structured-logging pipeline is still 'pending' on the roadmap"
repo: cv-project (meta)
status: todo
owner:
branch: docs/observability-scope
pr:
depends_on: []
risk: low
security_review: false
---

## Why

Filed by the 2026-10-06 board review. The README roadmap ticks "Configure observability (metrics; structured-logging pipeline pending)", and `docs/architecture.md` describes Prometheus/Grafana metrics and a separate logs pipeline (MongoDB Atlas or CloudWatch). In reality Prometheus and Grafana run **only in the local dev stack**; nothing scrapes the deployed services, and no logs pipeline exists (the app containers have no log driver; the `bff_node`/domain log groups are unused).

## Options (decide at H1; minutes)

1. **Record "metrics are local-only by design"** and descope the logs pipeline. Adjust the README and architecture wording (done in [T-502](T-502-final-docs-architecture-diagram.md)). Cheapest and honest.
2. **CloudWatch logs only:** the `awslogs` driver on the app containers into the existing log groups (+ a `logs:*` grant scoped to them): a small cv-infra task, ~cents/month.
3. **Cloud metrics** (Grafana/Prometheus in AWS): real monthly cost; likely not worth it for a demo.

## Acceptance criteria

- [ ] A recorded decision; follow-up tasks filed per repo if option 2 or 3.
