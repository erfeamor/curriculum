---
id: T-053
title: "cv-infra: refresh CLAUDE.md's cost model table with T-051's post-trim measurement"
repo: cv-infra
status: done
owner: tech-product-owner
branch: docs/cost-table-refresh
pr: https://github.com/erfeamor/cv-infra/pull/44
depends_on: [T-051]
risk: trivial
security_review: false
---

## Done — 2026-10-08

`cv-infra/CLAUDE.md`'s cost model now matches T-051 ([cv-infra#44](https://github.com/erfeamor/cv-infra/pull/44)): $116.15 of credits, **~$0.51/day** (fixed ~$0.47 plus CI ~$0.04), runway until about late May 2027, and the CI host left running at ~$1.2/day. Done outside the dev loop at the human's request (usage gap): a driver-only docs edit, with the human's merge as the gate.

## Why

The cv-infra half of [T-051](T-051-cost-remeasure-after-trims.md) (one task per repo). `cv-infra/CLAUDE.md`'s "Cost model" table and its review guidance quote the 2026-09-28 run rate, and the "leaving the CI host up costs ~$17/month" lever, both measured on the old instance types.

## Acceptance criteria

- [x] The table, the run-rate sentence and the review-guidance cost figures match T-051's measurement, dated.
