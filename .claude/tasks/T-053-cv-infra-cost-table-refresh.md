---
id: T-053
title: "cv-infra: refresh CLAUDE.md's cost model table with T-051's post-trim measurement"
repo: cv-infra
status: todo
owner:
branch: docs/cost-table-refresh
pr:
depends_on: [T-051]
risk: trivial
security_review: false
---

## Why

The cv-infra half of [T-051](T-051-cost-remeasure-after-trims.md) (one task per repo). `cv-infra/CLAUDE.md`'s "Cost model" table and its review guidance quote the 2026-09-28 run rate, and the "leaving the CI host up costs ~$17/month" lever, both measured on the old instance types.

## Acceptance criteria

- [ ] The table, the run-rate sentence and the review-guidance cost figures match T-051's measurement, dated.
