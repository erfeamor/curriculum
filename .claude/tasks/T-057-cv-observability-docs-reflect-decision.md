---
id: T-057
title: "cv-observability docs predate T-052/T-054: logging 'not wired up yet', pipeline 'Jenkins or GitHub Actions'"
repo: cv-observability
status: todo
owner:
branch: docs/reflect-observability-decision
pr:
depends_on: []
risk: trivial
security_review: false
---

## Why

Found by [T-502](T-502-final-docs-architecture-diagram.md)'s per-repo README audit (2026-10-08):

- `docs/logging.md` says structured JSON logs ship to MongoDB Atlas or CloudWatch, and that "Neither is wired up yet". Since [T-054](T-054-app-container-logs-to-cloudwatch.md), the domain service's and the BFF's raw container output ships to CloudWatch Logs. [T-052](T-052-observability-scope-decision.md) put structured JSON logging and Atlas out of scope.
- `README.md` line 20 repeats the "Atlas or CloudWatch" claim. Line 5 says "Pipeline: Jenkins or GitHub Actions"; it is GitHub Actions only (`.github/workflows/ci.yml` validates the compose file and the Prometheus config).
- The README should also say the stack is **local-only by design**: nothing scrapes the deployed services (T-052).

## Acceptance criteria

- [ ] `docs/logging.md` records the decision: what ships today (raw container output to `/cv-project/cv-domain-service` and `/cv-project/cv-bff-node`, 14 days), what's out of scope, and how to read it (`aws logs tail`). The old Logback/pino plan stays as a "should this ever be built" note.
- [ ] The README states the pipeline correctly and that the metrics stack is local-only.
